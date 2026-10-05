from copy import deepcopy
from dataclasses import replace
from uuid import UUID,uuid4
from sqlalchemy import select,func
from app.db.models import ReferenceRecord,AuditEvent
from app.db.finance_models import ReferenceBatch
from app.services.reference_imports import active_records,stage,validate,activate
from app.services.references import snapshot,pinned
from app.core.errors import DomainError
import pytest


@pytest.fixture
def capacity_measurement(environment,request):
    from capacity_probe import CapacityProbe
    with CapacityProbe(environment[0],request.node.callspec.params['kind']) as probe:
        yield probe


def policy_identity(ctx,client):
    p=replace(ctx,actor_id=uuid4(),roles=frozenset({'POLICY_ADMIN'}))
    client.app.state.settings.identities['policy-admin']={**{k:str(v) for k,v in p.scope().items()},'actor_id':str(p.actor_id),'roles':list(p.roles),'label':'Synthetic policy administrator'}
    return p,{'Authorization':'Bearer policy-admin','Idempotency-Key':str(uuid4())}


def test_business_policy_future_version_preserves_snapshot_and_conflicts(environment):
    db,ctx,other,client,cfg=environment;policy,headers=policy_identity(ctx,client)
    with db.session(ctx) as s:
        hotel=next(r for r in active_records(s,ctx).values() if r.kind=='expense_policies' and r.payload['category']=='HOTEL')
        old=snapshot(s,ctx);old_value=deepcopy(pinned(s,ctx,old.id));assert hotel.payload['allowance_amount']=='8000.00'
    body={'expected_version':hotel.version,'allowance_amount':'9000.00','effective_from':'2026-11-01','reason':'Future synthetic hotel allowance approved'}
    assert client.post(f'/api/v1/admin/records/{hotel.id}/drafts',json=body,headers={'Idempotency-Key':str(uuid4())}).status_code==403
    response=client.post(f'/api/v1/admin/records/{hotel.id}/drafts',json=body,headers=headers);assert response.status_code==201,response.text
    draft=response.json();assert draft['state']=='VALID',draft
    with db.session(ctx) as s:assert active_records(s,ctx)[str(hotel.id)].version==1
    result=client.post('/api/v1/admin/drafts/'+draft['id']+'/activate',json={'reason':body['reason']},headers={**headers,'Idempotency-Key':str(uuid4())});assert result.status_code==200,result.text
    with db.session(ctx) as s:
        assert active_records(s,ctx,'2026-10-31')[str(hotel.id)].payload['allowance_amount']=='8000.00'
        assert active_records(s,ctx,'2026-11-01')[str(hotel.id)].payload['allowance_amount']=='9000.00'
        assert pinned(s,ctx,old.id)==old_value
        assert s.scalar(select(func.count()).select_from(ReferenceRecord).where(ReferenceRecord.id==hotel.id))==2
        audit=s.scalar(select(AuditEvent).where(AuditEvent.object_id==UUID(draft['id']),AuditEvent.action=='REFERENCE_ACTIVATED'))
        assert audit.actor_id==policy.actor_id and audit.reason==body['reason']
    stale=client.post(f'/api/v1/admin/records/{hotel.id}/drafts',json=body,headers={**headers,'Idempotency-Key':str(uuid4())});assert stale.status_code==409
    foreign=client.get(f'/api/v1/admin/records/{hotel.id}/versions',headers={'Authorization':'Bearer test-second'});assert foreign.status_code==404


