"""Actual PostgreSQL review conflicts, retained decisions and guarded recovery."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from threading import Barrier
from uuid import UUID,uuid4
from sqlalchemy import select,func,text
import pytest
from app.core.errors import DomainError
from app.core.serialization import utcnow
from app.core.identity import Identity
from app.db.models import ReviewCase,Transaction,Job,AuditEvent,Evaluation,OutboxEvent,Report
from app.db.workflow_models import ReviewAction,OperationRecord
from app.db.finance_models import AllocationEvent,BudgetEvent,FinanceAllocation
from app.db.session import scope_query
from app.services import finance,reviews,operations
from app.services.worker import claim,run_once
from app.integrations.storage import LocalStorage
from test_finance_phase3 import configured,create,approve,drain,report,trusted_source
from test_vertical_slice import payload,headers,evaluate_case


def operational(environment):
    db,ctx,other,client,cfg=configured(environment)
    roles=ctx.roles|{'OPERATIONS_ADMIN','REPORT_EXPORTER','REVIEW_MANAGER'}
    ctx=replace(ctx,roles=roles);client.app.state.settings.identities['test-reviewer']['roles']=list(roles)
    return db,ctx,other,client,cfg

def case(client,tid):return client.get('/api/v1/transactions/'+tid+'/review-history').json()['items'][0]
def body(r):return {'expected_review_version':r['review_version'],'expected_transaction_version':r['current_transaction_version'],'reason_code':'EVIDENCE_REVIEW','comment':'Verify retained source and required controls'}
def assign(client,r,action='CLAIM',**kw):return client.post('/api/v1/reviews/'+r['id']+'/assign',json=body(r)|{'action':action}|kw,headers=headers())


def test_exception_resolution_retains_original_decision_and_two_reviewer_conflict(environment):
    db,ctx,other,client,cfg=operational(environment);tid=create(client,payload());old=evaluate_case(client,db,ctx,tid);assert old['decision']=='HOLD'
    r=assign(client,case(client,tid)).json();assert r['owner_id']==str(ctx.actor_id)
    assert client.post('/api/v1/transactions/'+tid+'/revisions',json={'expected_version':1,'reason':'Try bypassing assigned ownership','transaction':payload()},headers=headers()|{'Authorization':'Bearer test-manager'}).status_code==403
    assert client.post('/api/v1/transactions/'+tid+'/revisions',json={'expected_version':1,'reason':'Missing optimistic review guard','transaction':payload()},headers=headers()).status_code==409
    assert client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Stale reviewer cannot replace screening'},headers=headers()|{'Authorization':'Bearer test-manager'}).status_code==403
    response=client.post('/api/v1/reviews/'+r['id']+'/actions',json=body(r)|{'action':'REQUEST_INFORMATION','requested_input':'Please provide the authorized approval chain.'},headers=headers());assert response.status_code==200,response.text
    assert response.json()['review']['state']=='AWAITING_INFORMATION'
    approve(client,tid);drain(db,ctx);new=report(client,tid);assert new['decision']=='PASS' and new['current_eligible'],new
    r=case(client,tid);assert r['review_version']==4 and r['state']=='SUPERSEDED'
    same=body(r)|{'action':'RESOLVE_EXCEPTION'};barrier=Barrier(2)
    second=Identity(ctx.tenant_id,ctx.legal_entity_id,UUID('51000000-0000-4000-8000-000000000003'),frozenset({'FINANCE_REVIEWER'}),'Reviewer B')
    # Both reviewers opened version 4. A commits first; B submits that same stale version.
    with db.session(ctx) as s:result=reviews.act(s,ctx,UUID(r['id']),same,'reviewer-a');assert result['review']['review_version']==5
    with pytest.raises(DomainError) as error:
        with db.session(second) as s:reviews.act(s,second,UUID(r['id']),same,'reviewer-b')
    assert error.value.status==409 and error.value.code=='STALE_REVIEW_VERSION'
    stale=client.post('/api/v1/reviews/'+r['id']+'/actions',json=same,headers=headers()|{'Authorization':'Bearer test-manager'});assert stale.status_code==409
    assert case(client,tid)['state']=='RESOLVED'
    assert client.get('/api/v1/evaluations/'+old['evaluation_id']).json()['decision']=='HOLD'
    assert client.get('/api/v1/evaluations/'+old['evaluation_id']).json()['evaluation_status']=='SUPERSEDED'
    timeline=client.get('/api/v1/transactions/'+tid+'/timeline?limit=100').json()['items']
    assert {'REVIEW_CLAIM','REVIEW_REQUEST_INFORMATION','REVIEW_RESOLVE_EXCEPTION','EVALUATION_SUPERSEDED','APPROVAL_APPROVED'} <= {e['action'] for e in timeline}


def test_simultaneous_claim_has_one_owner_and_stale_conflict(environment):
    db,ctx,other,client,cfg=operational(environment);tid=create(client,payload());evaluate_case(client,db,ctx,tid);r=case(client,tid);barrier=Barrier(2)
    second=replace(ctx,actor_id=uuid4());command=body(r)|{'action':'CLAIM'}
    def run(who):
        barrier.wait()
        try:
            with db.session(who) as s:return 200,reviews.assign(s,who,UUID(r['id']),command,'concurrent-claim')['owner_id']
        except DomainError as exc:return exc.status,None
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,[ctx,second]))
    assert sorted(r[0] for r in results)==[200,409]
    assert case(client,tid)['owner_id']==next(owner for code,owner in results if code==200)


def test_request_correction_new_version_stale_approval_and_cancel_exact_once(environment):
    db,ctx,other,client,cfg=operational(environment);p=payload();tid=create(client,p);old=evaluate_case(client,db,ctx,tid);r=assign(client,case(client,tid)).json()
    eid=old['rules'][0]['evidence'][0]['id'];changed=p|{'invoice_number':'CORRECTED-P4-001'}
    result=client.post('/api/v1/reviews/'+r['id']+'/actions',json=body(r)|{'action':'CORRECT_FIELD','transaction':changed,'evidence_ids':[eid]},headers=headers());assert result.status_code==200,result.text
    detail=client.get('/api/v1/transactions/'+tid).json();assert detail['version']==2 and not detail['eligible'] and len(detail['versions'])==2
    assert detail['versions'][0]['payload']['invoice_number']==p['invoice_number']
    drain(db,ctx);assert report(client,tid)['decision']!='PASS' # Source and approvals still require verification.
    with db.session(ctx) as s:
        change=s.scalar(select(ReviewAction).where(ReviewAction.action=='CORRECT_FIELD'));assert change.details['old_value']['invoice_number']!=change.details['new_value']['invoice_number']
    # A separately complete case actually reserves capacity; cancellation releases each resource once.
    tid2=create(client,trusted_source(db,ctx,payload()|{'invoice_number':'CANCEL-P4-001'}));approve(client,tid2);drain(db,ctx);passed=report(client,tid2);assert passed['decision']=='PASS'
    command={'expected_version':1,'reason':'Cancel the fictional obligation before settlement'}
    for _ in range(2):
        response=client.post('/api/v1/transactions/'+tid2+'/cancellations',json=command,headers=headers());assert response.status_code==200,response.text
    with db.session(ctx) as s:
        ids=select(FinanceAllocation.id).where(FinanceAllocation.transaction_id==UUID(tid2))
        assert s.scalar(select(func.count()).select_from(AllocationEvent).where(AllocationEvent.allocation_id.in_(ids),AllocationEvent.action=='RELEASED'))==3
        assert s.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.object_id==UUID(tid2),AuditEvent.action=='TRANSACTION_CANCELLED'))==1
    assert client.post('/api/v1/transactions/'+tid2+'/evaluate',json={'expected_version':1,'reason':'Attempt to revive cancelled obligation'},headers=headers()).status_code==409
    assert client.post('/api/v1/transactions/'+tid2+'/revisions',json={'expected_version':1,'reason':'Attempt to revive cancellation','transaction':p},headers=headers()).status_code==409
    historic=client.get('/api/v1/evaluations/'+passed['evaluation_id']).json();assert historic['decision']=='PASS' and historic['eligible'] and not historic['current_eligible'] and historic['evaluation_status']=='STALE'


def test_operational_authorization_scope_export_replay_and_formula_escape(environment):
    db,ctx,other,client,cfg=operational(environment);tid=create(client,payload());r=evaluate_case(client,db,ctx,tid);review=case(client,tid)
    for path in ['reviews/'+review['id'],'transactions/'+tid+'/timeline','transactions/'+tid+'/review-history']:
        assert client.get('/api/v1/'+path,headers={'Authorization':'Bearer test-second'}).status_code==404
    for path,command in [('reviews/'+review['id']+'/assign',body(review)|{'action':'CLAIM'}),('transactions/'+tid+'/cancellations',{'expected_version':1,'reason':'Unauthorized cancellation'}),('operations/reconcile',{'reason':'Unauthorized repair'} )]:
        assert client.post('/api/v1/'+path,json=command,headers=headers()|{'Authorization':'Bearer test-reader'}).status_code==403
    assert client.post('/api/v1/reviews/'+review['id']+'/assign',json=body(review)|{'action':'CLAIM','actor_id':str(uuid4())},headers=headers()).status_code==422
    client.app.state.settings.identities['test-noexport']={**client.app.state.settings.identities['test-reviewer'],'roles':['FINANCE_REVIEWER']}
    client.app.state.settings.identities['test-policy-only']={**client.app.state.settings.identities['test-reviewer'],'roles':['POLICY_ADMIN']}
    for path in ['reviews','audit','transactions/'+tid+'/review-history','transactions/'+tid+'/timeline']:
        assert client.get('/api/v1/'+path,headers={'Authorization':'Bearer test-policy-only'}).status_code==403
    assert client.get('/api/v1/reviews?minimum_amount=not-a-number').status_code==400
    assert client.get('/api/v1/reviews?minimum_amount=100&maximum_amount=50').status_code==400
    assert client.post('/api/v1/evaluations/'+r['evaluation_id']+'/exports',json={'format':'csv'},headers=headers()|{'Authorization':'Bearer test-noexport'}).status_code==403
    export=client.post('/api/v1/evaluations/'+r['evaluation_id']+'/exports',json={'format':'csv'},headers=headers());assert export.status_code==201,export.text
    assert client.get('/api/v1/exports/'+export.json()['id'],headers={'Authorization':'Bearer test-second'}).status_code in (403,404)
    downloaded=client.get('/api/v1/exports/'+export.json()['id']);assert downloaded.status_code==200 and 'no-store' in downloaded.headers['cache-control']
    replay=client.post('/api/v1/evaluations/'+r['evaluation_id']+'/replay',headers=headers());assert replay.status_code==200 and replay.json()['matches'],replay.text
    assert operations.csv_safe(' =SUM(A1)')=="' =SUM(A1)" and operations.csv_safe('@payload')=="'@payload" and operations.csv_safe('Invoice')=='Invoice'


def test_retry_classification_dead_letter_manual_retry_and_reconciliation_idempotency(environment,monkeypatch):
    db,ctx,other,client,cfg=operational(environment);tid=create(client,payload())
    response=client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Exercise retryable failure'},headers=headers());jid=UUID(response.json()['job_id'])
    import app.services.worker as worker
    original=worker.finalize
    monkeypatch.setattr(worker,'finalize',lambda *a:(_ for _ in ()).throw(TimeoutError('untrusted provider token must not persist')))
    for attempt in range(3):
        with db.session(ctx) as s:s.get(Job,jid).available_at=utcnow()-timedelta(seconds=1)
        assert run_once(db,ctx)
    failed=client.get('/api/v1/operations/jobs').json()['items'][0];assert failed['state']=='DEAD_LETTER' and failed['retryable'] and failed['attempts']==3 and failed['first_failure_at'] and 'token' not in str(failed)
    command={'expected_attempts':3,'reason':'Dependency recovered; retry bounded stage'}
    assert client.post('/api/v1/operations/jobs/finance/'+str(jid)+'/retry',json=command,headers=headers()|{'Authorization':'Bearer test-reader'}).status_code==403
    key=headers();res=client.post('/api/v1/operations/jobs/finance/'+str(jid)+'/retry',json=command,headers=key);assert res.status_code==200,res.text
    assert client.post('/api/v1/operations/jobs/finance/'+str(jid)+'/retry',json=command,headers=key).json()==res.json()
    monkeypatch.setattr(worker,'finalize',original);assert run_once(db,ctx)
    # Delayed local outbox notification can be repaired from the committed job result.
    with db.session(ctx) as s:
        event=s.scalar(select(OutboxEvent).where(OutboxEvent.job_id==jid));event.delivered_at=None
    def reconcile():return client.post('/api/v1/operations/reconcile',json={'reason':'Inspect safe operational recovery'},headers=headers())
    first=reconcile();assert first.status_code==200,first.text
    assert any(f['code']=='DELAYED_OUTBOX' and f['status']=='REPAIRED' for f in first.json()['findings'])
    second=reconcile();assert second.status_code==200 and not second.json()['findings']
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(Evaluation).where(Evaluation.transaction_id==UUID(tid)))==1
        assert s.scalar(select(func.count()).select_from(OperationRecord).where(OperationRecord.kind=='RECONCILIATION'))==1
    assert operations.classify_failure(ValueError('invalid'))[1] is False


def test_stale_worker_lease_reconciliation_and_atomic_audit_failure(environment,monkeypatch):
    db,ctx,other,client,cfg=operational(environment);tid=create(client,payload());client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Crash after lease acquisition'},headers=headers())
    jid,owner,actor=claim(db,ctx)
    with db.session(ctx) as s:s.get(Job,jid).lease_until=utcnow()-timedelta(seconds=1)
    storage=LocalStorage(client.app.state.settings.storage_root)
    with db.session(ctx) as s:first=operations.reconcile(s,ctx,storage,'Recover abandoned lease','lease-repair')
    assert first['findings'][0]['code']=='STALE_LEASE'
    with pytest.raises(DomainError):
        with db.session(ctx) as s:finance.finalize(s,ctx,jid,owner)
    with db.session(ctx) as s:s.get(Job,jid).available_at=utcnow()-timedelta(seconds=1)
    assert run_once(db,ctx);r=case(client,tid)
    original=finance.audit
    def failed(*args,**kwargs):raise RuntimeError('Simulated audit persistence failure')
    monkeypatch.setattr(finance,'audit',failed)
    with pytest.raises(RuntimeError):
        with db.session(ctx) as s:reviews.assign(s,ctx,UUID(r['id']),body(r)|{'action':'CLAIM'},'audit-failure')
    monkeypatch.setattr(finance,'audit',original)
    assert case(client,tid)['owner_id'] is None and case(client,tid)['review_version']==1
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(ReviewAction))==0


def test_replay_pass_hold_review_and_health_minimal(environment):
    from phase1 import seed
    db,ctx,other,client,cfg=environment
    for r in seed(db,ctx,['vendor/clean','vendor/paid_duplicate','employee/daily_meals']):
        response=client.post('/api/v1/evaluations/'+r['latest_evaluation_id']+'/replay',headers=headers());assert response.status_code==200 and response.json()['matches'],response.text
    assert client.get('/api/v1/health/live').json()=={'status':'alive'}
    assert client.get('/api/v1/health/ready').json()=={'status':'ready'}
    assert client.get('/api/v1/operations/dependencies').status_code==403
    client.app.state.settings.identities['test-reviewer']['roles'].append('OPERATIONS_READER')
    status=client.get('/api/v1/operations/dependencies').json();assert status['enterprise_runtime']=='DEFERRED_EXTERNAL_PREREQUISITE' and status['risk_model']=='NOT_CONFIGURED'


def test_actual_document_review_correction_reverification_fresh_approval_and_history(environment):
    from test_document_finance import processed,commit_body
    db,ctx,other,client,cfg=operational(environment);doc=processed(environment)
    created=client.post('/api/v1/documents/'+doc['id']+'/commit',json=commit_body(doc),headers=headers());assert created.status_code==201,created.text
    tid=created.json()['id'];drain(db,ctx);initial=report(client,tid)
    current=client.get('/api/v1/transactions/'+tid).json()['versions'][-1]['payload'];correct_number=current['invoice_number']
    revised=client.post('/api/v1/transactions/'+tid+'/revisions',json={'expected_version':1,'reason':'Fictional data entry transcription error','transaction':current|{'invoice_number':'TRANSCRIPTION-ERROR'}},headers=headers());assert revised.status_code==201
    evaluate_case(client,db,ctx,tid,2);r=assign(client,case(client,tid)).json()
    wrong=client.get('/api/v1/transactions/'+tid).json()['versions'][-1]['payload'];evaluation=report(client,tid)
    evidence=[e['id'] for rule in evaluation['rules'] for e in rule['evidence'] if e['reference'].get('document_id')==doc['id']][:1]
    command=body(r)|{'action':'CORRECT_FIELD','document_id':doc['id'],'evidence_ids':evidence,
        'document_commit':commit_body(doc,transaction=wrong,corrections=[{'field_path':'invoice_number','value':correct_number,'page':1,'reason':'Verified the actual printed source number'}])}
    corrected=client.post('/api/v1/reviews/'+r['id']+'/actions',json=command,headers=headers());assert corrected.status_code==200,corrected.text
    assert corrected.json()['result']['version']==3
    approve(client,tid,3);drain(db,ctx);final=report(client,tid);assert final['decision']=='PASS' and final['current_eligible'],final
    versions=client.get('/api/v1/transactions/'+tid).json()['versions'];assert len(versions)==3 and versions[1]['payload']['invoice_number']=='TRANSCRIPTION-ERROR' and versions[2]['payload']['invoice_number']==correct_number
    with db.session(ctx) as s:
        action=s.scalar(select(ReviewAction).where(ReviewAction.action=='CORRECT_FIELD'))
        assert action.details['old_value']['invoice_number']=='TRANSCRIPTION-ERROR' and action.details['new_value']['invoice_number']==correct_number
    assert client.get('/api/v1/evaluations/'+initial['evaluation_id']).json()['decision']=='HOLD'


def test_native_unknown_and_unsupported_credit_route_to_review_without_source_invention(environment):
    from test_document_finance import processed
    db,ctx,other,client,cfg=operational(environment);doc=processed(environment,'missing_total.pdf');assert doc['state']=='NEEDS_INPUT'
    tid=create(client,payload())
    attached=client.post('/api/v1/transactions/'+tid+'/attachments',json={'expected_version':1,'document_id':doc['id'],'role':'INVOICE','reason':'Attach actual unreadable critical source for review'},headers=headers());assert attached.status_code==201,attached.text
    approve(client,tid,2);drain(db,ctx);result=report(client,tid)
    assert result['decision']=='REVIEW' and not result['eligible'],result
    assert next(r for r in result['rules'] if r['rule_id']=='DOC-001')['status']=='UNKNOWN'
    # Unsupported credit semantics are recognized explicitly, with other prerequisites complete.
    p=payload();p['document_type']='CREDIT_NOTE';p['invoice_number']='P4-CREDIT-UNSUPPORTED';p=trusted_source(db,ctx,p)
    credit=create(client,p);approve(client,credit);drain(db,ctx);credit_result=report(client,credit)
    assert credit_result['decision']=='REVIEW' and next(r for r in credit_result['rules'] if r['rule_id']=='SYS-001')['status']=='UNKNOWN',credit_result


def test_unconfigured_enterprise_document_stage_has_real_degraded_state_no_empty_success(environment):
    from dataclasses import replace
    from app.documents.config import ProviderSettings
    from app.db.document_models import DocumentJob,ExtractionRun
    from test_document_intake import upload
    from test_document_pipeline import drain as document_drain
    db,ctx,other,client,cfg=operational(environment);up,_=upload(client,'receipt_scan.pdf');client.post('/api/v1/uploads/'+up['id']+'/finalize',headers=headers())
    # A configured remote boundary with absent preprovisioned runtime assets is an actual unavailable dependency.
    document_drain(environment,providers=ProviderSettings(endpoint='http://127.0.0.1:65530',model='DEFERRED_ENTERPRISE_MODEL'))
    doc=client.get('/api/v1/documents/'+up['document_id']).json();assert doc['state']=='DEPENDENCY_UNAVAILABLE' and doc['last_error']=='TOKENIZER_NOT_PROVISIONED',doc
    assert doc['last_successful_stage']=='PREPROCESS' and not doc['draft']
    with db.session(ctx) as s:
        run=s.scalar(select(ExtractionRun));job=s.scalar(select(DocumentJob).where(DocumentJob.stage=='EXTRACT'))
        assert run.status=='FAILED' and run.result=={} and job.state=='FAILED' and not job.failure_retryable
        assert s.scalar(select(func.count()).select_from(Transaction))==0
    jobs=client.get('/api/v1/operations/jobs').json()['items'];assert any(j['last_error']=='TOKENIZER_NOT_PROVISIONED' and j['state']=='DEAD_LETTER' for j in jobs)


def test_nonzero_budget_cancel_compensation_and_reconciliation_preserve_history(environment):
    from decimal import Decimal
    from app.db.models import ReferenceRecord
    db,ctx,other,client,cfg=operational(environment);p=payload('employee/clean_taxi')
    p['requested_amount']='100';p['items'][0].update(claimed_amount='100',receipt_total_amount='100');p=trusted_source(db,ctx,p)
    tid=create(client,p);before=client.get('/api/v1/budgets/'+p['budget_id']+'/ledger').json()['balance']
    approve(client,tid);drain(db,ctx);old=report(client,tid);assert old['decision']=='PASS'
    reserved=client.get('/api/v1/budgets/'+p['budget_id']+'/ledger').json()['balance'];assert Decimal(before['available'])-Decimal(reserved['available'])==100
    allocations=client.get('/api/v1/transactions/'+tid+'/matching-allocations').json()['items'];budget=next(a for a in allocations if a['kind']=='BUDGET');assert Decimal(budget['amount'])==100
    # Simulated interrupted legacy cancellation left committed reservations. Only this isolated test projection changes.
    with db.session(ctx) as s:t=s.get(Transaction,UUID(tid));t.processing_state='CANCELLED';t.eligible=False;t.decision=None
    for _ in range(2):
        result=client.post('/api/v1/operations/reconcile',json={'reason':'Repair interrupted fictional cancellation'},headers=headers());assert result.status_code==200,result.text
    restored=client.get('/api/v1/budgets/'+p['budget_id']+'/ledger').json()['balance'];assert Decimal(restored['available'])==Decimal(before['available'])
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(BudgetEvent).where(BudgetEvent.allocation_id==UUID(budget['id']),BudgetEvent.entry_type=='RELEASE'))==1
        assert s.scalar(select(func.count()).select_from(AllocationEvent).where(AllocationEvent.allocation_id==UUID(budget['id']),AllocationEvent.action=='RELEASED'))==1
        assert s.scalar(select(func.count()).select_from(OperationRecord).where(OperationRecord.kind=='RECONCILIATION'))==1
    historic=client.get('/api/v1/evaluations/'+old['evaluation_id']).json();assert historic['eligible'] and not historic['current_eligible']


def test_material_amount_change_requires_new_authority_chain_and_retains_old_approvals(environment):
    from app.db.models import ReferenceRecord
    db,ctx,other,client,cfg=operational(environment);p=payload();p.update(subtotal_amount='50000',tax_amount='0',total_amount='50000')
    p['lines'][0].update(quantity='50',net_amount='50000',tax_rate='0',tax_amount='0',gross_amount='50000');p=trusted_source(db,ctx,p)
    tid=create(client,p);request=approve(client,tid);assert [s['role'] for s in request['requirements']]==['MANAGER','DEPARTMENT_HEAD'];drain(db,ctx)
    old=report(client,tid);p=client.get('/api/v1/transactions/'+tid).json()['versions'][-1]['payload'];p.update(subtotal_amount='150000',total_amount='150000');p['lines'][0].update(quantity='150',net_amount='150000',gross_amount='150000')
    revision=client.post('/api/v1/transactions/'+tid+'/revisions',json={'expected_version':1,'reason':'Material verified obligation increased to 150000','transaction':p},headers=headers());assert revision.status_code==201,revision.text
    assert not client.get('/api/v1/transactions/'+tid).json()['eligible']
    requests=client.get('/api/v1/transactions/'+tid+'/approval-requests').json()['items'];assert requests[0]['stale'] and len(requests[0]['actions'])==2
    fresh=client.post('/api/v1/transactions/'+tid+'/approval-requests',json={'expected_version':2,'reason':'Generate current amount authority chain'},headers=headers());assert fresh.status_code==201,fresh.text
    assert [s['role'] for s in fresh.json()['requirements']]==['MANAGER','DIRECTOR']
    stale=client.post('/api/v1/approval-requests/'+request['id']+'/actions',json={'expected_version':1,'sequence':2,'action':'APPROVED','reason':'Old head authority cannot satisfy new facts'},headers=headers()|{'Authorization':'Bearer test-head'});assert stale.status_code==409
    new=evaluate_case(client,db,ctx,tid,2);assert new['decision']=='HOLD' and not new['eligible']
    assert next(r for r in new['rules'] if r['rule_id']=='APR-001')['status']=='FAIL'
    assert client.get('/api/v1/evaluations/'+old['evaluation_id']).json()['transaction_version']==1


def test_reconciler_restores_missing_projection_with_new_evaluation_and_preserves_orphans(environment):
    db,ctx,other,client,cfg=operational(environment);tid=create(client,payload());original=evaluate_case(client,db,ctx,tid)
    storage=client.app.state.storage if hasattr(client.app.state,'storage') else LocalStorage(client.app.state.settings.storage_root)
    key,_=storage.put(ctx,b'Fictional retained storage object without metadata');orphan=storage.path(ctx,key)
    with db.session(ctx) as s:t=s.get(Transaction,UUID(tid));t.latest_evaluation_id=None;t.processing_state='RECEIVED';t.eligible=False
    for _ in range(2):
        result=client.post('/api/v1/operations/reconcile',json={'reason':'Recover projection without restoring historical eligibility'},headers=headers());assert result.status_code==200,result.text
    assert orphan.is_file()
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(Job).where(Job.transaction_id==UUID(tid)))==2
        assert s.scalar(select(func.count()).select_from(OperationRecord).where(OperationRecord.kind=='RECONCILIATION'))==2
    drain(db,ctx);fresh=report(client,tid);assert fresh['evaluation_id']!=original['evaluation_id'] and fresh['decision']==original['decision']
    assert client.get('/api/v1/evaluations/'+original['evaluation_id']).json()['evaluation_status']=='SUPERSEDED'


def test_new_payment_evidence_invalidates_current_eligibility_and_blocks_ledger_consumption(environment):
    from app.db.models import ReferenceRecord
    from sqlalchemy.exc import DBAPIError
    db,ctx,other,client,cfg=operational(environment);p=trusted_source(db,ctx,payload('employee/clean_taxi'));tid=create(client,p)
    approve(client,tid);drain(db,ctx);old=report(client,tid);assert old['current_eligible']
    budget=next(a for a in client.get('/api/v1/transactions/'+tid+'/matching-allocations').json()['items'] if a['kind']=='BUDGET')
    with db.session(ctx) as s:
        rid=uuid4();s.add(ReferenceRecord(**ctx.scope(),id=rid,version=1,kind='company_payments',label='New independent fictional company-card evidence',payload={'id':str(rid),'version':1,'employee_id':p['employee_id'],'document_id':p['items'][0]['source_document_id'],'amount':p['requested_amount'],'currency':'INR','status':'CONFIRMED','payment_type':'COMPANY_CARD'}))
    current=client.get('/api/v1/transactions/'+tid).json();assert not current['eligible'] and current['eligibility']['eligibility_reason']=='REFERENCES_CHANGED'
    assert next(t for t in client.get('/api/v1/transactions').json()['items'] if t['id']==tid)['eligible'] is False
    consume=client.post('/api/v1/allocations/'+budget['id']+'/actions',json={'action':'CONSUMED','reason':'Stale PASS cannot admit new consumption'},headers=headers());assert consume.status_code==409 and consume.json()['error']['code']=='ELIGIBILITY_STALE'
    unchanged=client.get('/api/v1/evaluations/'+old['evaluation_id']).json();assert unchanged['eligible'] and not unchanged['current_eligible']
    # The two new fact tables enforce database immutability as well as application guards.
    client.post('/api/v1/evaluations/'+old['evaluation_id']+'/replay',headers=headers())
    hold=evaluate_case(client,db,ctx,tid);r=assign(client,case(client,tid)).json();assert hold['decision']=='HOLD'
    with db.session(ctx) as s:
        for table in ('review_actions','operation_records'):
            with pytest.raises(DBAPIError):
                with s.begin_nested():s.execute(text('UPDATE '+table+' SET actor_id=:actor'),{'actor':uuid4()})
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(AllocationEvent).where(AllocationEvent.action=='CONSUMED'))==0


def test_manual_retry_exhaustion_is_bounded_and_permanent_failures_remain_terminal(environment):
    db,ctx,other,client,cfg=operational(environment);tid=create(client,payload());queued=client.post('/api/v1/transactions/'+tid+'/evaluate',json={'expected_version':1,'reason':'Exercise manual recovery exhaustion'},headers=headers()).json();jid=UUID(queued['job_id'])
    for cycle in range(2):
        with db.session(ctx) as s:
            job=s.get(Job,jid);job.attempts=job.maximum_attempts;operations.mark_failure(job,'DEPENDENCY_TIMEOUT',True,utcnow());attempt=job.attempts
        response=client.post('/api/v1/operations/jobs/finance/'+str(jid)+'/retry',json={'expected_attempts':attempt,'reason':'Dependency retry cycle'},headers=headers());assert response.status_code==200,response.text
        assert response.json()['manual_retries']==cycle+1 and response.json()['maximum_attempts']==attempt+3
    with db.session(ctx) as s:
        job=s.get(Job,jid);job.attempts=job.maximum_attempts;operations.mark_failure(job,'DEPENDENCY_TIMEOUT',True,utcnow());attempt=job.attempts
    denied=client.post('/api/v1/operations/jobs/finance/'+str(jid)+'/retry',json={'expected_attempts':attempt,'reason':'Third cycle must remain bounded'},headers=headers());assert denied.status_code==409
    with db.session(ctx) as s:
        job=s.get(Job,jid);job.manual_retries=0;operations.mark_failure(job,'UNSUPPORTED_INPUT_SCHEMA',False,utcnow())
    permanent=client.post('/api/v1/operations/jobs/finance/'+str(jid)+'/retry',json={'expected_attempts':attempt,'reason':'Permanent failure cannot be retried'},headers=headers());assert permanent.status_code==409
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(OperationRecord).where(OperationRecord.kind=='JOB_MANUAL_RETRY'))==2


def test_transient_document_storage_failure_exhaustion_allows_bounded_recovery(environment,monkeypatch):
    from app.db.document_models import DocumentJob,DocumentPage
    from test_document_intake import upload
    from test_document_pipeline import drain as document_drain
    import app.services.document_worker as worker
    db,ctx,other,client,cfg=operational(environment);up,_=upload(client,'vendor_native.pdf');client.post('/api/v1/uploads/'+up['id']+'/finalize',headers=headers())
    storage=LocalStorage(client.app.state.settings.storage_root);original=worker.perform
    monkeypatch.setattr(worker,'perform',lambda *args:(_ for _ in ()).throw(TimeoutError('Private provider content must not persist')))
    for _ in range(3):
        with db.session(ctx) as s:job=s.scalar(select(DocumentJob));job.available_at=utcnow()-timedelta(seconds=1)
        assert worker.run_once(db,ctx,storage,client.app.state.settings)
    doc=client.get('/api/v1/documents/'+up['document_id']).json();assert doc['state']=='FAILED_FINAL' and doc['last_error']=='DEPENDENCY_TIMEOUT'
    job=next(j for j in client.get('/api/v1/operations/jobs').json()['items'] if j['document_id']==up['document_id']);assert job['retryable'] and job['attempts']==3
    retried=client.post('/api/v1/operations/jobs/document/'+job['id']+'/retry',json={'expected_attempts':3,'reason':'Temporary storage dependency recovered'},headers=headers());assert retried.status_code==200,retried.text
    monkeypatch.setattr(worker,'perform',original);document_drain(environment)
    ready=client.get('/api/v1/documents/'+up['document_id']).json();assert ready['state']=='READY',ready
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(DocumentPage))==1
        recovered=s.get(DocumentJob,UUID(job['id']));assert recovered.attempts==4 and recovered.manual_retries==1 and recovered.state=='SUCCEEDED'
