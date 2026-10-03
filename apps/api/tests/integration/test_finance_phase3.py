from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import UUID,uuid4
import json,sys
from sqlalchemy import select,func,text
from sqlalchemy.exc import DBAPIError
import pytest
from app.core.config import ROOT
from app.core.identity import Identity
from app.core.serialization import utcnow
from app.db.models import ReferenceRecord,Transaction,TransactionVersion,ApprovalRecord,AuditEvent,Evaluation,Report
from app.db.finance_models import FinanceAllocation,AllocationEvent,BudgetEvent,DuplicateComparison,DuplicateResolution,ApprovalRequest,ApprovalAction
from app.services import finance,approvals,finance_ledger
from app.services.worker import run_once
from app.schemas.canonical import fixture_canonical
from test_vertical_slice import payload,headers,evaluate_case
sys.path.insert(0,str(ROOT/'scripts/seed'))
from phase3 import enable


def configured(environment):
    db,ctx,other,client,cfg=environment;enable(db,ctx)
    roles=ctx.roles|{'FINANCE_SUBMITTER','REFERENCE_ADMIN','DUPLICATE_REVIEWER','RECEIPT_ALLOCATOR','FINANCE_CONTROLLER','LEDGER_ADMIN'};ctx=replace(ctx,roles=roles)
    settings=client.app.state.settings
    settings.identities['test-reviewer']['roles']=list(roles)
    for token,actor,role in [('test-manager','51000000-0000-4000-8000-000000000003','MANAGER'),('test-head','51000000-0000-4000-8000-000000000004','DEPARTMENT_HEAD')]:
        settings.identities[token]={'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':actor,'roles':[role,'FINANCE_REVIEWER'],'label':'Synthetic '+role}
    return db,ctx,other,client,cfg


def create(client,p):
    r=client.post('/api/v1/transactions',json=p,headers=headers());assert r.status_code==201,r.text;return r.json()['id']


def approve(client,tid,version=1):
    r=client.post(f'/api/v1/transactions/{tid}/approval-requests',json={'expected_version':version,'reason':'Verify configured approval chain'},headers=headers());assert r.status_code==201,r.text
    request=r.json()
    for step in request['requirements']:
        token='test-manager' if step['role']=='MANAGER' else 'test-head'
        r=client.post('/api/v1/approval-requests/'+request['id']+'/actions',json={'expected_version':version,'sequence':step['sequence'],'action':'APPROVED','reason':'Authorized synthetic financial review'},headers=headers()|{'Authorization':'Bearer '+token});assert r.status_code==200,r.text
    return request


def drain(db,ctx):
    for _ in range(20):
        if not run_once(db,ctx):break


def report(client,tid):
    detail=client.get('/api/v1/transactions/'+tid).json();assert detail['processing_state']=='COMPLETED',detail
    r=client.get('/api/v1/evaluations/'+detail['latest_evaluation_id']);assert r.status_code==200,r.text;return r.json()


def trusted_source(db,ctx,p,name=None):
    from app.services.reference_imports import active_records
    with db.session(ctx) as s:
        source=active_records(s,ctx)[p['source_document_id']].payload if p['source_document_id'] else active_records(s,ctx)[p['items'][0]['source_document_id']].payload
        did=uuid4();new=dict(source);new['id']=str(did);new['facts']=dict(source['facts'])
        if p['branch']=='VENDOR_INVOICE':new['facts'].update(invoice_number=p['invoice_number'],total_amount=p['total_amount'],invoice_date=p['invoice_date'])
        else:new['facts'].update(receipt_total_amount=p['items'][0]['receipt_total_amount'],expense_date=p['expense_date'])
        s.add(ReferenceRecord(**ctx.scope(),id=did,version=1,kind='documents',label='Explicit synthetic Phase-3 source',payload=new));s.flush()
    if p['branch']=='VENDOR_INVOICE':p['source_document_id']=str(did)
    else:
        p['source_document_id']=str(did)
        for item in p['items']:item['source_document_id']=str(did)
    return p


def test_approval_api_current_version_authority_rejection_audit_and_pass(environment):
    db,ctx,other,client,cfg=configured(environment);tid=create(client,payload());r=evaluate_case(client,db,ctx,tid);assert r['decision']=='HOLD' and r['ruleset_version']=='rules-p3-v1'
    req=client.post(f'/api/v1/transactions/{tid}/approval-requests',json={'expected_version':1,'reason':'Request required approvals'},headers=headers()).json()
    body={'expected_version':1,'sequence':1,'action':'APPROVED','reason':'Attempt own approval'};r=client.post('/api/v1/approval-requests/'+req['id']+'/actions',json=body,headers=headers());assert r.status_code==403 and r.json()['error']['code']=='SELF_APPROVAL'
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(ApprovalAction).where(ApprovalAction.state=='REJECTED'))==1 and s.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.action=='APPROVAL_REJECTED'))==1
    assert client.post('/api/v1/approval-requests/'+req['id']+'/actions',json=body|{'actor_id':str(uuid4())},headers=headers()).status_code==422
    assert client.post('/api/v1/approval-requests/'+req['id']+'/actions',json=body|{'sequence':2},headers=headers()|{'Authorization':'Bearer test-head'}).status_code==403
    approve(client,tid);drain(db,ctx);r=report(client,tid);assert r['decision']=='PASS' and len(r['rules'])==28,r
    assert len(client.get('/api/v1/transactions/'+tid+'/matching-allocations').json()['items'])==3
    p=payload();p['invoice_number']='Changed material identity'
    result=client.post('/api/v1/transactions/'+tid+'/revisions',json={'expected_version':1,'reason':'Change material invoice facts','transaction':p},headers=headers());assert result.status_code==201
    assert client.post('/api/v1/approval-requests/'+req['id']+'/actions',json=body,headers=headers()).status_code==409
    assert client.get('/api/v1/transactions/'+tid+'/approval-requests').json()['items'][0]['stale']


