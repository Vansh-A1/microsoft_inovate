from datetime import timedelta
from decimal import Decimal
import csv,json
from io import StringIO,BytesIO
from uuid import UUID,uuid4
from sqlalchemy import select,text,func,update
from sqlalchemy.exc import DBAPIError,IntegrityError
import pytest
from app.core.errors import DomainError
from app.core.config import ROOT
from app.core.serialization import digest,utcnow
from app.db.models import *
from app.db.session import Database
from app.schemas.canonical import fixture_canonical
from app.services import finance
from app.rules.engine import RULE_IDS
from app.services.worker import run_once,claim
from app.services.imports import parse_file
from app.integrations.storage import LocalStorage
from phase1 import seed


def payload(name='vendor/clean'):
    return fixture_canonical(json.loads((ROOT/f'data/golden_cases/{name}.json').read_text())['transaction'])


def headers(key=None):return {'Idempotency-Key':key or str(uuid4())}


def create(client,data=None):
    r=client.post('/api/v1/transactions',json=data or payload(),headers=headers());assert r.status_code==201,r.text
    return r.json()['id']


def evaluate_case(client,database,identity,record_id,version=1):
    r=client.post(f'/api/v1/transactions/{record_id}/evaluate',json={'expected_version':version,'reason':'Test evaluation'},headers=headers());assert r.status_code==202,r.text
    assert run_once(database,identity)
    job=client.get('/api/v1/jobs/'+r.json()['job_id']).json();assert job['state']=='SUCCEEDED',job
    return client.get('/api/v1/evaluations/'+job['evaluation_id']).json()


@pytest.mark.parametrize('name,expected',[('vendor/clean','PASS'),('vendor/paid_duplicate','HOLD'),('vendor/partial_grn','HOLD'),('vendor/approval_pending','HOLD'),('employee/clean_taxi','PASS'),('employee/hotel_two_nights','PASS'),('employee/hotel_unknown_nights','REVIEW'),('employee/daily_meals','REVIEW')])
def test_real_postgres_golden_end_to_end(environment,name,expected):
    db,ctx,other,client,cfg=environment
    records=seed(db,ctx,[name]);r=records[0];assert r['decision']==expected,r
    report=client.get('/api/v1/evaluations/'+r['latest_evaluation_id']).json()
    assert report['decision']==expected and len(report['rules'])==len(RULE_IDS)
    assert report['model_status']=='NOT_CONFIGURED' and 'risk_score' not in report
    assert report['current_eligible']==(expected=='PASS')
    for rule in report['rules']:
        for evidence in rule['evidence']:
            resolved=client.get('/api/v1/evidence/'+evidence['id']);assert resolved.status_code==200,resolved.text
            assert resolved.json()['bbox'] is None
    html=client.get(f"/api/v1/evaluations/{r['latest_evaluation_id']}/report?format=html")
    assert html.status_code==200 and 'NOT_CONFIGURED' in html.text and 'VAL-003' in html.text
    queue=client.get('/api/v1/reviews').json()['items'];assert bool(queue)==(expected!='PASS')


def test_auth_scope_and_database_rls(environment):
    db,ctx,other,client,cfg=environment
    r=seed(db,ctx,['vendor/clean'])[0];rid=r['id'];eid=r['latest_evaluation_id']
    rules=client.get('/api/v1/evaluations/'+eid).json()['rules'];evidence=rules[0]['evidence'][0]['id']
    document_evidence=next(e['id'] for r in rules for e in r['evidence'] if e['reference']['kind']=='DOCUMENT_FIELD')
    assert client.get('/api/v1/evidence/'+document_evidence,headers={'Authorization':'Bearer test-second'}).status_code==404
    for route in [f'/transactions/{rid}',f'/evaluations/{eid}',f'/evidence/{evidence}',f'/evaluations/{eid}/report']:
        assert client.get('/api/v1'+route,headers={'Authorization':'Bearer test-second'}).status_code==404
    assert client.get('/api/v1/transactions',headers={'Authorization':'Bearer test-second'}).json()['items']==[]
    assert client.get('/api/v1/me',headers={'Authorization':'Bearer forged'}).status_code==401
    assert client.post('/api/v1/transactions',json=payload(),headers=headers()|{'Authorization':'Bearer test-reader'}).status_code==403
    assert client.post('/api/v1/transactions',json=payload()|{'tenant_id':str(other.tenant_id)},headers=headers()).status_code==422
    with db.session(other) as s:assert list(s.scalars(select(Transaction)))==[]  # raw query still isolated by RLS
    from dataclasses import replace
    same_tenant_other_entity=replace(ctx,legal_entity_id=UUID('20000000-0000-4000-8000-000000000002'))
    with db.session(same_tenant_other_entity) as s:assert list(s.scalars(select(Transaction)))==[]
    with db.engine.connect() as conn:
        assert conn.scalar(text('SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user')) is False
        assert conn.scalar(text('SELECT count(*) FROM transactions'))==0


