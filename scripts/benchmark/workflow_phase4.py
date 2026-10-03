#!/usr/bin/env python3
"""Measure real local workflow operations in an owned disposable PostgreSQL schema."""
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from uuid import UUID,uuid4
import json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'apps/api'),str(ROOT/'scripts/seed'),str(ROOT/'scripts/benchmark')]
from sqlalchemy import create_engine,select,text
from sqlalchemy.engine import make_url
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.core.identity import authenticate
from app.db.session import Database
from app.db.models import Transaction,ReviewCase,Evaluation,Report
from app.services import finance,operations,reviews
from app.services.references import seed_references
from app.services.worker import run_once
from app.schemas.canonical import fixture_canonical
from app.integrations.storage import LocalStorage
from phase3 import enable
from finance_phase3 import stats


def main():
    settings=Settings.load();ctx=authenticate(next(iter(settings.identities)),settings)
    ctx=replace(ctx,roles=ctx.roles|{'FINANCE_REVIEWER','FINANCE_SUBMITTER','REFERENCE_ADMIN','OPERATIONS_ADMIN','REPORT_EXPORTER'})
    base=make_url(settings.database_url).set(database='ap_phase1_test');schema='bench_phase4_'+uuid4().hex
    control=create_engine(base);db=None;values={};plan={}
    with control.begin() as c:c.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        url=base.update_query_dict({'options':f'-csearch_path={schema}'})
        cfg=Config(str(ROOT/'apps/api/alembic.ini'));cfg.attributes['database_url']=url.render_as_string(hide_password=False)
        command.upgrade(cfg,'head');db=Database(cfg.attributes['database_url']);db.settings=settings
        with db.session(ctx) as s:seed_references(s,ctx)
        enable(db,ctx)
        p=fixture_canonical(json.loads((ROOT/'data/golden_cases/vendor/clean.json').read_text())['transaction'])
        ids=[]
        for n in range(100):
            with db.session(ctx) as s:
                tid=uuid4();finance.create_transaction(s,ctx,p|{'invoice_number':f'SYNTHETIC-P4-BENCH-{n:04}'},'Fictional bounded workflow measurement','phase4-benchmark',tid)
                finance.enqueue(s,ctx,tid,1,'Compute actual finance findings','phase4-benchmark',f'bench-{n}')
            ids.append(tid)
        while run_once(db,ctx):pass
        target=ids[0]
        with db.session(ctx) as s:
            t=finance.get(s,Transaction,ctx,target);evaluation=t.latest_evaluation_id
            case=s.scalar(select(ReviewCase).where(ReviewCase.transaction_id==target))
            review_id=case.id;content=s.scalar(select(Report).where(Report.evaluation_id==evaluation)).content
        storage=LocalStorage(ROOT/'runtime/benchmark-storage-phase4')
        def measure(label,fn,samples=10):
            timings=[]
            for _ in range(samples):
                start=perf_counter()
                with db.session(ctx) as s:fn(s)
                timings.append((perf_counter()-start)*1000)
            values[label]=stats(timings)
        measure('review_queue_25',lambda s:operations.review_queue(s,ctx,limit=25))
        measure('case_detail',lambda s:finance.transaction_detail(s,ctx,target))
        measure('audit_timeline_50',lambda s:operations.timeline(s,ctx,target))
        measure('dashboard',lambda s:operations.dashboard(s,ctx))
        def assignment(s):
            r=finance.get(s,ReviewCase,ctx,review_id)
            data={'expected_review_version':r.row_version,'expected_transaction_version':1,'reason_code':'PERFORMANCE_CHECK','comment':'Fictional measured assignment','action':'RELEASE' if r.owner_id else 'CLAIM'}
            reviews.assign(s,ctx,review_id,data,'phase4-benchmark')
        measure('assignment_action',assignment)
        measure('report_export_generation',lambda s:operations.prepare_export(s,ctx,evaluation,'csv','phase4-benchmark'))
        measure('reconciliation_batch',lambda s:operations.reconcile(s,ctx,storage,'Bounded fictional consistency inspection','phase4-benchmark'),3)
        start=perf_counter()
        with db.session(ctx) as s:
            r=finance.get(s,ReviewCase,ctx,review_id)
            if not r.owner_id:reviews.assign(s,ctx,review_id,{'expected_review_version':r.row_version,'expected_transaction_version':1,'reason_code':'PERFORMANCE_CHECK','comment':'Claim fictional correction case','action':'CLAIM'},'phase4-benchmark')
            data={'expected_review_version':r.row_version,'expected_transaction_version':1,'reason_code':'PERFORMANCE_CHECK','comment':'Correct fictional benchmark identity','action':'CORRECT_FIELD','transaction':p|{'invoice_number':'SYNTHETIC-P4-BENCH-CORRECTED'},'evidence_ids':[content['rules'][0]['evidence'][0]['id']]}
            reviews.act(s,ctx,review_id,data,'phase4-benchmark')
        while run_once(db,ctx):pass
        values['correction_and_reevaluation']=stats([(perf_counter()-start)*1000])
        measure('cancellation',lambda s:reviews.cancel(s,ctx,ids[1],1,'Cancel fictional measured obligation','phase4-benchmark'),1)
        with db.session(ctx) as s:
            for table in ('review_cases','audit_events','jobs','evaluations'):s.execute(text('ANALYZE '+table))
            queries={
                'queue':"SELECT id FROM review_cases WHERE tenant_id=:tenant AND legal_entity_id=:entity AND state IN ('OPEN','ASSIGNED','AWAITING_INFORMATION') ORDER BY created_at,id LIMIT 26",
                'owned_queue':"SELECT id FROM review_cases WHERE tenant_id=:tenant AND legal_entity_id=:entity AND owner_id=:actor AND state='ASSIGNED' ORDER BY created_at,id LIMIT 26",
                'timeline':"SELECT id FROM audit_events WHERE tenant_id=:tenant AND legal_entity_id=:entity AND object_id=:target ORDER BY sequence LIMIT 51",
                'jobs':"SELECT id FROM jobs WHERE tenant_id=:tenant AND legal_entity_id=:entity AND state='FAILED' ORDER BY updated_at,id LIMIT 51"}
            for key,query in queries.items():plan[key]=s.scalar(text('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query),{'tenant':ctx.tenant_id,'entity':ctx.legal_entity_id,'actor':ctx.actor_id,'target':target})
            decisions=dict(s.execute(select(Transaction.decision,text('count(*)')).group_by(Transaction.decision)).all())
            pg=s.scalar(text('SELECT version()'))
        output={'version':'workflow-phase4-benchmark-v1','synthetic':True,'dataset':{'computed_transactions':100,'decisions':{k or 'CANCELLED':v for k,v in decisions.items()}},'measurements':values,'postgresql':pg,'query_plans':plan,'limits':'Warm local single-process measurements; 100 computed synthetic cases, not a production SLA, load test or live inference benchmark. Cancellation and correction each have one sample.'}
        path=ROOT/'generated/reports/workflow-phase4.json';path.write_text(json.dumps(output,indent=2)+'\n')
        print(json.dumps({'dataset':output['dataset'],'measurements':values,'report':str(path)},indent=2))
    finally:
        if db:db.engine.dispose()
        with control.begin() as c:c.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control.dispose()


if __name__=='__main__':main()