@pytest.mark.parametrize('payment_type',['COMPANY_CARD','ADVANCE'])
def test_employee_shared_receipt_and_company_card_controls(environment,payment_type):
    db,ctx,other,client,cfg=configured(environment);p=payload('employee/shared_within');tid=create(client,p);approve(client,tid)
    item=client.get('/api/v1/transactions/'+tid).json()['versions'][-1]['payload']['items'][0]
    body={'expected_version':1,'document_id':item['source_document_id'],'item_id':item['id'],'amount':item['claimed_amount'],'quantity':'1','reason':'Authorized employee share of a fictional meal','evidence_ids':[tid]}
    r=client.post('/api/v1/transactions/'+tid+'/receipt-shares',json=body,headers=headers());assert r.status_code==201,r.text
    drain(db,ctx);r=report(client,tid);assert next(x for x in r['rules'] if x['rule_id']=='EXP-005')['status']=='PASS'
    assert r['decision']=='PASS',r
    p=payload('employee/clean_taxi');p=trusted_source(db,ctx,p);tid2=create(client,p);approve(client,tid2)
    with db.session(ctx) as s:
        rid=uuid4();s.add(ReferenceRecord(**ctx.scope(),id=rid,version=1,kind='company_payments',label='Confirmed synthetic independent payment',payload={'id':str(rid),'version':1,'employee_id':p['employee_id'],'document_id':p['items'][0]['source_document_id'],'amount':'2400','currency':'INR','status':'CONFIRMED','payment_type':payment_type}));s.flush()
    q=client.post('/api/v1/transactions/'+tid2+'/evaluate',json={'expected_version':1,'reason':'Verify confirmed company payment'},headers=headers());assert q.status_code==202
    drain(db,ctx);result=report(client,tid2);assert result['decision']=='HOLD' and next(x for x in result['rules'] if x['rule_id']=='EXP-006')['status']=='FAIL'


def test_duplicate_punctuation_resolution_and_version_binding(environment):
    db,ctx,other,client,cfg=configured(environment);p=payload();p['invoice_number']='P3-SERIES-001';p=trusted_source(db,ctx,p);tid=create(client,p);approve(client,tid);drain(db,ctx);assert report(client,tid)['decision']=='PASS'
    otherp=dict(p);otherp['invoice_number']='p3 series 001';otherp=trusted_source(db,ctx,otherp);second=create(client,otherp);approve(client,second);drain(db,ctx);r=report(client,second);assert r['decision']=='REVIEW',r
    rows=client.get('/api/v1/transactions/'+second+'/duplicate-candidates').json()['items'];candidate=next(r for r in rows if r['candidate_id']==tid);assert candidate['classification']=='POSSIBLE_DUPLICATE' and candidate['signals']['aggressive_key_same']
    body={'expected_version':1,'disposition':'DISTINCT','reason':'Two independently verified legitimate invoice series','evidence_ids':[second,tid]}
    r=client.post('/api/v1/duplicate-candidates/'+candidate['id']+'/resolutions',json=body,headers=headers());assert r.status_code==201,r.text
    drain(db,ctx);assert report(client,second)['decision']=='PASS'
    revised=client.post('/api/v1/transactions/'+tid+'/revisions',json={'expected_version':1,'reason':'Material candidate facts changed','transaction':p|{'invoice_number':'New invoice identity'}},headers=headers());assert revised.status_code==201
    assert client.post('/api/v1/duplicate-candidates/'+candidate['id']+'/resolutions',json=body,headers=headers()).status_code==409


def test_budget_ledger_consumption_reversal_and_immutability(environment):
    db,ctx,other,client,cfg=configured(environment);tid=create(client,payload());approve(client,tid);drain(db,ctx);r=report(client,tid);assert r['decision']=='PASS'
    allocations=client.get('/api/v1/transactions/'+tid+'/matching-allocations').json()['items'];budget=next(a for a in allocations if a['kind']=='BUDGET');assert Decimal(budget['amount'])==0
    before=client.get('/api/v1/budgets/'+budget['resource_id']+'/ledger').json()['balance']
    r=client.post('/api/v1/allocations/'+budget['id']+'/actions',json={'action':'CONSUMED','reason':'Record verified fictional settlement lifecycle'},headers=headers());assert r.status_code==200,r.text
    after=client.get('/api/v1/budgets/'+budget['resource_id']+'/ledger').json()['balance'];assert Decimal(after['available'])==Decimal(before['available']) and Decimal(after['consumed'])>Decimal(before['consumed'])
    assert client.post('/api/v1/allocations/'+budget['id']+'/actions',json={'action':'RELEASED','reason':'Invalid release of consumed amount'},headers=headers()).status_code==409
    with db.session(ctx) as s:
        with pytest.raises(DBAPIError):
            with s.begin_nested():s.execute(text('UPDATE budget_events SET amount=amount+1'))
    r=client.post('/api/v1/allocations/'+budget['id']+'/actions',json={'action':'REVERSED','reason':'Explicit verified reversal, not release'},headers=headers());assert r.status_code==200