def test_idempotent_create_revision_and_evaluate(environment):
    db,ctx,other,client,cfg=environment;key=headers('stable-create')
    a=client.post('/api/v1/transactions',json=payload(),headers=key);b=client.post('/api/v1/transactions',json=payload(),headers=key)
    assert a.status_code==b.status_code==201 and a.json()==b.json()
    assert client.post('/api/v1/transactions',json=payload()|{'invoice_number':'DIFFERENT'},headers=key).status_code==409
    rid=a.json()['id'];body={'expected_version':1,'reason':'Queue deterministic checks'};key=headers('stable-eval')
    a=client.post(f'/api/v1/transactions/{rid}/evaluate',json=body,headers=key);b=client.post(f'/api/v1/transactions/{rid}/evaluate',json=body,headers=key)
    assert a.status_code==b.status_code==202 and a.json()==b.json()
    assert run_once(db,ctx)
    case=client.get('/api/v1/transactions/'+rid).json();assert case['decision']=='HOLD'  # intake cannot self-authorize approvals
    revision={'expected_version':1,'reason':'Correct reference number','transaction':payload()|{'invoice_number':'CORRECTED'}};key=headers('stable-revision')
    a=client.post(f'/api/v1/transactions/{rid}/revisions',json=revision,headers=key);b=client.post(f'/api/v1/transactions/{rid}/revisions',json=revision,headers=key)
    assert a.status_code==b.status_code==201 and a.json()==b.json()
    assert client.post(f'/api/v1/transactions/{rid}/revisions',json=revision,headers=headers()).status_code==409
    current=client.get('/api/v1/transactions/'+rid).json();assert len(current['versions'])==2 and current['versions'][0]['payload']['invoice_number']!=current['versions'][1]['payload']['invoice_number']
    assert current['eligible'] is False and current['decision'] is None
    assert client.post(f'/api/v1/transactions/{rid}/evaluate',json={'expected_version':1,'reason':'Stale screening request'},headers=headers()).status_code==409
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(Transaction))==1


def test_re_evaluation_supersedes_immutable_reports_and_reservations(environment):
    db,ctx,other,client,cfg=environment;r=seed(db,ctx,['vendor/clean'])[0];rid=r['id'];old=r['latest_evaluation_id']
    original=client.get('/api/v1/evaluations/'+old+'/report').json()
    current=evaluate_case(client,db,ctx,rid)
    assert current['decision']=='PASS' and current['supersedes_id']==old
    assert client.get('/api/v1/evaluations/'+old+'/report').json()==original
    assert client.get('/api/v1/evaluations/'+old).json()['current_eligible'] is False
    with db.session(ctx) as s:
        reservations=list(s.scalars(select(CapacityReservation).where(CapacityReservation.state=='ACTIVE')))
        assert len(reservations)==3 and sum(r.quantity for r in reservations if r.kind=='GRN_LINE')==Decimal('20')
        assert next(r for r in reservations if r.kind=='BUDGET').amount==Decimal('0')
        assert s.scalar(select(func.count()).select_from(Evaluation))==2


