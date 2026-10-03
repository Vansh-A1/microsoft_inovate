"""Versioned ownership of the existing review projection. No decision override."""
from uuid import UUID
from sqlalchemy import select
from app.core.errors import DomainError
from app.core.serialization import projection, utcnow
from app.db.models import ReviewCase, Transaction, TransactionVersion, Evaluation, EvidenceObject
from app.db.workflow_models import ReviewAction
from app.db.session import scope_query
from app.services import finance

ACTIVE = ('OPEN','ASSIGNED','AWAITING_INFORMATION')

def require(identity, role='FINANCE_REVIEWER'):
    if role not in identity.roles:raise DomainError(403,'FORBIDDEN',role.replace('_',' ').title()+' permission is required.')

def view(session, identity, row):
    transaction=finance.get(session,Transaction,identity,row.transaction_id)
    evaluated=finance.get(session,Evaluation,identity,row.evaluation_id)
    return projection({'id':row.id,'transaction_id':row.transaction_id,'evaluation_id':row.evaluation_id,
        'transaction_version':evaluated.transaction_version,'current_transaction_version':transaction.latest_version,
        'review_version':row.row_version,'owner_id':row.owner_id,'state':row.state,'decision':row.decision,
        'branch':row.branch,'reasons':row.reasons,'created_at':row.created_at,'updated_at':row.updated_at,
        'permitted_actions':(['RELEASE','REQUEST_INFORMATION','CORRECT_FIELD','CANCEL_TRANSACTION','MARK_DUPLICATE','MARK_DISTINCT','SHARED_RECEIPT_RESOLUTION','PROPOSE_WAIVER'] if row.owner_id==identity.actor_id and row.state in ACTIVE else ['RESOLVE_EXCEPTION'] if row.owner_id==identity.actor_id and row.state=='SUPERSEDED' and transaction.eligible else ['CLAIM'] if row.owner_id is None and row.state in ACTIVE else []) if 'FINANCE_REVIEWER' in identity.roles else []})

def guard(session,identity,review_id,data):
    require(identity);finance.scope_lock(session,identity)
    row=finance.get(session,ReviewCase,identity,review_id);transaction=finance.get(session,Transaction,identity,row.transaction_id)
    if row.row_version!=data['expected_review_version'] or transaction.latest_version!=data['expected_transaction_version']:
        raise DomainError(409,'STALE_REVIEW_VERSION','This case changed after you opened it. Refresh before submitting.',details={'current_review_version':row.row_version,'current_transaction_version':transaction.latest_version,'state':row.state,'owner_id':str(row.owner_id) if row.owner_id else None})
    return row,transaction

def record(session,identity,row,transaction,action,data,correlation,details=None):
    row.row_version+=1;row.updated_at=utcnow()
    fact=ReviewAction(**identity.scope(),review_case_id=row.id,review_version=row.row_version,
        transaction_version=transaction.latest_version,actor_id=identity.actor_id,action=action,
        reason_code=data['reason_code'],comment=data['comment'],evidence=data.get('evidence_ids',[]),details=details or {})
    session.add(fact);session.flush()
    finance.audit(session,identity,'REVIEW_'+action,row.id,row.row_version,data['comment'],correlation,
        {'transaction_id':str(transaction.id),'transaction_version':transaction.latest_version,'reason_code':data['reason_code'],'action_id':str(fact.id),'owner_id':str(row.owner_id) if row.owner_id else None,'state':row.state})
    return view(session,identity,row)

