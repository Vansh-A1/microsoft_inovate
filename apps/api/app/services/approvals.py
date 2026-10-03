"""Server-authorized ordered approvals; immutable request/action and waiver facts."""
from datetime import timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy import select
from app.core.errors import DomainError
from app.core.serialization import utcnow,digest,projection
from app.db.models import Transaction,TransactionVersion,ApprovalRecord
from app.db.finance_models import ApprovalRequest,ApprovalAction,Waiver
from app.db.session import scope_query
from app.services.reference_imports import effective,select_policy,require,active_records
from app.services import finance
D=Decimal


def requirements(refs,p,day,exception_ids=()):
    policy,candidates=select_policy(refs,'approval_policies',p,day,refs.get(str(p.get('employee_id'))))
    amount=p.get('total_amount' if p['branch']=='VENDOR_INVOICE' else 'requested_amount')
    bands=[]
    if policy and amount is not None:
        amount=D(amount)
        bands=[b for b in policy['bands'] if (amount>D(b['lower_bound_amount']) or b['lower_inclusive'] and amount==D(b['lower_bound_amount'])) and (b['upper_bound_amount'] is None or amount<D(b['upper_bound_amount']))]
    roles=list(bands[0]['required_roles']) if len(bands)==1 else []
    if policy and roles:
        for rule_id in sorted(exception_ids):
            for role in policy.get('exception_roles',{}).get(rule_id,[]):
                if role not in roles:roles.append(role)
    return policy,[{'sequence':i,'role':role} for i,role in enumerate(roles,1)],candidates


def current_exceptions(session,identity,version):
    from app.db.models import Evaluation,RuleResultRow
    t=finance.get(session,Transaction,identity,version.transaction_id)
    current=session.scalar(scope_query(select(Evaluation),Evaluation,identity).where(Evaluation.id==t.latest_evaluation_id,Evaluation.transaction_version==version.version)) if t.latest_evaluation_id else None
    if not current:return []
    return session.scalars(scope_query(select(RuleResultRow.rule_id),RuleResultRow,identity).where(RuleResultRow.evaluation_id==current.id,RuleResultRow.status.in_(['FAIL','UNKNOWN','ERROR']),RuleResultRow.rule_id.not_in(['APR-001','APR-002']))).all()


def delegation(refs,delegator,delegate,p,day,purpose,role=None):
    amount=D(p.get('total_amount' if p['branch']=='VENDOR_INVOICE' else 'requested_amount') or '0')
    valid=[r for r in refs.values() if r.get('_kind')=='delegations' and r.get('delegator_id')==delegator and r.get('delegate_id')==delegate and r.get('purpose')==purpose and effective(r,day) and r.get('currency')==p.get('currency') and r.get('cost_center_id')==p.get('cost_center_id') and amount<=D(r['ceiling_amount']) and (not role or role in r.get('roles',[]))]
    return valid[0] if len(valid)==1 else None


def authority(refs,p,policy,role,actor_id,author_id,day,server_roles=None):
    actor=refs.get(actor_id);amount=p.get('total_amount' if p['branch']=='VENDOR_INVOICE' else 'requested_amount');claimant=p.get('employee_id');delegate=None;principal=actor
    if actor_id in (claimant,author_id):return False,None,'SELF_APPROVAL'
    if not actor or actor.get('_kind')!='employees' or actor.get('status')!='ACTIVE' or not effective(actor,day):return False,None,'ACTOR_NOT_ACTIVE'
    if server_roles is not None and role not in server_roles:return False,None,'AUTHENTICATED_ROLE_REQUIRED'
    if role not in actor.get('roles',[]):
        candidates=[r for r in refs.values() if r.get('_kind')=='delegations' and r.get('delegate_id')==actor_id and role in r.get('roles',[])]
        found=[]
        for r in candidates:
            proof=delegation(refs,r['delegator_id'],actor_id,p,day,'APPROVE',role)
            source=refs.get(r['delegator_id'])
            if proof and source and role in source.get('roles',[]) and effective(source,day) and source.get('status')=='ACTIVE':found.append((proof,source))
        if len(found)!=1:return False,None,'ROLE_OR_DELEGATION_REQUIRED'
        delegate,principal=found[0]
    if principal.get('cost_center_id')!=p.get('cost_center_id') or principal.get('department')!=policy.get('department'):return False,delegate,'AUTHORITY_SCOPE'
    if role=='MANAGER' and claimant and refs.get(claimant,{}).get('manager_id')!=principal['id']:return False,delegate,'CLAIMANT_MANAGER_REQUIRED'
    limits=principal.get('approval_authority',{}).get(role)
    # Existing synthetic masters predate explicit ceilings; policy may supply an approved role matrix.
    limits=limits or policy.get('authority_limits',{}).get(role)
    if not limits:return False,delegate,'AUTHORITY_CEILING_NOT_CONFIGURED'
    if limits.get('currency')!=p.get('currency') or amount is None or D(amount)>D(limits['ceiling_amount']):return False,delegate,'AUTHORITY_CEILING_OR_CURRENCY'
    return True,delegate,'AUTHORIZED'