def test_db_constraints_and_immutable_bulk_update(environment):
    db,ctx,other,client,cfg=environment;rid=create(client)
    with pytest.raises(DBAPIError):
        with db.session(ctx) as s:s.execute(update(TransactionVersion).where(TransactionVersion.transaction_id==UUID(rid)).values(content_digest='f'*64))
    with pytest.raises(DBAPIError):
        with db.session(ctx) as s:s.execute(update(Transaction).where(Transaction.id==UUID(rid)).values(eligible=True,decision='HOLD'))
    with pytest.raises(DBAPIError):
        with db.session(ctx) as s:s.add(ReviewCase(**ctx.scope(),transaction_id=uuid4(),evaluation_id=uuid4(),decision='HOLD',branch='VENDOR_INVOICE',reasons=[]));s.flush()
    detail=client.get('/api/v1/transactions/'+rid).json();assert detail['version']==1
    with db.engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace=current_schema()::regnamespace AND relkind='r' AND relrowsecurity AND relforcerowsecurity"))==22
        assert c.scalar(text("SELECT numeric_scale FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='transaction_versions' AND column_name='total_amount'"))==6


def test_atomic_audit_failure_rolls_back_creation(environment,monkeypatch):
    db,ctx,other,client,cfg=environment
    def fail(*args,**kwargs):raise RuntimeError('simulated append failure')
    monkeypatch.setattr(finance,'audit',fail)
    with pytest.raises(RuntimeError):
        with db.session(ctx) as s:finance.create_transaction(s,ctx,payload(),'Rollback probe','probe')
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(Transaction))==0
        assert s.scalar(select(func.count()).select_from(TransactionVersion))==0


def test_worker_recovers_expired_lease_and_effects_are_idempotent(environment):
    db,ctx,other,client,cfg=environment;rid=create(client)
    reply=client.post(f'/api/v1/transactions/{rid}/evaluate',json={'expected_version':1,'reason':'Crash recovery probe'},headers=headers()).json();job_id=UUID(reply['job_id'])
    leased=claim(db,ctx);assert leased[0]==job_id
    assert claim(db,ctx) is None
    with db.session(ctx) as s:job=finance.get(s,Job,ctx,job_id);job.lease_until=utcnow()-timedelta(seconds=1)
    assert run_once(db,ctx)
    with db.session(ctx) as s:
        job=finance.get(s,Job,ctx,job_id);eid=job.result_evaluation_id
        assert job.attempts==2 and job.state=='SUCCEEDED'
        assert finance.finalize(s,ctx,job_id,uuid4())==eid
        assert s.scalar(select(func.count()).select_from(Evaluation))==1
        assert s.scalar(select(func.count()).select_from(Report))==1
        assert s.scalar(select(OutboxEvent)).delivered_at is not None


def test_worker_retry_safe_failure_no_partial_evaluation(environment,monkeypatch):
    from app.services import worker
    db,ctx,other,client,cfg=environment;rid=create(client)
    job=client.post(f'/api/v1/transactions/{rid}/evaluate',json={'expected_version':1,'reason':'Retry probe'},headers=headers()).json()['job_id']
    def fail(*args,**kwargs):raise RuntimeError('secret must never be recorded')
    monkeypatch.setattr(finance,'audit',fail)
    assert run_once(db,ctx)
    current=client.get('/api/v1/jobs/'+job).json();assert current['state']=='RETRYABLE' and current['last_error']=='EXECUTION_FAILED'
    assert 'secret' not in json.dumps(current)
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(Evaluation))==0


def test_stale_job_never_finalizes_old_version(environment):
    db,ctx,other,client,cfg=environment;rid=create(client)
    queued=client.post(f'/api/v1/transactions/{rid}/evaluate',json={'expected_version':1,'reason':'Old version'},headers=headers()).json()
    revision={'expected_version':1,'reason':'Updated before worker','transaction':payload()}
    assert client.post(f'/api/v1/transactions/{rid}/revisions',json=revision,headers=headers()).status_code==201
    assert run_once(db,ctx)
    assert client.get('/api/v1/jobs/'+queued['job_id']).json()['state']=='STALE'
    assert client.get('/api/v1/transactions/'+rid).json()['eligible'] is False