def assign(session,identity,review_id,data,correlation):
    row,t=guard(session,identity,review_id,data)
    if row.state not in ACTIVE:raise DomainError(409,'REVIEW_CLOSED','This review is no longer open.')
    action=data['action']
    if action=='CLAIM':
        if row.owner_id is not None:raise DomainError(409,'CASE_ALREADY_ASSIGNED','Another reviewer owns this case.')
        row.owner_id=identity.actor_id;row.state='ASSIGNED'
    elif action=='RELEASE':
        if row.owner_id!=identity.actor_id:raise DomainError(403,'CASE_NOT_OWNED','Only the current owner can release this case.')
        row.owner_id=None;row.state='OPEN'
    else:
        require(identity,'REVIEW_MANAGER')
        target=UUID(data['owner_id'])
        # Targets are trusted configured identities in this exact scope; UUID knowledge is not authority.
        settings=session.info.get('settings')
        if not settings or not any(r['actor_id']==str(target) and r['tenant_id']==str(identity.tenant_id) and r['legal_entity_id']==str(identity.legal_entity_id) and 'FINANCE_REVIEWER' in r['roles'] for r in settings.identities.values()):
            raise DomainError(422,'ASSIGNEE_UNAVAILABLE','Choose an authorized reviewer in this entity.')
        row.owner_id=target;row.state='ASSIGNED'
    return record(session,identity,row,t,action,data,correlation)

def act(session,identity,review_id,data,correlation):
    row,t=guard(session,identity,review_id,data)
    if row.owner_id!=identity.actor_id:raise DomainError(403,'CASE_NOT_OWNED','Claim this case before recording a review action.')
    session.info['review_authorized_transaction']=t.id
    action=data['action'];details={};result=None
    if row.state not in ACTIVE and not (action=='RESOLVE_EXCEPTION' and row.state=='SUPERSEDED'):
        raise DomainError(409,'REVIEW_CLOSED','This review is no longer open.')
    for eid in data.get('evidence_ids',[]):
        evidence=finance.get(session,EvidenceObject,identity,UUID(eid))
        if evidence.evaluation_id!=row.evaluation_id:raise DomainError(409,'REVIEW_EVIDENCE_STALE','Use evidence from this review evaluation.')
    if action=='REQUEST_INFORMATION':
        if not data.get('requested_input'):raise DomainError(422,'REQUEST_INPUT_REQUIRED','Describe the evidence or input required.')
        row.state='AWAITING_INFORMATION';details={'requested_input':data['requested_input']}
    elif action=='RESOLVE_EXCEPTION':
        from app.services.operations import eligibility
        if not eligibility(session,identity,t)['current_eligible']:raise DomainError(409,'CONTROLS_UNRESOLVED','Resolve required controls and obtain a fresh eligible evaluation before closing this review.')
        row.state='RESOLVED'
    elif action=='CANCEL_TRANSACTION':
        result=cancel(session,identity,t.id,t.latest_version,data['comment'],correlation);row.state='CANCELLED'
    elif action=='CORRECT_FIELD':
        if not data.get('evidence_ids'):raise DomainError(422,'CORRECTION_EVIDENCE_REQUIRED','Cite source evidence for the corrected facts.')
        if data.get('document_commit'):
            from app.services.document_facts import commit
            previous=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==t.id,TransactionVersion.version==t.latest_version))
            previous_payload=finance.redact(previous.payload)
            body=data['document_commit']|{'transaction_id':str(t.id),'expected_version':t.latest_version,'reason':data['comment']}
            result=commit(session,identity,UUID(data['document_id']),body,correlation)
            current=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==t.id,TransactionVersion.version==t.latest_version))
            details={'document_id':data['document_id'],'corrections':finance.redact(body['corrections']),'old_value':previous_payload,'new_value':finance.redact(current.payload)}
        else:
            if not data.get('transaction'):raise DomainError(422,'CORRECTION_REQUIRED','Supply corrected canonical facts.')
            old=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==t.id,TransactionVersion.version==t.latest_version))
            details={'old_value':finance.redact(old.payload),'new_value':finance.redact(data['transaction']),'source_evaluation_id':str(row.evaluation_id)}
            result=finance.revise(session,identity,t.id,{'expected_version':t.latest_version,'reason':data['comment'],'transaction':data['transaction']},correlation)
            result|=finance.enqueue(session,identity,t.id,t.latest_version,'Review correction requires fresh screening',correlation,'review-correction:'+str(row.id)+':'+str(row.row_version))
    elif action in ('MARK_DUPLICATE','MARK_DISTINCT','SHARED_RECEIPT_RESOLUTION'):
        from app.services.finance_controls import resolve_duplicate
        if not data.get('comparison_id') or not data.get('evidence_ids'):raise DomainError(422,'COMPARISON_REQUIRED','Select a comparison and cite source evidence.')
        from app.db.finance_models import DuplicateComparison
        comparison=finance.get(session,DuplicateComparison,identity,UUID(data['comparison_id']))
        if comparison.transaction_id!=t.id:raise DomainError(409,'COMPARISON_SCOPE','Comparison belongs to another case.')
        disposition={'MARK_DUPLICATE':'CONFIRMED_DUPLICATE','MARK_DISTINCT':'DISTINCT','SHARED_RECEIPT_RESOLUTION':'SHARED_RECEIPT_ALLOCATION'}[action]
        result=resolve_duplicate(session,identity,comparison.id,{'expected_version':t.latest_version,'disposition':disposition,'reason':data['comment'],'evidence_ids':[str(t.id)]},correlation)
        details={'comparison_id':str(comparison.id),'disposition':disposition}
    elif action=='PROPOSE_WAIVER':
        from app.services.approvals import waive
        if not data.get('rule_id') or not data.get('expires_at'):raise DomainError(422,'WAIVER_REQUIRED','Select a rule and expiry; configured waiver authority is required.')
        result=waive(session,identity,t.id,{'expected_version':t.latest_version,'reason':data['comment'],'rule_id':data['rule_id'],'expires_at':data['expires_at'],'evidence_ids':data.get('evidence_ids',[])},correlation)
        details={'waiver_id':result['id'],'rule_id':data['rule_id']}
    else:raise DomainError(422,'REVIEW_ACTION_INVALID','Select a supported review action.')
    return {'review':record(session,identity,row,t,action,data,correlation,details),'result':result}