def test_policy_admin_cannot_activate_master_or_financial_inputs(environment):
    db,ctx,other,client,cfg=environment;policy,headers=policy_identity(ctx,client);master=replace(ctx,roles=frozenset({'REFERENCE_ADMIN'}))
    with db.session(ctx) as s:
        vendor=next(r for r in active_records(s,ctx).values() if r.kind=='vendors');p=deepcopy(vendor.payload);p['version']=2
    assert client.post(f'/api/v1/admin/records/{vendor.id}/drafts',json={'expected_version':1,'legal_name':'Forged change','reason':'Policy role is insufficient'},headers=headers).status_code==403
    with db.session(master) as s:
        batch=stage(s,master,{'source_system':'BUSINESS_ADMIN','source_version':'v2','reason':'Approved master edit','records':[{'kind':'vendors','payload':p}]},'test');assert validate(s,master,UUID(batch['id']),'test')['state']=='VALID'
    response=client.post('/api/v1/admin/drafts/'+batch['id']+'/activate',json={'reason':'Attempt forbidden master activation'},headers={**headers,'Idempotency-Key':str(uuid4())});assert response.status_code==403
    assert client.post('/api/v1/reference-imports/'+batch['id']+'/activate',json={'reason':'Attempt unrestricted activation'},headers={**headers,'Idempotency-Key':str(uuid4())}).status_code==403
    catalog=client.get('/api/v1/admin/catalog',headers=headers).json();assert all(r['kind'] in ('expense_policies','approval_policies','delegations','waiver_policies') for r in catalog['items'])
    for extra in ({'actor_id':str(uuid4())},{'decision':'PASS'},{'allowance_amount':9000}):
        response=client.post(f'/api/v1/admin/records/{vendor.id}/drafts',json={'expected_version':1,'reason':'Reject forged form',**extra},headers={**headers,'Idempotency-Key':str(uuid4())});assert response.status_code==422


def test_business_draft_retry_and_audit_rollback(environment,monkeypatch):
    from app.services import finance
    db,ctx,other,client,cfg=environment;policy,headers=policy_identity(ctx,client)
    item=next(r for r in client.get('/api/v1/admin/catalog',headers=headers).json()['items'] if r['kind']=='expense_policies')
    path='/api/v1/admin/records/'+item['id']+'/drafts';body={'expected_version':1,'allowance_amount':'9000.00','reason':'Idempotent business form'}
    r=client.post(path,json=body,headers=headers);assert r.status_code==201,r.text;assert client.post(path,json=body,headers=headers).json()==r.json()
    with db.session(ctx) as s:count=s.scalar(select(func.count()).select_from(ReferenceBatch))
    def broken(*args,**kwargs):raise DomainError(503,'AUDIT_UNAVAILABLE','Audit persistence unavailable.')
    monkeypatch.setattr(finance,'audit',broken)
    result=client.post(path,json=body,headers={**headers,'Idempotency-Key':str(uuid4())});assert result.status_code==503
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(ReferenceBatch))==count
    client.app.state.settings.identities['policy-admin']['roles']=['FINANCE_REVIEWER']
    assert client.post(path,json=body,headers=headers).status_code==403