def import_bytes(data):
    f=StringIO();writer=csv.writer(f);writer.writerow(['transaction_json']);writer.writerow([json.dumps(data)]);writer.writerow(['{bad json']);return f.getvalue().encode()


def test_csv_preview_commit_invalid_rows_retained_and_evidence_resolves(environment):
    db,ctx,other,client,cfg=environment;body=import_bytes(payload('employee/clean_taxi'));key=headers('import-preview')
    a=client.post('/api/v1/imports/preview',files={'file':('rows.csv',body,'text/csv')},headers=key);b=client.post('/api/v1/imports/preview',files={'file':('rows.csv',body,'text/csv')},headers=key)
    assert a.status_code==201,a.text
    assert a.json()==b.json() and a.json()['invalid_count']==1 and a.json()['valid_count']==1
    bid=a.json()['id'];assert [r['row_number'] for r in a.json()['rows']]==[2,3]
    key=headers('commit-import');a=client.post(f'/api/v1/imports/{bid}/commit',headers=key);b=client.post(f'/api/v1/imports/{bid}/commit',headers=key)
    assert a.status_code==200,a.text
    assert a.json()==b.json() and a.json()['state']=='COMMITTED'
    assert a.json()['rows'][1]['transaction_id'] is None and a.json()['rows'][1]['errors']
    assert run_once(db,ctx);rid=a.json()['rows'][0]['transaction_id'];current=client.get('/api/v1/transactions/'+rid).json();report=client.get('/api/v1/evaluations/'+current['latest_evaluation_id']).json()
    imported=[e for r in report['rules'] for e in r['evidence'] if e['reference']['kind']=='IMPORT_CELL'];assert imported
    resolved=client.get('/api/v1/evidence/'+imported[0]['id']).json();assert resolved['source']['row_number']==2
    with pytest.raises(DBAPIError):
        with db.session(ctx) as s:s.execute(update(ImportRow).values(raw_values={'transaction_json':'replacement'}))