def state(session,identity,version,refs,exception_ids=None):
    p=version.payload;day=p.get('invoice_date' if p['branch']=='VENDOR_INVOICE' else 'expense_date');policy,required,candidates=requirements(refs,p,day,current_exceptions(session,identity,version) if exception_ids is None else exception_ids)
    records=session.scalars(scope_query(select(ApprovalRecord),ApprovalRecord,identity).where(ApprovalRecord.transaction_id==version.transaction_id,ApprovalRecord.transaction_version==version.version).order_by(ApprovalRecord.sequence,ApprovalRecord.approved_at)).all()
    requests=session.scalars(scope_query(select(ApprovalRequest),ApprovalRequest,identity).where(ApprovalRequest.transaction_id==version.transaction_id,ApprovalRequest.transaction_version==version.version)).all()
    request_ids=[r.id for r in requests if policy and str(r.policy_id)==policy['id'] and r.policy_version==policy['version']]
    declines=session.scalars(scope_query(select(ApprovalAction),ApprovalAction,identity).where(ApprovalAction.request_id.in_(request_ids),ApprovalAction.state=='DECLINED')).all() if request_ids else []
    steps=[];seen=set();prior_time=None;valid=bool(policy and required and policy['id']==p.get('approval_policy_id'))
    for needed in required:
        matches=[r for r in records if r.sequence==needed['sequence'] and str(r.policy_id)==policy['id'] and r.policy_version==policy['version']];r=matches[0] if len(matches)==1 else None
        permitted=False;deleg=None;reason='MISSING_APPROVAL'
        if r:
            permitted,deleg,reason=authority(refs,p,policy,needed['role'],str(r.actor_id),str(version.author_id),r.approved_at.isoformat()[:10])
            permitted=bool(permitted and r.role==needed['role'] and r.state=='APPROVED' and r.approved_at<=utcnow() and str(r.actor_id) not in seen and (prior_time is None or prior_time<=r.approved_at))
            seen.add(str(r.actor_id));prior_time=r.approved_at
        steps.append(needed|{'state':'DECLINED' if any(a.sequence==needed['sequence'] for a in declines) else r.state if r else 'PENDING','authorized':permitted,'reason':reason,'record_id':str(r.id) if r else None,'actor_id':str(r.actor_id) if r else None,'authority_id':str(r.actor_id) if r else None,'delegation_id':deleg and deleg['id'],'transaction_version':version.version})
    return {'policy_valid':valid,'policy_id':policy and policy['id'],'policy_version':policy and policy['version'],'steps':steps,'authority_valid':valid and all(s['authorized'] for s in steps),'candidate_policy_ids':[r['id'] for r in candidates]}


def create_request(session,identity,transaction_id,expected,reason,correlation):
    finance.scope_lock(session,identity);t=finance.get(session,Transaction,identity,transaction_id)
    if t.latest_version!=expected:raise DomainError(409,'STALE_VERSION','Refresh before requesting approvals.')
    version=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==t.id,TransactionVersion.version==expected));refs={k:r.payload|{'_kind':r.kind} for k,r in active_records(session,identity).items()}
    p=version.payload;day=p.get('invoice_date' if p['branch']=='VENDOR_INVOICE' else 'expense_date');policy,steps,candidates=requirements(refs,p,day,current_exceptions(session,identity,version))
    if not policy or not steps or policy['id']!=p.get('approval_policy_id'):raise DomainError(409,'APPROVAL_POLICY_AMBIGUOUS','Select exactly one effective approval policy.')
    old=session.scalar(scope_query(select(ApprovalRequest),ApprovalRequest,identity).where(ApprovalRequest.transaction_id==t.id,ApprovalRequest.transaction_version==expected,ApprovalRequest.policy_id==UUID(policy['id']),ApprovalRequest.policy_version==policy['version'],ApprovalRequest.requirements_digest==digest(steps)))
    if old:return view_request(session,identity,old,refs,version)
    row=ApprovalRequest(**identity.scope(),transaction_id=t.id,transaction_version=expected,policy_id=UUID(policy['id']),policy_version=policy['version'],requirements=steps,payload_digest=version.content_digest,requirements_digest=digest(steps));session.add(row);session.flush()
    finance.audit(session,identity,'APPROVAL_REQUESTED',row.id,1,reason,correlation,{'transaction_id':str(t.id),'transaction_version':expected,'steps':steps})
    return view_request(session,identity,row,refs,version)