@pytest.mark.parametrize('kind',['BUDGET','GRN','DUPLICATE','RECEIPT'])
def test_eight_concurrent_finalizations_keep_capacity_and_retry_invariants(environment,kind,capacity_measurement):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from decimal import Decimal
    from test_finance_phase3 import configured,payload,trusted_source,create,approve,report
    from app.services import finance,finance_ledger
    from app.services.worker import claim
    from app.db.models import Job,Transaction
    from app.db.finance_models import FinanceAllocation
    db,ctx,other,client,cfg=configured(environment);ids=[]
    shared=None
    if kind=='RECEIPT':
        shared=payload('employee/shared_within');shared['items'][0]['receipt_total_amount']='1000.00'
        shared=trusted_source(db,ctx,shared)
    if kind=='BUDGET':
        p=payload('employee/clean_taxi')
        with db.session(ctx) as s:
            old=active_records(s,ctx)[p['budget_id']].payload;bid=uuid4();budget=old|{'id':str(bid),'ledger':[{'id':str(uuid4()),'version':1,'entry_type':'ALLOCATION','amount':'100','currency':'INR'}]}
            s.add(ReferenceRecord(**ctx.scope(),id=bid,version=1,kind='budgets',label='Synthetic stress capacity 100',payload=budget))
    for n in range(8):
        p=deepcopy(shared) if kind=='RECEIPT' else payload('employee/clean_taxi' if kind=='BUDGET' else 'vendor/clean')
        if kind=='BUDGET':p.update(budget_id=str(bid),claim_number=str(uuid4()),requested_amount='80');p['items'][0].update(claimed_amount='80',receipt_total_amount='80')
        elif kind=='RECEIPT':
            with db.session(ctx) as s:
                employee=deepcopy(active_records(s,ctx)[p['employee_id']].payload);eid=uuid4();employee.update(id=str(eid),name=f'Synthetic concurrent claimant {n}')
                s.add(ReferenceRecord(**ctx.scope(),id=eid,version=1,kind='employees',label=employee['name'],payload=employee))
            p['employee_id']=str(eid)
            p.update(claim_number=str(uuid4()),requested_amount='200.00');p['items'][0].update(claimed_amount='200.00',id=str(uuid4()))
        else:
            p['invoice_number']='SYNTHETIC-P6-REPEATED' if kind=='DUPLICATE' else str(uuid4())
            if kind=='GRN':p.update(subtotal_amount='30000',tax_amount='5400',total_amount='35400');p['lines'][0].update(quantity='30',net_amount='30000',tax_amount='5400',gross_amount='35400')
        if kind!='RECEIPT':p=trusted_source(db,ctx,p)
        tid=create(client,p);approve(client,tid);ids.append(tid)
        if kind=='RECEIPT':
            item=client.get('/api/v1/transactions/'+tid).json()['versions'][-1]['payload']['items'][0]
            from test_vertical_slice import headers
            body={'expected_version':1,'document_id':item['source_document_id'],'item_id':item['id'],'amount':'200.00','quantity':'1','reason':'Explicit synthetic concurrent receipt allocation','evidence_ids':[tid]}
            response=client.post('/api/v1/transactions/'+tid+'/receipt-shares',json=body,headers=headers());assert response.status_code==201,response.text
    leases=[]
    for _ in range(100):
        lease=claim(db,ctx)
        if not lease:break
        jid,owner,actor=lease
        with db.session(ctx) as s:
            job=finance.get(s,Job,ctx,jid);t=finance.get(s,Transaction,ctx,job.transaction_id)
            if job.generation==t.row_version:leases.append((jid,owner))
            else:finance.finalize(s,ctx,jid,owner)
    assert len(leases)==8
    barrier=Barrier(8)
    def finish(lease):
        barrier.wait()
        with capacity_measurement.sample():
            with db.session(ctx) as s:return finance.finalize(s,ctx,*lease)
    with ThreadPoolExecutor(8) as pool:list(pool.map(finish,leases))
    if kind=='RECEIPT':
        from app.db.finance_models import DuplicateComparison
        from app.services.finance_controls import resolve_duplicate
        # Shared-source candidates need an explicit disposition before capacity admission.
        with db.session(ctx) as s:
            pairs=s.scalars(select(DuplicateComparison).where(DuplicateComparison.transaction_id.in_([UUID(tid) for tid in ids]))).all()
            for pair in pairs:
                resolve_duplicate(s,ctx,pair.id,{'expected_version':1,'disposition':'SHARED_RECEIPT_ALLOCATION','reason':'Inspected common synthetic receipt and distinct authorized claimants','evidence_ids':[str(pair.transaction_id),str(pair.candidate_id)]},'release-receipt-stress')
        leases=[]
        for _ in range(150):
            lease=claim(db,ctx)
            if not lease:break
            jid,owner,actor=lease
            with db.session(ctx) as s:
                job=finance.get(s,Job,ctx,jid);t=finance.get(s,Transaction,ctx,job.transaction_id)
                if job.generation==t.row_version:leases.append((jid,owner))
                else:finance.finalize(s,ctx,jid,owner)
        assert len(leases)==8
        barrier=Barrier(8)
        capacity_measurement.round=2
        with ThreadPoolExecutor(8) as pool:list(pool.map(finish,leases))
    decisions=[report(client,tid)['decision'] for tid in ids]
    if kind!='RECEIPT':assert decisions.count('PASS')<=1,decisions
    if kind in ('BUDGET','GRN'):assert decisions.count('PASS')==1 and decisions.count('HOLD')==7,decisions
    with db.session(ctx) as s:
        allocations=finance_ledger.active(s,ctx)
        if kind=='BUDGET':assert sum((a.amount for a,state in allocations if a.kind=='BUDGET'),Decimal(0))<=100
        if kind=='GRN':assert sum((a.quantity for a,state in allocations if a.kind=='GRN_LINE'),Decimal(0))<=50
        if kind=='RECEIPT':
            used=sum((a.amount for a,state in allocations if a.kind=='RECEIPT'),Decimal(0));assert used<=1000
            assert used==1000 and decisions.count('PASS')==5 and decisions.count('HOLD')==3,decisions
        before=s.scalar(select(func.count()).select_from(FinanceAllocation))
        for lease in leases:finance.finalize(s,ctx,*lease)
        assert s.scalar(select(func.count()).select_from(FinanceAllocation))==before