def test_xlsx_text_rows_and_formula_rejection(environment):
    from openpyxl import Workbook
    db,ctx,other,client,cfg=environment;book=Workbook();sheet=book.active;sheet.title='Claims';sheet.append(['transaction_json']);sheet.append([json.dumps(payload('employee/clean_taxi'))]);sheet.append(['=1+1']);sheet.append([123.45]);f=BytesIO();book.save(f)
    r=client.post('/api/v1/imports/preview',files={'file':('claims.xlsx',f.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},headers=headers());assert r.status_code==201,r.text
    assert r.json()['row_count']==3 and r.json()['invalid_count']==2 and r.json()['rows'][1]['raw_values']['transaction_json']=='=1+1'


def test_private_storage_paths_and_tenant_boundaries(environment,tmp_path):
    db,ctx,other,client,cfg=environment;storage=LocalStorage(tmp_path/'store');key,hashed=storage.put(ctx,b'synthetic')
    assert storage.get(ctx,key)==b'synthetic' and len(hashed)==64
    for bad in ['../../etc/passwd','https://example.com/file',key.replace(str(ctx.tenant_id),str(other.tenant_id))]:
        with pytest.raises((ValueError,DomainError)):storage.get(ctx,bad)
    with pytest.raises((ValueError,DomainError)):storage.get(other,key)


def test_fresh_migrations_upgrade_downgrade_and_ready(environment):
    from alembic import command
    db,ctx,other,client,cfg=environment;assert client.get('/api/v1/health/ready').status_code==200
    # Fresh additional schema, never reset the seeded application database.
    from sqlalchemy.engine import make_url
    schema='roundtrip_'+uuid4().hex
    with db.engine.begin() as conn:conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    url=make_url(cfg.attributes['database_url']).update_query_dict({'options':f'-csearch_path={schema}'})
    cfg.attributes['database_url']=url.render_as_string(hide_password=False)
    command.upgrade(cfg,'head');command.downgrade(cfg,'base');command.upgrade(cfg,'head')
    temporary=Database(url.render_as_string(hide_password=False))
    with temporary.engine.connect() as conn:assert conn.scalar(text("SELECT count(*) FROM information_schema.tables WHERE table_schema=current_schema()"))==23
    temporary.engine.dispose()
    with db.engine.begin() as conn:conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


def test_filters_reports_escape_and_audit_chain(environment):
    db,ctx,other,client,cfg=environment;seed(db,ctx,['vendor/clean','employee/daily_meals','vendor/approval_pending'])
    assert len(client.get('/api/v1/reviews?decision=HOLD&reason=APR-001&branch=VENDOR_INVOICE').json()['items'])==1
    assert client.get('/api/v1/reviews?minimum_age_days=1').json()['items']==[]
    assert len(client.get('/api/v1/transactions?decision=PASS').json()['items'])==1
    assert client.get('/api/v1/transactions?limit=999').status_code==400
    rows=client.get('/api/v1/audit').json()['items'];assert rows
    assert all(b['previous_hash']==a['event_hash'] for a,b in zip(rows,rows[1:]))
    output=finance.report_html({'decision':'<script>alert(1)</script>','transaction_id':'x','transaction_version':1,'eligible':False,'evaluation_id':'x','evaluated_at':'x','rules':[],'next_actions':['<img src=x onerror=alert(1)>']})
    assert '<script>' not in output and '<img' not in output and '&lt;script&gt;' in output


def test_sqlite_never_silent_application_fallback():
    with pytest.raises(ValueError):Database('sqlite://')


def trusted_claim(session,ctx,p,source_fact,approver_roles):
    """Test-only trusted authority provisioning; ordinary API has no approval write surface."""
    rid=uuid4();document=uuid4();source_fact=source_fact|{'id':str(document)};p=p|{'source_document_id':str(document)}
    if p['branch']=='EMPLOYEE_EXPENSE':p['items']=[item|{'source_document_id':str(document),'id':str(uuid4())} for item in p['items']]
    session.add(ReferenceRecord(**ctx.scope(),id=document,version=1,kind='documents',label='Test synthetic source',payload=source_fact));session.flush()
    finance.create_transaction(session,ctx,p,'Trusted test structured data','concurrency-test',rid)
    for index,role in enumerate(approver_roles,1):
        actor=UUID('51000000-0000-4000-8000-000000000003' if role=='MANAGER' else '51000000-0000-4000-8000-000000000004')
        session.add(ApprovalRecord(**ctx.scope(),transaction_id=rid,transaction_version=1,policy_id=UUID(p['approval_policy_id']),policy_version=1,actor_id=actor,role=role,sequence=index,state='APPROVED',approved_at=utcnow()-timedelta(seconds=10)))
    session.flush();finance.enqueue(session,ctx,rid,1,'Concurrent admission test','test',str(rid));return rid


@pytest.mark.parametrize('kind',['BUDGET','GRN_LINE'])
def test_concurrent_admission_never_overallocates(environment,kind):
    from concurrent.futures import ThreadPoolExecutor
    db,ctx,other,client,cfg=environment
    with db.session(ctx) as s:
        if kind=='BUDGET':
            base=payload('employee/clean_taxi');old=s.scalar(select(ReferenceRecord).where(ReferenceRecord.id==UUID(base['budget_id']))).payload
            budget_id=uuid4();ledger_id=uuid4();ledger={'id':str(ledger_id),'version':1,**{k:str(v) for k,v in ctx.scope().items()},'entry_type':'ALLOCATION','amount':'100.00','currency':'INR'}
            budget=old|{'id':str(budget_id),'ledger':[ledger]}
            s.add(ReferenceRecord(**ctx.scope(),id=budget_id,version=1,kind='budgets',label='Test budget 100',payload=budget));s.add(ReferenceRecord(**ctx.scope(),id=ledger_id,version=1,kind='budget_ledger',label='Test allocation',payload=ledger));s.flush()
            document=s.scalar(select(ReferenceRecord).where(ReferenceRecord.id==UUID(base['items'][0]['source_document_id']))).payload
            for index in range(2):
                p=base|{'claim_number':f'TEST-CAPACITY-{index}','requested_amount':'80.00','budget_id':str(budget_id),'items':[base['items'][0]|{'claimed_amount':'80.00','receipt_total_amount':'80.00'}]}
                trusted_claim(s,ctx,p,document|{'facts':document['facts']|{'receipt_total_amount':'80.00'}},['MANAGER'])
        else:
            base=payload();document=s.scalar(select(ReferenceRecord).where(ReferenceRecord.id==UUID(base['source_document_id']))).payload
            for index in range(2):
                p=base|{'invoice_number':f'TEST-GRN-{index}','subtotal_amount':'30000.00','tax_amount':'5400.00','total_amount':'35400.00','lines':[base['lines'][0]|{'quantity':'30.0000','net_amount':'30000.00','tax_amount':'5400.00','gross_amount':'35400.00'}]}
                trusted_claim(s,ctx,p,document|{'facts':document['facts']|{'invoice_number':p['invoice_number'],'quantity':'30.0000','total_amount':'35400.00'}},['MANAGER','DEPARTMENT_HEAD'])
    with ThreadPoolExecutor(max_workers=2) as workers:assert all(workers.map(lambda _:run_once(db,ctx),range(2)))
    with db.session(ctx) as s:
        decisions=list(s.scalars(select(Transaction.decision)));assert sorted(decisions)==['HOLD','PASS'],decisions
        active=list(s.scalars(select(CapacityReservation).where(CapacityReservation.state=='ACTIVE',CapacityReservation.kind==kind)))
        assert sum((r.amount if kind=='BUDGET' else r.quantity for r in active),Decimal('0'))==Decimal('80' if kind=='BUDGET' else '30')


def test_same_number_other_vendor_not_duplicate(environment):
    db,ctx,other,client,cfg=environment;p=payload('vendor/paid_duplicate');vendor=uuid4()
    with db.session(ctx) as s:
        old=s.scalar(select(ReferenceRecord).where(ReferenceRecord.id==UUID(p['vendor_id']))).payload
        s.add(ReferenceRecord(**ctx.scope(),id=vendor,version=1,kind='vendors',label='Second test vendor',payload=old|{'id':str(vendor),'legal_name':'Second synthetic vendor'}))
    rid=create(client,p|{'vendor_id':str(vendor)})
    report=evaluate_case(client,db,ctx,rid);rule=next(r for r in report['rules'] if r['rule_id']=='DUP-002')
    assert rule['status']=='PASS' and rule['observed']['matching_record_ids']==[]


def test_audit_failure_blocks_pass_and_all_effects(environment,monkeypatch):
    from phase1 import seed_case
    db,ctx,other,client,cfg=environment
    with db.session(ctx) as s:rid=seed_case(s,ctx,'vendor/clean')
    leased=claim(db,ctx);original=finance.audit
    def fail_on_finalize(*args,**kwargs):
        if args[2]=='EVALUATION_FINALIZED':raise RuntimeError('audit append unavailable')
        return original(*args,**kwargs)
    monkeypatch.setattr(finance,'audit',fail_on_finalize)
    with pytest.raises(RuntimeError):
        with db.session(ctx) as s:finance.finalize(s,ctx,leased[0],leased[1])
    with db.session(ctx) as s:
        assert not finance.get(s,Transaction,ctx,rid).eligible
        assert s.scalar(select(func.count()).select_from(Evaluation))==0
        assert s.scalar(select(func.count()).select_from(CapacityReservation))==0
        assert s.scalar(select(func.count()).select_from(Report))==0


def test_persisted_pinned_inputs_reproduce_evaluation(environment):
    from app.rules.engine import evaluate,RuleContext
    db,ctx,other,client,cfg=environment;r=seed(db,ctx,['vendor/clean'])[0]
    with db.session(ctx) as s:
        pinned=s.scalar(select(EvaluationInput));assert pinned.content_digest==digest(pinned.encoded)
        assert evaluate(RuleContext(pinned.encoded)).decision==r['decision']
        assert evaluate(RuleContext(pinned.encoded)).eligible is True


def test_revision_invalidates_approved_version_and_capacity(environment):
    db,ctx,other,client,cfg=environment;r=seed(db,ctx,['vendor/clean'])[0]
    revised=client.post(f"/api/v1/transactions/{r['id']}/revisions",json={'expected_version':1,'reason':'Material amount correction','transaction':payload()|{'total_amount':'24000.00'}},headers=headers())
    assert revised.status_code==201
    report=evaluate_case(client,db,ctx,r['id'],2)
    assert report['decision']=='HOLD'
    assert next(rule for rule in report['rules'] if rule['rule_id']=='APR-001')['status']=='FAIL'
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(CapacityReservation).where(CapacityReservation.state=='ACTIVE'))==0