def view_request(session,identity,row,refs=None,version=None):
    t=finance.get(session,Transaction,identity,row.transaction_id)
    if refs is None:refs={k:r.payload|{'_kind':r.kind} for k,r in active_records(session,identity).items()}
    if version is None:version=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==row.transaction_id,TransactionVersion.version==row.transaction_version))
    actions=session.scalars(scope_query(select(ApprovalAction),ApprovalAction,identity).where(ApprovalAction.request_id==row.id).order_by(ApprovalAction.created_at,ApprovalAction.id)).all()
    current_state=state(session,identity,version,refs)
    return projection({'id':row.id,'transaction_id':row.transaction_id,'transaction_version':row.transaction_version,'policy_id':row.policy_id,'policy_version':row.policy_version,'requirements':row.requirements,'stale':t.latest_version!=row.transaction_version or version.content_digest!=row.payload_digest or refs.get(str(row.policy_id),{}).get('version')!=row.policy_version or [{'sequence':s['sequence'],'role':s['role']} for s in current_state['steps']]!=row.requirements,'status':current_state,'actions':[{'id':r.id,'actor_id':r.actor_id,'sequence':r.sequence,'state':r.state,'reason':r.reason,'delegation_id':r.delegation_id,'created_at':r.created_at} for r in actions]})


def act(session,identity,request_id,data,correlation):
    finance.scope_lock(session,identity);row=finance.get(session,ApprovalRequest,identity,request_id);t=finance.get(session,Transaction,identity,row.transaction_id)
    if t.latest_version!=data['expected_version'] or t.latest_version!=row.transaction_version:raise DomainError(409,'STALE_APPROVAL','Facts changed; obtain a new approval request.')
    version=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==t.id,TransactionVersion.version==t.latest_version));refs={k:r.payload|{'_kind':r.kind} for k,r in active_records(session,identity).items()};policy=refs.get(str(row.policy_id))
    wanted=next((s for s in row.requirements if s['sequence']==data['sequence']),None)
    permitted=False;deleg=None;code='SEQUENCE_INVALID'
    if wanted and policy and policy['version']==row.policy_version:
        current=state(session,identity,version,refs);previous=[s for s in current['steps'] if s['sequence']<data['sequence']]
        if [{'sequence':s['sequence'],'role':s['role']} for s in current['steps']]!=row.requirements:raise DomainError(409,'STALE_APPROVAL_REQUIREMENTS','Current exception requirements changed; request the current chain.')
        if all(s['state']=='APPROVED' and s['authorized'] for s in previous):
            permitted,deleg,code=authority(refs,version.payload,policy,wanted['role'],str(identity.actor_id),str(version.author_id),utcnow().date().isoformat(),identity.roles)
            existing=[s for s in current['steps'] if s['state']=='APPROVED']
            if any(s['actor_id']==str(identity.actor_id) or s['sequence']==data['sequence'] for s in existing):permitted=False;code='DUPLICATE_STEP_OR_ACTOR'
        else:code='PREVIOUS_STEP_REQUIRED'
    declined=session.scalar(scope_query(select(ApprovalAction),ApprovalAction,identity).where(ApprovalAction.request_id==row.id,ApprovalAction.state=='DECLINED'))
    if declined:permitted=False;code='REQUEST_DECLINED'
    state_name=data['action'] if permitted else 'REJECTED'
    action=ApprovalAction(**identity.scope(),request_id=row.id,sequence=data['sequence'],actor_id=identity.actor_id,authority_id=identity.actor_id if permitted else None,authority_version=refs[str(identity.actor_id)]['version'] if permitted else None,delegation_id=UUID(deleg['id']) if deleg else None,delegation_version=deleg['version'] if deleg else None,state=state_name,reason=data['reason']);session.add(action);session.flush()
    finance.audit(session,identity,'APPROVAL_'+state_name,row.id,1,data['reason'],correlation,{'sequence':data['sequence'],'actor_id':str(identity.actor_id),'rejection_code':None if permitted else code,'transaction_version':row.transaction_version})
    if not permitted:return {'rejected':True,'code':code,'request':view_request(session,identity,row,refs,version)}
    if data['action']=='APPROVED':
        session.add(ApprovalRecord(**identity.scope(),transaction_id=t.id,transaction_version=t.latest_version,policy_id=row.policy_id,policy_version=row.policy_version,actor_id=identity.actor_id,role=wanted['role'],sequence=data['sequence'],state='APPROVED',approved_at=utcnow()));session.flush()
    finance.enqueue(session,identity,t.id,t.latest_version,'Approval action requires fresh screening',correlation,str(action.id))
    return {'rejected':False,'request':view_request(session,identity,row,refs,version)}


