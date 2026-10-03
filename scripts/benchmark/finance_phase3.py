#!/usr/bin/env python3
"""Measure actual PostgreSQL finance operations in an isolated disposable schema."""
from pathlib import Path
from dataclasses import replace
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
from time import perf_counter
from uuid import UUID,uuid4,uuid5
import json,platform,statistics,sys
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'apps/api'),str(ROOT/'scripts/seed')]
from sqlalchemy import create_engine,insert,select,text
from sqlalchemy.engine import make_url
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.core.identity import authenticate
from app.core.serialization import utcnow
from app.db.session import Database
from app.db.models import ReferenceRecord,TransactionVersion,ApprovalRecord,Job,Transaction
from app.services.references import seed_references,number_key
from app.services import finance,duplicates
from app.services.worker import claim
from app.rules.finance_phase3 import evaluate
from app.schemas.canonical import fixture_canonical
from phase3 import enable
from finance_catalog import activate_catalog,transactions,uid


def stats(values):return {'samples':len(values),'min_ms':round(min(values),3),'median_ms':round(statistics.median(values),3),'p95_ms':round(sorted(values)[int((len(values)-1)*.95)],3),'max_ms':round(max(values),3)}

def main():
    settings=Settings.load();identity=authenticate(next(iter(settings.identities)),settings);identity=replace(identity,roles=identity.roles|{'FINANCE_SUBMITTER','REFERENCE_ADMIN'})
    base=make_url(settings.database_url).set(database='ap_phase1_test');schema='bench_phase3_'+uuid4().hex;control=create_engine(base);db=None
    with control.begin() as c:c.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        url=base.update_query_dict({'options':f'-csearch_path={schema}'});cfg=Config(str(ROOT/'apps/api/alembic.ini'));cfg.attributes['database_url']=url.render_as_string(hide_password=False);command.upgrade(cfg,'head');db=Database(cfg.attributes['database_url'])
        with db.session(identity) as s:seed_references(s,identity)
        enable(db,identity);activate_catalog(db,identity)
        vendor='50000000-0000-4000-8000-000000000001'
        # Fetch the source supplier rather than assuming its UUID prefix.
        with db.session(identity) as s:vendor=str(next(r.id for r in s.scalars(select(ReferenceRecord).where(ReferenceRecord.kind=='vendors')) if r.payload['legal_name'].startswith('DEMO')))
        histories=[]
        for i in range(10000):
            rid=UUID(uid(f'benchmark-history-{i}'));party=UUID(vendor if i%20==0 else uid(f'vendor-{i%19+1}'));day=date(2026,1,1)+timedelta(days=i%270);amount=Decimal(50000+i);number=f'SYNTHETIC-HISTORY-{i:05}'
            payload={'id':str(rid),'version':1,'synthetic':True,'branch':'VENDOR_INVOICE','vendor_id':str(party),'invoice_number':number,'invoice_date':str(day),'total_amount':str(amount),'currency':'INR','lifecycle':'PAID','capacity_state':'CONSUMED'}
            histories.append(identity.scope()|{'id':rid,'version':1,'kind':'historical_transactions','label':number,'payload':payload,'amount':amount,'currency':'INR','business_date':day,'party_id':party,'number_key':number_key(number)})
        with db.session(identity) as s:
            s.execute(insert(ReferenceRecord),histories)
            for r in transactions():finance.create_transaction(s,identity,r['transaction'],'Fictional scale input, no eligibility asserted','phase3-benchmark',UUID(r['id']))
        with db.engine.begin() as c:c.execute(text('ANALYZE reference_records'));c.execute(text('ANALYZE transaction_versions'))
        p=fixture_canonical(json.loads((ROOT/'data/golden_cases/vendor/clean.json').read_text())['transaction']);target=uuid4()
        with db.session(identity) as s:
            finance.create_transaction(s,identity,p,'Fictional complete benchmark case','phase3-benchmark',target)
            for order,actor,role in [(1,'51000000-0000-4000-8000-000000000003','MANAGER'),(2,'51000000-0000-4000-8000-000000000004','DEPARTMENT_HEAD')]:s.add(ApprovalRecord(**identity.scope(),transaction_id=target,transaction_version=1,policy_id=UUID(p['approval_policy_id']),policy_version=2,actor_id=UUID(actor),role=role,sequence=order,state='APPROVED',approved_at=utcnow()))
        lookup=[];pure=[];finalize=[];end_to_end=[];decisions=[]
        profile={'near_amount_absolute':'10','duplicate_window_days':7,'fuzzy_number_cutoff':85,'phash_distance':6}
        for i in range(25):
            with db.session(identity) as s:
                v=s.scalar(select(TransactionVersion).where(TransactionVersion.transaction_id==target));start=perf_counter();rows,coverage=duplicates.search(s,identity,v,profile);lookup.append((perf_counter()-start)*1000)
        for i in range(10):
            start_all=perf_counter()
            with db.session(identity) as s:created=finance.enqueue(s,identity,target,1,'Measure actual isolated finalization','phase3-benchmark',f'iteration-{i}')
            job_id,owner,actor_id=claim(db,identity)
            with db.session(identity) as s:
                job=finance.get(s,Job,identity,job_id);v=s.scalar(select(TransactionVersion).where(TransactionVersion.transaction_id==target));context=finance.build_context(s,identity,job,v);start=perf_counter();d=evaluate(context);pure.append((perf_counter()-start)*1000)
            start=perf_counter()
            with db.session(identity) as s:eid=finance.finalize(s,identity,job_id,owner)
            finalize.append((perf_counter()-start)*1000);end_to_end.append((perf_counter()-start_all)*1000)
            with db.session(identity) as s:t=finance.get(s,Transaction,identity,target);decisions.append(t.decision);assert t.decision=='PASS',t.decision
        with db.session(identity) as s:
            pg=s.scalar(text('SELECT version()'));counts=dict(s.execute(text('SELECT kind,count(*) FROM reference_records GROUP BY kind')).all())
            plan=s.execute(text("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT id FROM reference_records WHERE tenant_id=:tenant AND legal_entity_id=:entity AND kind='historical_transactions' AND party_id=:party AND number_key='synthetic-history-00000'"),{'tenant':identity.tenant_id,'entity':identity.legal_entity_id,'party':UUID(vendor)}).scalar()
        cpu=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),'Unavailable');memory=next(line for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemTotal'))
        output={'version':'finance-phase3-benchmark-v1','synthetic':True,'environment':{'python':platform.python_version(),'platform':platform.platform(),'cpu':cpu,'memory':memory,'postgresql':pg},'dataset':{'generated_history':10000,'structured_transactions':200,'reference_counts':counts},'measurements':{'duplicate_candidate_lookup':stats(lookup),'pure_rules_including_po_grn':stats(pure),'transactional_finalization_including_budget':stats(finalize),'enqueue_claim_context_finalization':stats(end_to_end)},'computed_decisions':decisions,'lookup_plan':plan,'limitations':'Warm local development samples, single process; no production SLA or live VLM/image-history benchmark. Each finalization rechecks actual PG capacity and replaces only its own unconsumed reservation.'}
        target_file=ROOT/'generated/reports/finance-phase3.json';target_file.parent.mkdir(parents=True,exist_ok=True);target_file.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'dataset':output['dataset'],'measurements':output['measurements'],'report':str(target_file)}))
    finally:
        if db:db.engine.dispose()
        with control.begin() as c:c.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control.dispose()

if __name__=='__main__':main()
