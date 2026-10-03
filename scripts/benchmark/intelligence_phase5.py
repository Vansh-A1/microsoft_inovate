"""Actual PIT feature measurements on 10k synthetic facts in an owned disposable schema."""
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from uuid import UUID,uuid4
import json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'apps/api'),str(ROOT/'scripts/benchmark')]
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine,text,select,event
from sqlalchemy.engine import make_url
from app.core.config import Settings
from app.core.identity import authenticate
from app.core.serialization import digest,utcnow
from app.db.session import Database
from app.db.models import Transaction,TransactionVersion
from app.services.references import seed_references
from app.services import finance,intelligence as ml
from app.risk import features,anomaly
from app.schemas.canonical import fixture_canonical
from finance_phase3 import stats

def main():
    settings=Settings.load();ctx=replace(authenticate(next(iter(settings.identities)),settings),roles=frozenset({'ML_ADMIN','FINANCE_REVIEWER'}))
    base=make_url(settings.database_url).set(database='ap_phase1_test');schema='bench_phase5_'+uuid4().hex;control=create_engine(base);db=None
    with control.begin() as c:c.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        url=base.update_query_dict({'options':f'-csearch_path={schema}'});cfg=Config(str(ROOT/'apps/api/alembic.ini'));cfg.attributes['database_url']=url.render_as_string(hide_password=False);command.upgrade(cfg,'head')
        db=Database(cfg.attributes['database_url']);db.settings=settings
        with db.session(ctx) as s:snapshot=seed_references(s,ctx)
        p=fixture_canonical(json.loads((ROOT/'data/golden_cases/vendor/clean.json').read_text())['transaction'])
        ids=[uuid4() for _ in range(10000)]
        with db.session(ctx) as s:
            s.add_all([Transaction(**ctx.scope(),id=tid,branch='VENDOR_INVOICE',latest_version=1,row_version=1,processing_state='RECEIVED',eligible=False) for tid in ids]);s.flush()
            versions=[]
            for i,tid in enumerate(ids):
                amount=str(Decimal('1000')+Decimal(i%101));facts=p|{'invoice_number':f'SYNTHETIC-P5-HISTORY-{i:05d}','invoice_date':'2026-09-01','total_amount':amount,'subtotal_amount':amount,'tax_amount':'0','source_document_id':None}
                facts['lines']=[p['lines'][0]|{'quantity':'1','unit_price':amount,'net_amount':amount,'tax_rate':'0','tax_amount':'0','gross_amount':amount}]
                versions.append(TransactionVersion(**ctx.scope(),transaction_id=tid,version=1,payload=facts,total_amount=Decimal(amount),currency='INR',business_date=date(2026,9,1),party_id=UUID(p['vendor_id']),number_key=facts['invoice_number'],content_digest=digest(facts),author_id=ctx.actor_id,change_reason='Synthetic submitted facts for isolated measurement'))
            s.add_all(versions)
        with db.session(ctx) as s:current=finance.create_transaction(s,ctx,p|{'invoice_number':'SYNTHETIC-P5-CURRENT'},'Synthetic PIT measurement target','benchmark');v=s.scalar(select(TransactionVersion).where(TransactionVersion.transaction_id==UUID(current['id'])));s.execute(text('ANALYZE transaction_versions'))
        cutoff=utcnow();values={};last=None;history_rows=None;captured=[]
        def capture(conn,cursor,statement,parameters,context,executemany):
            if 'row_number()' in statement and not statement.startswith('EXPLAIN'):captured.append((statement,parameters))
        event.listen(db.engine,'before_cursor_execute',capture)
        timings=[]
        for _ in range(5):
            start=perf_counter()
            with db.session(ctx) as s:history_rows,coverage=ml.history(s,ctx,v,cutoff)
            timings.append((perf_counter()-start)*1000)
        event.remove(db.engine,'before_cursor_execute',capture);values['pit_history_query_10000']=stats(timings)
        timings=[]
        for _ in range(5):
            start=perf_counter();last=features.build(v.payload,v.transaction_id,1,cutoff,snapshot.id,history_rows,coverage=coverage)
            timings.append((perf_counter()-start)*1000)
        values['feature_build_10000']=stats(timings);scores=[]
        for _ in range(20):start=perf_counter();scored=anomaly.score(last);scores.append((perf_counter()-start)*1000)
        values['statistical_score']=stats(scores)
        assert last['values']['history_count']==10000 and str(v.transaction_id) not in [r['object_id'] for r in last['history_manifest']]
        assert digest(last)==digest(features.build(v.payload,v.transaction_id,1,cutoff,snapshot.id,history_rows,coverage=coverage))
        with db.session(ctx) as s:plan=s.connection().exec_driver_sql('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+captured[0][0],captured[0][1]).scalar()
        output={'version':'intelligence-phase5-benchmark-v1','synthetic':True,'history_count':10000,'branches':['VENDOR_INVOICE'],
            'measurements':values,'anomaly_output':scored,'feature_snapshot_digest':digest(last),'history_query_plan':plan,
            'supervised_metrics':None,'limitation':'Five warm local query/build samples and 20 score samples; development pipeline measurement only. No representative data, classifier accuracy, VLM execution or production SLA.'}
        path=ROOT/'generated/reports/intelligence-phase5.json';path.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'history_count':10000,'measurements':values,'report':str(path)},indent=2))
    finally:
        if db:db.engine.dispose()
        with control.begin() as c:c.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control.dispose()
if __name__=='__main__':main()