@pytest.mark.parametrize('kind',['BUDGET','GRN','DUPLICATE'])
def test_phase3_real_concurrent_admission_and_idempotent_finalize(environment,kind):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from app.services.worker import claim
    db,ctx,other,client,cfg=configured(environment);ids=[]
    if kind=='BUDGET':
        p=payload('employee/clean_taxi')
        with db.session(ctx) as s:
            old=s.scalar(select(ReferenceRecord).where(ReferenceRecord.id==UUID(p['budget_id']),ReferenceRecord.version==1)).payload;bid=uuid4();budget=old|{'id':str(bid),'ledger':[{'id':str(uuid4()),'version':1,'entry_type':'ALLOCATION','amount':'100','currency':'INR'}]};s.add(ReferenceRecord(**ctx.scope(),id=bid,version=1,kind='budgets',label='Synthetic capacity 100',payload=budget));s.flush()
        for i in range(2):
            p=payload('employee/clean_taxi');p.update(budget_id=str(bid),claim_number=str(uuid4()),requested_amount='80');p['items'][0].update(claimed_amount='80',receipt_total_amount='80');p=trusted_source(db,ctx,p);tid=create(client,p);approve(client,tid);ids.append(tid)
    else:
        for i in range(2):
            p=payload();p['invoice_number']='CONCURRENT-IDENTICAL-P3' if kind=='DUPLICATE' else str(uuid4())
            if kind=='GRN':p.update(subtotal_amount='30000',tax_amount='5400',total_amount='35400');p['lines'][0].update(quantity='30',net_amount='30000',tax_amount='5400',gross_amount='35400')
            p=trusted_source(db,ctx,p);tid=create(client,p);approve(client,tid);ids.append(tid)
    # Drain only stale intermediate approval intents; retain the latest two leases.
    leases=[]
    for _ in range(20):
        leased=claim(db,ctx)
        if not leased:break
        jid,owner,actor=leased
        with db.session(ctx) as s:
            from app.db.models import Job
            job=finance.get(s,Job,ctx,jid);t=finance.get(s,Transaction,ctx,job.transaction_id)
            if job.generation==t.row_version:leases.append((jid,owner))
            else:finance.finalize(s,ctx,jid,owner)
    assert len(leases)==2
    barrier=Barrier(2)
    def finish(lease):
        barrier.wait()
        with db.session(ctx) as s:return finance.finalize(s,ctx,*lease)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(finish,leases))
    decisions=[report(client,tid)['decision'] for tid in ids]
    assert decisions.count('PASS')<=1,decisions
    if kind in ('BUDGET','GRN'):assert decisions.count('PASS')==1 and 'HOLD' in decisions,decisions
    with db.session(ctx) as s:
        active=finance_ledger.active(s,ctx)
        if kind=='BUDGET':assert sum((a.amount for a,state in active if a.kind=='BUDGET'),Decimal('0'))<=100
        if kind=='GRN':assert sum((a.quantity for a,state in active if a.kind=='GRN_LINE'),Decimal('0'))<=50
        before=s.scalar(select(func.count()).select_from(FinanceAllocation))
        for lease in leases:finance.finalize(s,ctx,*lease)
        assert s.scalar(select(func.count()).select_from(FinanceAllocation))==before


def test_phase3_every_evidence_resolves_and_pinned_replay_after_reference_change(environment):
    from app.db.models import EvaluationInput
    from app.rules.finance_phase3 import evaluate as replay
    from app.rules.engine import RuleContext
    from app.services.reference_imports import stage,validate,activate,active_records
    db,ctx,other,client,cfg=configured(environment);tid=create(client,payload());approve(client,tid);drain(db,ctx);r=report(client,tid);assert r['decision']=='PASS'
    for rule in r['rules']:
        for e in rule['evidence']:
            response=client.get('/api/v1/evidence/'+e['id']);assert response.status_code==200,response.text
            assert client.get('/api/v1/evidence/'+e['id'],headers={'Authorization':'Bearer test-second'}).status_code==404
    with db.session(ctx) as s:
        input=s.scalar(select(EvaluationInput).where(EvaluationInput.evaluation_id==UUID(r['evaluation_id'])));assert replay(RuleContext(input.encoded)).decision=='PASS'
        vendor=active_records(s,ctx)[payload()['vendor_id']];updated=dict(vendor.payload);updated.update(version=2,status='BLOCKED')
        batch=stage(s,ctx,{'source_system':'SYNTHETIC_PHASE3','source_version':'blocked-v2','reason':'Simulate current mandatory master restriction','records':[{'kind':'vendors','payload':updated}]},'test');bid=UUID(batch['id']);assert validate(s,ctx,bid,'test')['state']=='VALID';activate(s,ctx,bid,'Approved synthetic restriction','test')
        assert replay(RuleContext(input.encoded)).decision=='PASS'
    q=client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Recheck current mandatory restriction'},headers=headers());assert q.status_code==202;drain(db,ctx);assert report(client,tid)['decision']=='HOLD'


def test_phase3_audit_failure_rolls_back_ledger_and_decision(environment,monkeypatch):
    from app.services.worker import claim
    db,ctx,other,client,cfg=configured(environment);tid=create(client,payload());approve(client,tid)
    for _ in range(10):
        lease=claim(db,ctx)
        if not lease:pytest.fail('No latest job')
        with db.session(ctx) as s:
            from app.db.models import Job
            j=finance.get(s,Job,ctx,lease[0]);t=finance.get(s,Transaction,ctx,UUID(tid));latest=j.generation==t.row_version
            if not latest:finance.finalize(s,ctx,*lease[:2])
        if latest:break
    original=finance.audit
    def fail(*args,**kw):
        if args[2]=='EVALUATION_FINALIZED':raise RuntimeError('Simulated audit storage outage')
        return original(*args,**kw)
    monkeypatch.setattr(finance,'audit',fail)
    with pytest.raises(RuntimeError):
        with db.session(ctx) as s:finance.finalize(s,ctx,*lease[:2])
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(Evaluation))==0
        assert s.scalar(select(func.count()).select_from(FinanceAllocation))==0
        assert s.scalar(select(func.count()).select_from(BudgetEvent))==0
        assert not finance.get(s,Transaction,ctx,UUID(tid)).eligible