def cancel(session,identity,transaction_id,expected,reason,correlation):
    require(identity);finance.scope_lock(session,identity);t=finance.get(session,Transaction,identity,transaction_id)
    if t.latest_version!=expected:raise DomainError(409,'STALE_VERSION','Refresh before cancellation.')
    if t.processing_state=='CANCELLED':return {'id':str(t.id),'version':t.latest_version,'state':'CANCELLED'}
    finance.review_guard(session,identity,t)
    from app.db.finance_models import FinanceAllocation
    from app.services import finance_ledger
    rows=session.scalars(scope_query(select(FinanceAllocation),FinanceAllocation,identity).where(FinanceAllocation.transaction_id==t.id)).all()
    if 'CONSUMED' in finance_ledger.states(session,identity,rows).values():raise DomainError(409,'CONSUMED_ALLOCATION','Settled capacity requires an explicit reversal before cancellation.')
    finance.release(session,identity,t.id);t.eligible=False;t.decision=None;t.processing_state='CANCELLED';t.row_version+=1
    from app.db.models import Job
    for job in session.scalars(scope_query(select(Job),Job,identity).where(Job.transaction_id==t.id,Job.state.in_(['QUEUED','RUNNING','RETRYABLE']))):job.state='CANCELLED';job.lease_until=None
    for case in session.scalars(scope_query(select(ReviewCase),ReviewCase,identity).where(ReviewCase.transaction_id==t.id,ReviewCase.state=='SUPERSEDED')):
        case.state='CANCELLED';case.row_version+=1;case.updated_at=utcnow()
    finance.audit(session,identity,'TRANSACTION_CANCELLED',t.id,t.latest_version,reason,correlation)
    return {'id':str(t.id),'version':t.latest_version,'state':'CANCELLED'}