def test_newer_same_version_intent_makes_old_job_stale(environment):
    db,ctx,other,client,cfg=environment;rid=create(client);body={'expected_version':1,'reason':'Fresh deterministic intent'}
    first=client.post(f'/api/v1/transactions/{rid}/evaluate',json=body,headers=headers()).json()
    second=client.post(f'/api/v1/transactions/{rid}/evaluate',json=body,headers=headers()).json()
    assert run_once(db,ctx);assert client.get('/api/v1/jobs/'+first['job_id']).json()['state']=='STALE'
    assert run_once(db,ctx);assert client.get('/api/v1/jobs/'+second['job_id']).json()['state']=='SUCCEEDED'
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(Evaluation))==1


def test_retry_pass_has_one_capacity_effect(environment):
    from phase1 import seed_case
    db,ctx,other,client,cfg=environment
    with db.session(ctx) as s:rid=seed_case(s,ctx,'vendor/clean')
    leased=claim(db,ctx)
    with db.session(ctx) as s:finance.get(s,Job,ctx,leased[0]).lease_until=utcnow()-timedelta(seconds=1)
    assert run_once(db,ctx)
    with db.session(ctx) as s:
        job=finance.get(s,Job,ctx,leased[0]);assert job.state=='SUCCEEDED'
        assert finance.finalize(s,ctx,job.id,uuid4())==job.result_evaluation_id
        assert finance.get(s,Transaction,ctx,rid).eligible is True
        assert s.scalar(select(func.count()).select_from(Evaluation))==1
        assert s.scalar(select(func.count()).select_from(CapacityReservation).where(CapacityReservation.state=='ACTIVE'))==3