def test_waiver_is_explicit_nonwaivable_denied_and_original_result_retained(environment):
    db,ctx,other,client,cfg=configured(environment);tid=create(client,payload('employee/daily_meals'));approve(client,tid);drain(db,ctx);r=report(client,tid);assert r['decision']=='REVIEW'
    rule=next(x for x in r['rules'] if x['rule_id']=='EXP-003');body={'expected_version':1,'rule_id':'EXP-003','reason':'Controller-approved fictional exception with receipt evidence','expires_at':(utcnow()+timedelta(days=2)).isoformat(),'evidence_ids':[rule['evidence'][0]['id']]}
    assert client.post('/api/v1/transactions/'+tid+'/waivers',json=body|{'rule_id':'BUD-001'},headers=headers()).status_code==403
    response=client.post('/api/v1/transactions/'+tid+'/waivers',json=body,headers=headers());assert response.status_code==201,response.text
    drain(db,ctx);new=report(client,tid);assert new['decision']=='PASS' and next(x for x in new['rules'] if x['rule_id']=='EXP-003')['status']=='FAIL' and new['waiver_dispositions']
    assert client.get('/api/v1/evaluations/'+r['evaluation_id']).json()['decision']=='REVIEW'


@pytest.mark.parametrize('branch,name,source_type',[('vendor','vendor_native.pdf','VENDOR_INVOICE'),('employee','receipt_native.pdf','EMPLOYEE_RECEIPT')])
def test_phase3_actual_pdf_source_verification_approval_report(environment,branch,name,source_type):
    from test_document_finance import processed,commit_body
    db,ctx,other,client,cfg=configured(environment);doc=processed(environment,name,source_type);body=commit_body(doc,branch)
    r=client.post('/api/v1/documents/'+doc['id']+'/commit',json=body,headers=headers());assert r.status_code==201,r.text
    tid=r.json()['id'];approve(client,tid);drain(db,ctx);r=report(client,tid)
    assert r['decision']=='PASS' and r['extraction_mode']=='DOCUMENT_DERIVED' and r['ruleset_version']=='rules-p3-v1',r
    for rule in r['rules']:
        for e in rule['evidence']:
            response=client.get('/api/v1/evidence/'+e['id']);assert response.status_code==200,response.text
    assert any(e['reference']['document_id']==doc['id'] for rule in r['rules'] for e in rule['evidence'])


def test_authorized_service_acceptance_contract_ceiling_and_missing_acceptance(environment):
    from app.services.reference_imports import active_records,stage,validate,activate
    db,ctx,other,client,cfg=configured(environment);p=payload();cid=uuid4();lid=uuid4();sid=uuid4()
    with db.session(ctx) as s:
        records=active_records(s,ctx);base=records[p['po_id']].payload;actor=records['51000000-0000-4000-8000-000000000003'].payload
        employee=actor|{'version':2,'roles':actor['roles']+['SERVICE_ACCEPTER']}
        contract=base|{'id':str(cid),'version':1,'approved_ceiling_amount':'100000','non_po_authorized':True,'acceptance_required':True}
        line={'id':str(lid),'version':1,'contract_id':str(cid),'unit_price':'1000','uom':'EA','tolerance':{'operator':'MAX','price_absolute_amount':'0','price_relative_rate':'0'}}
        data={'source_system':'SYNTHETIC_PHASE3','source_version':'contract-v1','reason':'Approved fictional service route','records':[{'kind':'contracts','payload':contract},{'kind':'contract_lines','payload':line},{'kind':'employees','payload':employee}]};b=stage(s,ctx,data,'test');bid=UUID(b['id']);result=validate(s,ctx,bid,'test');assert result['state']=='VALID',result['validation'];activate(s,ctx,bid,'Authorized fictional services','test')
    p.update(po_id=None,contract_id=str(cid),invoice_number='CONTRACT-MILESTONE-P3');p['lines'][0].update(po_line_id=None,grn_line_id=None,contract_line_id=str(lid));p=trusted_source(db,ctx,p);tid=create(client,p);approve(client,tid);drain(db,ctx);r=report(client,tid);assert r['decision']=='HOLD' and next(x for x in r['rules'] if x['rule_id']=='GRN-001')['status']=='FAIL'
    with db.session(ctx) as s:
        acceptance={'id':str(sid),'version':1,'contract_id':str(cid),'contract_line_id':str(lid),'accepted_quantity':'20','accepted_amount':'23600','accepter_id':'51000000-0000-4000-8000-000000000003','accepted_date':'2026-09-25','status':'ACCEPTED'}
        data={'source_system':'SYNTHETIC_PHASE3','source_version':'acceptance-v1','reason':'Independent authorized service acceptance','records':[{'kind':'service_acceptances','payload':acceptance}]};b=stage(s,ctx,data,'test');bid=UUID(b['id']);result=validate(s,ctx,bid,'test');assert result['state']=='VALID',result['validation'];activate(s,ctx,bid,'Verified service milestone acceptance','test')
    p['lines'][0]['service_acceptance_id']=str(sid);response=client.post('/api/v1/transactions/'+tid+'/revisions',json={'expected_version':1,'reason':'Add authorized service acceptance','transaction':p},headers=headers());assert response.status_code==201
    approve(client,tid,2);drain(db,ctx);assert report(client,tid)['decision']=='PASS'