def test_policy_workspace_denied_and_safe_structured_telemetry(environment,monkeypatch):
    import json
    from app.core import observability
    db,ctx,other,client,cfg=environment;policy,headers=policy_identity(ctx,client)
    events=[];monkeypatch.setattr(observability.log,'info',events.append)
    for path in ('overview','transactions','documents','reviews/'+str(uuid4())):
        assert client.get('/api/v1/'+path,headers=headers).status_code==403
    assert client.post('/api/v1/uploads',json={},headers=headers).status_code==403
    assert client.get('/api/v1/operations/dependencies').status_code==403
    response=client.get('/api/v1/transactions?private_query=DO_NOT_LOG_THIS');assert response.status_code==200
    assert response.headers['X-Content-Type-Options']=='nosniff' and 'no-store' in response.headers['Cache-Control']
    assert all('DO_NOT_LOG_THIS' not in e and 'policy-admin' not in e for e in events)
    assert json.loads(events[-1])['route']=='/api/v1/transactions'
    assert set(json.loads(events[-1]))=={'event','method','route','status','duration_ms','correlation_id'}


def test_enterprise_submission_roles_use_enabled_server_membership(environment,monkeypatch):
    from test_finance_phase3 import configured,payload,trusted_source,approve,drain,report
    from test_vertical_slice import evaluate_case,headers
    from app.integrations.storage import LocalStorage
    from app.integrations import blob_storage
    from app.db.models import Report
    db,ctx,other,client,cfg=configured(environment);p=trusted_source(db,ctx,payload('employee/clean_taxi')|{'claim_number':'SYNTHETIC-ENTERPRISE-MEMBERSHIP'})
    ctx=replace(ctx,actor_id=uuid4())
    client.app.state.settings.identities['enterprise-submitter']={**{k:str(v) for k,v in ctx.scope().items()},'actor_id':str(ctx.actor_id),'roles':list(ctx.roles),'label':'Synthetic on-behalf finance submitter'}
    response=client.post('/api/v1/transactions',json=p,headers=headers()|{'Authorization':'Bearer enterprise-submitter'})
    assert response.status_code==201,response.text
    tid=response.json()['id'];approve(client,tid)
    membership={**{k:str(v) for k,v in ctx.scope().items()},'actor_id':str(ctx.actor_id),'roles':list(ctx.roles),'enabled':True}
    # Mock external storage only; use actual PostgreSQL admission/rules/audit and RLS role guard.
    monkeypatch.setattr(blob_storage,'configured_storage',lambda settings:LocalStorage(client.app.state.settings.storage_root))
    db.settings=replace(client.app.state.settings,development=False,identities={},enterprise_identity={'memberships':{str(uuid4()):membership}})
    drain(db,ctx);first=report(client,tid);assert first['decision']=='PASS',first
    assert first['finance_controls']['finance_submission_authorized'] is True
    assert next(rule for rule in first['rules'] if rule['rule_id']=='EMP-001')['observed']['on_behalf'] is True
    with db.session(ctx) as s:before=deepcopy(s.scalar(select(Report).where(Report.evaluation_id==UUID(first['evaluation_id']))).content)
    membership['enabled']=False
    second=evaluate_case(client,db,ctx,tid);assert second['decision']=='HOLD'
    assert second['finance_controls']['finance_submission_authorized'] is False
    assert next(rule for rule in second['rules'] if rule['rule_id']=='EMP-001')['status']=='FAIL'
    with db.session(ctx) as s:assert s.scalar(select(Report).where(Report.evaluation_id==UUID(first['evaluation_id']))).content==before