def test_worker_exhaustion_does_not_stop_drain_of_other_jobs(environment):
    db,ctx,other,client,cfg=environment;first=create(client);second=create(client,payload('employee/clean_taxi'))
    body={'expected_version':1,'reason':'Drain durable queue'}
    jobs=[client.post(f'/api/v1/transactions/{rid}/evaluate',json=body,headers=headers()).json()['job_id'] for rid in [first,second]]
    with db.session(ctx) as s:finance.get(s,Job,ctx,UUID(jobs[0])).attempts=3
    assert run_once(db,ctx);assert client.get('/api/v1/jobs/'+jobs[0]).json()['state']=='FAILED'
    assert client.get('/api/v1/transactions/'+first).json()['processing_state']=='FAILED_FINAL'
    assert run_once(db,ctx);assert client.get('/api/v1/jobs/'+jobs[1]).json()['state']=='SUCCEEDED'


def test_seed_rerun_keeps_one_logical_evaluation_and_effect(environment):
    db,ctx,other,client,cfg=environment;seed(db,ctx,['vendor/clean'])
    with db.session(ctx) as s:counts=[s.scalar(select(func.count()).select_from(model)) for model in [Transaction,Evaluation,ApprovalRecord,CapacityReservation,AuditEvent]]
    assert seed(db,ctx,['vendor/clean'])[0]['decision']=='PASS'
    with db.session(ctx) as s:assert counts==[s.scalar(select(func.count()).select_from(model)) for model in [Transaction,Evaluation,ApprovalRecord,CapacityReservation,AuditEvent]]