def test_valid_and_expired_approval_delegation_and_cross_employee_privacy(environment):
    from app.services.reference_imports import stage,validate,activate
    db,ctx,other,client,cfg=configured(environment);delegate='51000000-0000-4000-8000-000000000002'
    client.app.state.settings.identities['test-delegate']={'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':delegate,'roles':['MANAGER','FINANCE_REVIEWER'],'label':'Synthetic delegated manager'}
    with db.session(ctx) as s:
        record={'id':str(uuid4()),'version':1,'effective_from':'2026-01-01','effective_to':'2027-01-01','delegator_id':'51000000-0000-4000-8000-000000000003','delegate_id':delegate,'purpose':'APPROVE','roles':['MANAGER'],'ceiling_amount':'100000','currency':'INR','cost_center_id':payload()['cost_center_id']}
        data={'source_system':'SYNTHETIC_PHASE3','source_version':'delegation-v1','reason':'Explicit authority delegation','records':[{'kind':'delegations','payload':record}]};b=stage(s,ctx,data,'test');bid=UUID(b['id']);assert validate(s,ctx,bid,'test')['state']=='VALID';activate(s,ctx,bid,'Bounded delegated approval authority','test')
    tid=create(client,payload());req=client.post('/api/v1/transactions/'+tid+'/approval-requests',json={'expected_version':1,'reason':'Request delegated approval'},headers=headers()).json();body={'expected_version':1,'sequence':1,'action':'APPROVED','reason':'Exercise authorized delegated manager'}
    r=client.post('/api/v1/approval-requests/'+req['id']+'/actions',json=body,headers=headers()|{'Authorization':'Bearer test-delegate'});assert r.status_code==200,r.text
    assert r.json()['request']['status']['steps'][0]['delegation_id']==record['id']
    with db.session(ctx) as s:
        expired=record|{'version':2,'effective_from':'2025-01-01','effective_to':'2026-01-01'};b=stage(s,ctx,data|{'source_version':'expired-v2','records':[{'kind':'delegations','payload':expired}]},'test');bid=UUID(b['id']);assert validate(s,ctx,bid,'test')['state']=='VALID';activate(s,ctx,bid,'Expire configured delegation','test')
    tid2=create(client,payload()|{'invoice_number':'Different delegated request'});req=client.post('/api/v1/transactions/'+tid2+'/approval-requests',json={'expected_version':1,'reason':'Request after delegation expiry'},headers=headers()).json()
    assert client.post('/api/v1/approval-requests/'+req['id']+'/actions',json=body,headers=headers()|{'Authorization':'Bearer test-delegate'}).status_code==403
    client.app.state.settings.identities['test-employee']={'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':delegate,'roles':['EMPLOYEE'],'label':'Synthetic claimant'}
    assert client.get('/api/v1/transactions/'+tid,headers={'Authorization':'Bearer test-employee'}).status_code==404
    assert client.get('/api/v1/transactions/'+tid+'/duplicate-candidates',headers={'Authorization':'Bearer test-employee'}).status_code==404


def test_shared_receipt_exceeded_and_split_review_are_computed(environment):
    db,ctx,other,client,cfg=configured(environment)
    p=payload('employee/shared_within');tid=create(client,p);approve(client,tid);item=client.get('/api/v1/transactions/'+tid).json()['versions'][-1]['payload']['items'][0]
    body={'expected_version':1,'document_id':item['source_document_id'],'item_id':item['id'],'amount':'600','quantity':'1','reason':'Authorized first actual receipt share','evidence_ids':[tid]};assert client.post('/api/v1/transactions/'+tid+'/receipt-shares',json=body,headers=headers()).status_code==201
    drain(db,ctx);assert report(client,tid)['decision']=='PASS'
    secondp=payload('employee/shared_exceeded');secondp['claim_number']='Second allocated share';second=create(client,secondp);approve(client,second);item=client.get('/api/v1/transactions/'+second).json()['versions'][-1]['payload']['items'][0]
    body.update(document_id=item['source_document_id'],item_id=item['id'],amount=item['claimed_amount'],evidence_ids=[second]);assert client.post('/api/v1/transactions/'+second+'/receipt-shares',json=body,headers=headers()).status_code==201
    drain(db,ctx);r=report(client,second);assert r['decision']=='HOLD' and next(x for x in r['rules'] if x['rule_id']=='EXP-005')['status']=='FAIL'