def waive(session,identity,transaction_id,data,correlation):
    finance.scope_lock(session,identity);t=finance.get(session,Transaction,identity,transaction_id)
    if t.latest_version!=data['expected_version']:raise DomainError(409,'STALE_VERSION','Refresh before a waiver.')
    refs={k:r.payload|{'_kind':r.kind} for k,r in active_records(session,identity).items()};profiles=[r for r in refs.values() if r['_kind']=='finance_profiles'];profile=profiles[0] if len(profiles)==1 else None
    if not profile or data['rule_id'] not in profile['waivable_rules'] or not set(profile['waiver_roles'])&identity.roles:raise DomainError(403,'WAIVER_FORBIDDEN','This rule is nonwaivable or the actor lacks configured waiver authority.')
    from app.db.models import Evaluation,RuleResultRow
    evaluation=finance.get(session,Evaluation,identity,t.latest_evaluation_id) if t.latest_evaluation_id else None
    rule=session.scalar(scope_query(select(RuleResultRow),RuleResultRow,identity).where(RuleResultRow.evaluation_id==evaluation.id,RuleResultRow.rule_id==data['rule_id'])) if evaluation else None
    if not evaluation or evaluation.transaction_version!=t.latest_version or not rule or rule.status in ('PASS','NOT_APPLICABLE'):raise DomainError(409,'WAIVER_RESULT_REQUIRED','Waiver needs a current unresolved rule result.')
    expires=__import__('datetime').datetime.fromisoformat(data['expires_at'].replace('Z','+00:00'))
    if expires.tzinfo is None or not utcnow()<expires<=utcnow()+timedelta(days=profile.get('waiver_maximum_days',7)):raise DomainError(422,'WAIVER_EXPIRY_INVALID','Use a future UTC expiry within the configured maximum.')
    if not data['evidence_ids']:raise DomainError(422,'WAIVER_EVIDENCE_REQUIRED','Cite actual current evaluation evidence.')
    from app.db.models import EvidenceObject
    for eid in data['evidence_ids']:
        source=finance.get(session,EvidenceObject,identity,UUID(eid))
        if source.evaluation_id!=evaluation.id:raise DomainError(409,'WAIVER_EVIDENCE_STALE','Evidence must belong to the current evaluation.')
    row=Waiver(**identity.scope(),transaction_id=t.id,transaction_version=t.latest_version,rule_id=rule.rule_id,rule_version=rule.rule_version,actor_id=identity.actor_id,policy_id=UUID(profile['id']),policy_version=profile['version'],reason=data['reason'],evidence=data['evidence_ids'],expires_at=expires);session.add(row);session.flush();finance.audit(session,identity,'RULE_WAIVED',row.id,1,data['reason'],correlation,{'rule_id':row.rule_id,'transaction_version':t.latest_version,'expires_at':expires.isoformat()})
    finance.enqueue(session,identity,t.id,t.latest_version,'Explicit rule waiver requires fresh controls',correlation,str(row.id));return projection({'id':row.id,'rule_id':row.rule_id,'rule_version':row.rule_version,'transaction_version':row.transaction_version,'expires_at':row.expires_at,'original_result_retained':True})