def test_insufficient_approver_authority_is_persisted_hold(environment):
    db,ctx,other,client,cfg=environment;rid=UUID(create(client))
    with db.session(ctx) as s:
        for seq,actor,role in [(1,'51000000-0000-4000-8000-000000000002','MANAGER'),(2,'51000000-0000-4000-8000-000000000004','DEPARTMENT_HEAD')]:
            s.add(ApprovalRecord(**ctx.scope(),transaction_id=rid,transaction_version=1,policy_id=UUID(payload()['approval_policy_id']),policy_version=1,actor_id=UUID(actor),role=role,sequence=seq,state='APPROVED',approved_at=utcnow()-timedelta(seconds=10)))
    report=evaluate_case(client,db,ctx,str(rid));approval=next(r for r in report['rules'] if r['rule_id']=='APR-002')
    assert report['decision']=='HOLD' and approval['status']=='FAIL' and approval['observed']['steps'][0]['actor_has_role'] is False


def test_arithmetic_and_bank_failures_have_persisted_evidence(environment):
    db,ctx,other,client,cfg=environment;original=payload();rid=create(client,original|{'total_amount':'23601.00','payment_account_token':'DEMO-UNAPPROVED-ACCOUNT'})
    report=evaluate_case(client,db,ctx,rid)
    assert report['decision']=='HOLD'
    for rule_id in ['VAL-003','VEN-003']:
        rule=next(r for r in report['rules'] if r['rule_id']==rule_id);assert rule['status']=='FAIL' and rule['evidence']
    with db.session(ctx) as s:assert s.scalar(select(ReferenceRecord).where(ReferenceRecord.id==UUID(original['vendor_id']))).payload['payment_account_token']==original['payment_account_token']


def test_http_envelope_and_request_size_limit(environment):
    db,ctx,other,client,cfg=environment
    assert client.get('/api/v1/unknown-route').json()['error']['code']=='HTTP_404'
    result=client.post('/api/v1/transactions',content=b' ' * 2300001,headers=headers()|{'Content-Type':'application/json'})
    assert result.status_code==413 and result.json()['error']['code']=='REQUEST_TOO_LARGE'


def test_incompatible_worker_stage_never_executes(environment):
    db,ctx,other,client,cfg=environment;rid=create(client);body={'expected_version':1,'reason':'Compatibility guard'}
    reply=client.post(f'/api/v1/transactions/{rid}/evaluate',json=body,headers=headers()).json()
    with db.session(ctx) as s:finance.get(s,Job,ctx,UUID(reply['job_id'])).stage_version='unavailable-rule-version'
    assert claim(db,ctx) is None
    with db.session(ctx) as s:
        assert not finance.get(s,Transaction,ctx,UUID(rid)).eligible
        assert s.scalar(select(func.count()).select_from(Evaluation))==0


def test_transaction_list_batches_current_facts_and_latest_jobs(environment):
    from sqlalchemy import event
    db,ctx,other,client,cfg=environment
    ids=[create(client,payload()|{'invoice_number':f'LIST-{i}'}) for i in range(5)]
    revision={'expected_version':1,'reason':'List current revision','transaction':payload()|{'invoice_number':'LIST-CORRECTED'}}
    assert client.post(f'/api/v1/transactions/{ids[0]}/revisions',json=revision,headers=headers()).status_code==201
    for number in range(2):
        r=client.post(f'/api/v1/transactions/{ids[0]}/evaluate',json={'expected_version':2,'reason':f'List intent {number}'},headers=headers())
        assert r.status_code==202
        last_job=r.json()['job_id']
    statements=[]
    def record(connection,cursor,statement,parameters,context,executemany):
        if statement.lstrip().upper().startswith('SELECT') and 'set_config' not in statement:statements.append(statement)
    event.listen(db.engine,'before_cursor_execute',record)
    try:response=client.get('/api/v1/transactions')
    finally:event.remove(db.engine,'before_cursor_execute',record)
    assert response.status_code==200 and len(statements)==3
    items={row['id']:row for row in response.json()['items']}
    assert set(items)==set(ids)
    assert items[ids[0]]['versions'][0]['payload']['invoice_number']=='LIST-CORRECTED'
    assert items[ids[0]]['versions'][0]['version']==2 and len(items[ids[0]]['versions'])==1
    assert items[ids[0]]['job']['id']==last_job
    assert len(client.get('/api/v1/transactions/'+ids[0]).json()['versions'])==2