def test_actual_image_candidates_across_employees_and_masked_peer_comparison(environment):
    from io import BytesIO
    from PIL import Image
    from PIL import ImageDraw
    def image(total='1200.00'):
        im=Image.new('RGB',(640,850),'white');d=ImageDraw.Draw(im);d.text((40,40),'FICTIONAL MERCHANT - SYNTHETIC BENCHMARK',fill='black');d.line((40,90,600,90),fill='black',width=3)
        for i,value in enumerate(['Receipt TEST-017','Meal for two','2026-09-25','Quantity 2','Total INR '+total]):d.text((50,130+i*80),value,fill='black',font_size=24)
        d.rectangle((40,530,600,600),outline='black',width=3);return im
    def encode(im,format='PNG',**kw):
        stream=BytesIO();im.save(stream,format=format,**kw);return stream.getvalue()
    from test_document_pipeline import drain as drain_docs
    db,ctx,other,client,cfg=configured(environment)
    def upload_image(raw,name):
        r=client.post('/api/v1/uploads',json={'filename':name,'mime':'image/jpeg','source_type':'EMPLOYEE_RECEIPT'},headers=headers());assert r.status_code==201,r.text;s=r.json();assert client.post(s['bytes_url'],content=raw).status_code==200
        assert client.post('/api/v1/uploads/'+s['id']+'/finalize',headers=headers()).status_code==202;drain_docs(environment);d=client.get('/api/v1/documents/'+s['document_id']).json();assert d['pages']
        return d['id']
    first_doc=upload_image(encode(image(),'JPEG',quality=95),'synthetic-original.jpg');second_doc=upload_image(encode(image().resize((320,425)),'JPEG',quality=55),'synthetic-compressed.jpg')
    ids=[]
    for i,did in enumerate([first_doc,second_doc]):
        p=payload('employee/clean_taxi');p.update(employee_id='51000000-0000-4000-8000-00000000000'+str(i+1),source_document_id=did,claim_number=str(uuid4()),merchant='FICTIONAL MERCHANT',receipt_number='TEST-017',requested_amount='1200');p['items'][0].update(source_document_id=did,claimed_amount='1200',receipt_total_amount='1200');tid=create(client,p);ids.append(tid)
        q=client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Search actual uploaded receipt candidates'},headers=headers());assert q.status_code==202;drain(db,ctx)
    rows=client.get('/api/v1/transactions/'+ids[1]+'/duplicate-candidates').json()['items'];r=next(r for r in rows if r['candidate_id']==ids[0]);assert r['signals']['phash']['distance']<=6
    actor='51000000-0000-4000-8000-000000000002';client.app.state.settings.identities['test-claimant']={'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':actor,'roles':['EMPLOYEE'],'label':'Synthetic own-claim reader'}
    response=client.get('/api/v1/transactions/'+ids[1]+'/duplicate-candidates',headers={'Authorization':'Bearer test-claimant'});assert response.status_code==200 and response.json()['detail_access']=='MASKED' and 'candidate_id' not in response.json()['items'][0]
    r=report(client,ids[1]);safe=client.get('/api/v1/evaluations/'+r['evaluation_id'],headers={'Authorization':'Bearer test-claimant'});assert safe.status_code==200 and 'candidate_facts' not in safe.text
    assert client.get('/api/v1/documents/'+first_doc,headers={'Authorization':'Bearer test-claimant'}).status_code==404
    # Same merchant template with a different purchase is never confirmed solely by pHash.
    third=upload_image(encode(image('2450.00'),'JPEG',quality=75),'synthetic-distinct-purchase.jpg');p=payload('employee/clean_taxi');p.update(source_document_id=third,claim_number=str(uuid4()),merchant='FICTIONAL MERCHANT',receipt_number='TEST-018',requested_amount='2450');p['items'][0].update(source_document_id=third,claimed_amount='2450',receipt_total_amount='2450');tid=create(client,p);q=client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Compare template with changed purchase facts'},headers=headers());assert q.status_code==202;drain(db,ctx);r=report(client,tid)
    assert next(rule for rule in r['rules'] if rule['rule_id']=='DUP-003')['status']=='PASS' and r['decision']!='PASS'


def stage_records(client,records):
    r=client.post('/api/v1/reference-imports',json={'source_system':'SYNTHETIC_TEST','source_version':'v1','records':records,'reason':'Explicit synthetic acceptance configuration'},headers=headers());assert r.status_code==201,r.text;bid=r.json()['id']
    r=client.post('/api/v1/reference-imports/'+bid+'/validate',headers=headers());assert r.status_code==200 and r.json()['state']=='VALID',r.text
    r=client.post('/api/v1/reference-imports/'+bid+'/activate',json={'reason':'Activate validated synthetic test facts'},headers=headers());assert r.status_code==200,r.text
    return bid


def test_real_split_trip_across_months_and_cancellation_release(environment):
    from app.services.reference_imports import active_records
    db,ctx,other,client,cfg=configured(environment);p=payload('employee/clean_taxi');p['merchant']='SYNTHETIC TRAVEL DESK';p['trip_reference']='P3-CROSS-MONTH'
    with db.session(ctx) as s:policy=dict(active_records(s,ctx)[p['expense_policy_id']].payload)
    policy.update(version=2,split_threshold_amount='2500',split_near_fraction='0.8',trip_limit='4500',monthly_limit='5000')
    stage_records(client,[{'kind':'expense_policies','payload':policy}])
    first=dict(p);first['claim_number']='P3 AUGUST';first['expense_date']='2026-08-31';first['submission_date']='2026-09-01';first['items']=[first['items'][0]|{'expense_date':'2026-08-31'}];first=trusted_source(db,ctx,first);one=create(client,first);approve(client,one);drain(db,ctx);assert report(client,one)['decision']=='PASS',report(client,one)
    second=dict(p);second['claim_number']='P3 SEPTEMBER';second['expense_date']='2026-09-01';second['items']=[second['items'][0]|{'expense_date':'2026-09-01'}];second=trusted_source(db,ctx,second);two=create(client,second);approve(client,two);drain(db,ctx);r=report(client,two);exp=next(x for x in r['rules'] if x['rule_id']=='EXP-002');assert 'trip_limit' in exp['observed']['failed']
    controls=r['finance_controls'];assert Decimal(controls['aggregates']['TRIP']['amount'])==4800 and Decimal(controls['aggregates']['MONTH']['amount'])==2400
    # Same-day near-limit pattern is a review finding, separate from trip limits.
    policy.update(version=3,trip_limit='9000',monthly_limit='9000')
    stage_records(client,[{'kind':'expense_policies','payload':policy}]);client.post('/api/v1/transactions/'+two+'/evaluate',json={'expected_version':1,'reason':'Apply increased fictional trip limit'},headers=headers());drain(db,ctx);assert report(client,two)['decision']=='PASS'
    third=dict(second);third['claim_number']='P3 POSSIBLE SPLIT';third=trusted_source(db,ctx,third);three=create(client,third);approve(client,three)
    client.post('/api/v1/transactions/'+three+'/evaluate',json={'expected_version':1,'reason':'Check active same-day split pattern'},headers=headers());drain(db,ctx);r=report(client,three);assert next(x for x in r['rules'] if x['rule_id']=='PAT-001')['decision_effect']=='REVIEW'
    allocations=client.get('/api/v1/transactions/'+one+'/matching-allocations').json()['items'];before=client.get('/api/v1/budgets/'+p['budget_id']+'/ledger').json()['balance']
    assert client.post('/api/v1/transactions/'+one+'/cancellations',json={'expected_version':1,'reason':'Cancel only unconsumed synthetic reservation'},headers=headers()).status_code==200
    after=client.get('/api/v1/budgets/'+p['budget_id']+'/ledger').json()['balance'];assert Decimal(after['available'])-Decimal(before['available'])==2400
    assert all(a['state']=='RELEASED' for a in client.get('/api/v1/transactions/'+one+'/matching-allocations').json()['items'])


def test_exact_duplicate_distinct_survives_lifecycle_and_policy_replay(environment):
    from app.db.models import EvaluationInput
    from app.rules.engine import RuleContext
    from app.rules.finance_phase3 import evaluate
    from app.services.reference_imports import active_records
    db,ctx,other,client,cfg=configured(environment);p=payload();p['invoice_number']='P3 EXACT REUSE';p=trusted_source(db,ctx,p);one=create(client,p);approve(client,one);drain(db,ctx);assert report(client,one)['decision']=='PASS'
    p2=trusted_source(db,ctx,dict(p));two=create(client,p2);approve(client,two);drain(db,ctx);assert report(client,two)['decision']=='HOLD'
    candidate=next(r for r in client.get('/api/v1/transactions/'+two+'/duplicate-candidates').json()['items'] if r['candidate_id']==one)
    body={'expected_version':1,'disposition':'DISTINCT','reason':'Verified legitimate number reuse; different actual sources','evidence_ids':[one,two]}
    assert client.post('/api/v1/duplicate-candidates/'+candidate['id']+'/resolutions',json=body,headers=headers()).status_code==201
    drain(db,ctx);old=report(client,two);assert old['decision']=='PASS',old
    with db.session(ctx) as s:
        original=s.scalar(select(EvaluationInput).where(EvaluationInput.evaluation_id==UUID(old['evaluation_id'])));retained=original.encoded
        policy=dict(active_records(s,ctx)[p['approval_policy_id']].payload)
    # A current source lifecycle changes comparison diagnostics without changing pinned transaction versions.
    allocation=client.get('/api/v1/transactions/'+one+'/matching-allocations').json()['items'][0]
    assert client.post('/api/v1/allocations/'+allocation['id']+'/actions',json={'action':'CONSUMED','reason':'Consume already admitted source obligation'},headers=headers()).status_code==200
    policy['version']=3;policy['authority_limits']['MANAGER']['ceiling_amount']='100'
    stage_records(client,[{'kind':'approval_policies','payload':policy}])
    client.post('/api/v1/transactions/'+two+'/evaluate',json={'expected_version':1,'reason':'Recheck changed authority policy'},headers=headers());drain(db,ctx);current=report(client,two);assert current['decision']=='HOLD' and next(x for x in current['rules'] if x['rule_id']=='APR-002')['status']=='FAIL'
    assert next(x for x in current['rules'] if x['rule_id']=='DUP-002')['status']=='PASS'
    assert evaluate(RuleContext(retained)).decision=='PASS'
    assert client.get('/api/v1/evaluations/'+old['evaluation_id']).json()['decision']=='PASS'


def test_declined_request_is_terminal_and_account_version_safe(environment):
    db,ctx,other,client,cfg=configured(environment);p=payload();tid=create(client,p)
    req=client.post('/api/v1/transactions/'+tid+'/approval-requests',json={'expected_version':1,'reason':'Independent required approval review'},headers=headers()).json()
    body={'expected_version':1,'sequence':1,'action':'DECLINED','reason':'Decline unsupported current facts'}
    assert client.post('/api/v1/approval-requests/'+req['id']+'/actions',json=body,headers=headers()|{'Authorization':'Bearer test-manager'}).status_code==200
    assert client.post('/api/v1/approval-requests/'+req['id']+'/actions',json=body|{'action':'APPROVED'},headers=headers()|{'Authorization':'Bearer test-manager'}).status_code==403
    drain(db,ctx);assert report(client,tid)['decision']=='HOLD'
    account={'id':str(uuid4()),'version':1,'vendor_id':p['vendor_id'],'equality_token':'SYNTHETIC_CHANGED_TOKEN','status':'APPROVED','effective_from':'2026-01-01','effective_to':'2027-01-01'}
    stage_records(client,[{'kind':'payment_accounts','payload':account}]);client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Check approved payment account version'},headers=headers());drain(db,ctx);r=report(client,tid)
    assert next(x for x in r['rules'] if x['rule_id']=='VEN-003')['decision_effect']=='HOLD'
    assert 'SYNTHETIC_CHANGED_TOKEN' not in json.dumps(r)


def test_computed_exception_changes_required_approval_roles(environment):
    from app.services.reference_imports import active_records
    db,ctx,other,client,cfg=configured(environment);p=payload('employee/daily_meals')
    with db.session(ctx) as s:policy=dict(active_records(s,ctx)[p['approval_policy_id']].payload)
    with db.session(ctx) as s:cfo=dict(active_records(s,ctx)['51000000-0000-4000-8000-000000000004'].payload)
    cfo.update(version=2,roles=cfo['roles']+['CFO'])
    policy.update(version=3,exception_roles={'EXP-003':['CFO']});stage_records(client,[{'kind':'approval_policies','payload':policy},{'kind':'employees','payload':cfo}])
    client.app.state.settings.identities['test-cfo']={'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':'51000000-0000-4000-8000-000000000004','roles':['CFO','FINANCE_REVIEWER'],'label':'Synthetic CFO'}
    tid=create(client,p);r=evaluate_case(client,db,ctx,tid);assert next(x for x in r['rules'] if x['rule_id']=='EXP-003')['status']=='FAIL'
    req=client.post('/api/v1/transactions/'+tid+'/approval-requests',json={'expected_version':1,'reason':'Request computed exception chain'},headers=headers());assert req.status_code==201,req.text;req=req.json();assert [s['role'] for s in req['requirements']]==['MANAGER','CFO']
    for sequence,token in [(1,'test-manager'),(2,'test-cfo')]:
        action=client.post('/api/v1/approval-requests/'+req['id']+'/actions',json={'expected_version':1,'sequence':sequence,'action':'APPROVED','reason':'Effective explicit exception authority'},headers=headers()|{'Authorization':'Bearer '+token});assert action.status_code==200,action.text
    drain(db,ctx);r=report(client,tid);assert next(x for x in r['rules'] if x['rule_id']=='APR-001')['status']=='PASS' and r['decision']=='REVIEW'
    # Completion of the exceptional approval chain leaves the original allowance finding intact.
    assert next(x for x in r['rules'] if x['rule_id']=='EXP-003')['status']=='FAIL'


def test_resident_worker_selects_finance_scope_and_preserves_job_actor(environment):
    from app.services.worker import worker_identities
    db,ctx,other,client,cfg=configured(environment);settings=client.app.state.settings
    settings.identities['last-restricted-employee']={'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':'51000000-0000-4000-8000-000000000002','roles':['EMPLOYEE'],'label':'Restricted final identity'}
    worker=worker_identities(settings)[(ctx.tenant_id,ctx.legal_entity_id)]
    assert 'FINANCE_REVIEWER' in worker.roles and worker.actor_id==ctx.actor_id
    tid=create(client,payload());client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Exercise the scoped resident worker'},headers=headers());drain(db,worker);r=report(client,tid);assert r['decision']=='HOLD' and r['ruleset_version']=='rules-p3-v1'


def test_worker_claim_and_concurrent_approval_mutation_share_lock_order(environment):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from app.services.worker import claim
    db,ctx,other,client,cfg=configured(environment);tid=create(client,payload());client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Concurrent claim and approval request'},headers=headers());barrier=Barrier(2)
    def lease():barrier.wait(timeout=10);return claim(db,ctx)
    def request():barrier.wait(timeout=10);return client.post('/api/v1/transactions/'+tid+'/approval-requests',json={'expected_version':1,'reason':'Concurrent durable approval request'},headers=headers())
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(lease);b=pool.submit(request);leased=a.result(timeout=15);response=b.result(timeout=15)
    assert leased and response.status_code==201,response.text
    with db.session(ctx) as s:assert finance.finalize(s,ctx,leased[0],leased[1])
    assert report(client,tid)['decision']=='HOLD'


def test_on_behalf_submission_and_verified_preapproval_expire_without_defaults(environment):
    from app.services.reference_imports import active_records
    db,ctx,other,client,cfg=configured(environment);p=payload('employee/clean_taxi');delegate='51000000-0000-4000-8000-000000000002';manager='51000000-0000-4000-8000-000000000003'
    client.app.state.settings.identities['test-on-behalf']={'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':delegate,'roles':['FINANCE_REVIEWER'],'label':'Synthetic delegated submitter'}
    with db.session(ctx) as s:
        refs=active_records(s,ctx);policy=refs[p['expense_policy_id']].payload|{'version':2,'preapproval_required':True};actor=refs[manager].payload;actor=actor|{'version':2,'roles':actor['roles']+['PREAPPROVER']}
    period={'effective_from':'2026-01-01','effective_to':'2026-09-26'}
    delegation=period|{'id':str(uuid4()),'version':1,'delegator_id':p['employee_id'],'delegate_id':delegate,'purpose':'SUBMIT','roles':['SUBMIT'],'ceiling_amount':'5000','currency':'INR','cost_center_id':p['cost_center_id']}
    preapproval=period|{'id':str(uuid4()),'version':1,'employee_id':p['employee_id'],'approver_id':manager,'currency':'INR','category':p['category'],'cost_center_id':p['cost_center_id'],'ceiling_amount':'5000','approved_date':'2026-09-24','status':'APPROVED'}
    stage_records(client,[{'kind':'expense_policies','payload':policy},{'kind':'employees','payload':actor},{'kind':'delegations','payload':delegation},{'kind':'preapprovals','payload':preapproval}])
    def submit(facts):
        facts=trusted_source(db,ctx,facts);r=client.post('/api/v1/transactions',json=facts,headers=headers()|{'Authorization':'Bearer test-on-behalf'});assert r.status_code==201,r.text
        tid=r.json()['id'];approve(client,tid);drain(db,ctx);return report(client,tid)
    r=submit(p);assert r['decision']=='PASS',r
    control=next(x for x in r['rules'] if x['rule_id']=='EXP-002');assert control['observed']['preapproval_id']==preapproval['id']
    for e in control['evidence']:assert client.get('/api/v1/evidence/'+e['id']).status_code==200
    p=payload('employee/clean_taxi');p.update(expense_date='2026-09-27',claim_number='Delegation and preapproval expired');p['items'][0]['expense_date']=p['expense_date']
    r=submit(p);assert r['decision']=='HOLD' and next(x for x in r['rules'] if x['rule_id']=='EMP-001')['status']=='FAIL'
    assert 'verified_preapproval' in next(x for x in r['rules'] if x['rule_id']=='EXP-002')['observed']['missing']


def test_stale_activated_source_prevents_pass_and_resolves_pinned_evidence(environment):
    db,ctx,other,client,cfg=configured(environment);tid=create(client,payload());approve(client,tid);drain(db,ctx);old=report(client,tid);assert old['decision']=='PASS'
    with db.session(ctx) as s:finance.enqueue(s,ctx,UUID(tid),1,'Explicit future freshness check','phase3-stale','stale-source-check',evaluated_at=utcnow()+timedelta(days=31))
    drain(db,ctx);new=report(client,tid);r=next(x for x in new['rules'] if x['rule_id']=='REF-001');assert new['decision']!='PASS' and r['status']=='UNKNOWN' and r['observed']['stale_reference_ids']
    for e in r['evidence']:assert client.get('/api/v1/evidence/'+e['id']).status_code==200
    assert client.get('/api/v1/evaluations/'+old['evaluation_id']).json()['decision']=='PASS'
