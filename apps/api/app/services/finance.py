"""Transactional orchestration. Immutable facts, guarded effects and atomic audit."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
import html
from uuid import UUID, uuid4, uuid5
from sqlalchemy import select, update, or_, and_, func
from app.core.errors import DomainError, unavailable
from app.core.serialization import canonical_json, digest, projection, utcnow
from app.db.models import *
from app.db.session import scope_query, advisory_lock
from app.rules.engine import RuleContext, evaluate, RULESET, DECISION_POLICY
from app.services.references import snapshot, snapshot_records, pinned, number_key


def get(session, model, identity, record_id):
    row=session.scalar(scope_query(select(model),model,identity).where(model.id==record_id))
    if row is None:raise unavailable()
    if 'EMPLOYEE' in identity.roles and not {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER'}&identity.roles:
        txid=getattr(row,'transaction_id',None)
        if model is Transaction:txid=row.id
        if model in (Evaluation,EvidenceObject,Report) and txid is None:
            eid=getattr(row,'evaluation_id',None)
            evaluated=session.scalar(scope_query(select(Evaluation),Evaluation,identity).where(Evaluation.id==eid)) if eid else None
            txid=evaluated.transaction_id if evaluated else None
        if txid:
            t=session.scalar(scope_query(select(Transaction),Transaction,identity).where(Transaction.id==txid))
            current=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==txid,TransactionVersion.version==t.latest_version)) if t else None
            if not current or current.party_id!=identity.actor_id:raise unavailable()
        if model.__tablename__=='documents':
            from app.db.document_models import UploadSession,TransactionDocument
            owned=session.scalar(scope_query(select(UploadSession),UploadSession,identity).where(UploadSession.document_id==row.id,UploadSession.actor_id==identity.actor_id))
            linked=session.scalar(scope_query(select(TransactionVersion).join(TransactionDocument,(TransactionDocument.transaction_id==TransactionVersion.transaction_id)&(TransactionDocument.transaction_version==TransactionVersion.version)),TransactionVersion,identity).where(TransactionDocument.document_id==row.id,TransactionVersion.party_id==identity.actor_id))
            if not owned and not linked:raise unavailable()
    return row


def scope_lock(session,identity):
    # A conservative scope lock protects duplicate and capacity checks/finalization together.
    # Phase 3 can refine granularity without weakening the admission invariant.
    advisory_lock(session,f'finance:{identity.tenant_id}:{identity.legal_entity_id}')


def audit(session,identity,action,object_id,version,reason,correlation,payload=None):
    tenant=session.scalar(select(Tenant).where(Tenant.id==identity.tenant_id).with_for_update())
    if tenant is None:raise DomainError(503,'REFERENCE_NOT_READY','Development reference seed is required.')
    event_id=uuid4();at=utcnow();sequence=tenant.audit_sequence+1
    data=projection({'id':event_id,'tenant_id':identity.tenant_id,'legal_entity_id':identity.legal_entity_id,'sequence':sequence,'actor_id':identity.actor_id,'action':action,'object_id':object_id,'object_version':version,'reason':reason,'correlation_id':correlation,'created_at':at,'payload':payload or {}})
    hashed=digest({'previous_hash':tenant.audit_hash,'event':data})
    session.add(AuditEvent(**identity.scope(),id=event_id,created_at=at,sequence=sequence,actor_id=identity.actor_id,action=action,object_id=object_id,object_version=version,reason=reason,correlation_id=correlation,previous_hash=tenant.audit_hash,event_hash=hashed,payload=payload or {}))
    tenant.audit_sequence=sequence;tenant.audit_hash=hashed
    try:session.flush()
    except Exception:
        from app.core.observability import log
        # No actor, source payload, DB/provider exception text or secret enters
        # this signal. The failed business transaction still rolls back.
        log.error('{"event":"audit_write_failed"}')
        raise


def idempotent(session,identity,endpoint,key,body,status,operation):
    if not key or len(key)>128 or not key.isascii() or any(ord(c)<33 for c in key):
        raise DomainError(400,'IDEMPOTENCY_KEY_REQUIRED','Provide an ASCII Idempotency-Key of 1–128 characters.')
    hashed=digest(body)
    advisory_lock(session,f'idem:{identity.tenant_id}:{identity.legal_entity_id}:{identity.actor_id}:{endpoint}:{key}')
    row=session.scalar(scope_query(select(IdempotencyRecord),IdempotencyRecord,identity).where(IdempotencyRecord.actor_id==identity.actor_id,IdempotencyRecord.endpoint==endpoint,IdempotencyRecord.key==key))
    if row:
        if row.request_hash!=hashed:raise DomainError(409,'IDEMPOTENCY_CONFLICT','This key was already used with different input.')
        return row.response,row.response_status
    scope_lock(session,identity)
    response=projection(operation())
    session.add(IdempotencyRecord(**identity.scope(),actor_id=identity.actor_id,endpoint=endpoint,key=key,request_hash=hashed,response_status=status,response=response));session.flush()
    return response,status


def create_transaction(session,identity,payload,reason,correlation,transaction_id=None,*,normalizer_version='structured-p1-v1'):
    scope_lock(session,identity)
    row=Transaction(**identity.scope(),id=transaction_id or uuid4(),branch=payload['branch'],latest_version=1,row_version=1,processing_state='RECEIVED',eligible=False)
    session.add(row);session.flush()
    append_version(session,identity,row,payload,1,reason,normalizer_version=normalizer_version)
    audit(session,identity,'TRANSACTION_CREATED',row.id,1,reason,correlation,{'branch':row.branch})
    return {'id':str(row.id),'version':1,'processing_state':row.processing_state}


def append_version(session,identity,row,payload,version,reason,*,normalizer_version='structured-p1-v1'):
    payload=dict(payload)
    for field in ['lines','items']:
        payload[field]=[dict(item,id=item.get('id') or str(uuid5(row.id,f'{field}:{i}'))) for i,item in enumerate(payload.get(field,[]),1)]
    vendor=row.branch=='VENDOR_INVOICE';amount=payload.get('total_amount' if vendor else 'requested_amount');day=payload.get('invoice_date' if vendor else 'expense_date');party=payload.get('vendor_id' if vendor else 'employee_id')
    fact=TransactionVersion(**identity.scope(),transaction_id=row.id,version=version,payload=payload,total_amount=Decimal(amount) if amount is not None else None,currency=payload.get('currency'),business_date=date.fromisoformat(day) if day else None,party_id=UUID(party) if party else None,number_key=number_key(payload.get('invoice_number' if vendor else 'claim_number')),content_digest=digest(payload),author_id=identity.actor_id,change_reason=reason)
    fact.normalizer_version=normalizer_version
    session.add(fact);session.flush();return fact


def release(session,identity,transaction_id):
    from app.services.finance_ledger import release_transaction
    release_transaction(session,identity,transaction_id)
    session.execute(scope_query(update(CapacityReservation),CapacityReservation,identity).where(CapacityReservation.transaction_id==transaction_id,CapacityReservation.state=='ACTIVE').values(state='RELEASED'))
    session.execute(scope_query(update(ReviewCase),ReviewCase,identity).where(ReviewCase.transaction_id==transaction_id,ReviewCase.state.in_(['OPEN','ASSIGNED','AWAITING_INFORMATION'])).values(state='SUPERSEDED',row_version=ReviewCase.row_version+1,updated_at=utcnow()))


def require_active(row):
    if row.processing_state=='CANCELLED':raise DomainError(409,'TRANSACTION_CANCELLED','This transaction is cancelled; its history remains available.')


def review_guard(session,identity,row,data=None):
    """Legacy mutation routes obey ownership once a case has been claimed."""
    if session.info.get('review_authorized_transaction')==row.id:return
    case=session.scalar(scope_query(select(ReviewCase),ReviewCase,identity).where(ReviewCase.transaction_id==row.id).order_by(ReviewCase.created_at.desc()).limit(1))
    if not case or not case.owner_id or case.state in ('RESOLVED','CANCELLED'):return
    if case.owner_id!=identity.actor_id:raise DomainError(403,'CASE_NOT_OWNED','The assigned reviewer must make this change.')
    data=data or {}
    if str(case.id)!=str(data.get('review_case_id')) or case.row_version!=data.get('expected_review_version'):
        raise DomainError(409,'STALE_REVIEW_VERSION','Use the current owned review and expected review version.',details={'current_review_version':case.row_version,'review_case_id':str(case.id)})
    session.info['review_authorized_transaction']=row.id


def revise(session,identity,record_id,data,correlation,*,normalizer_version='structured-p1-v1',copy_document_links=True):
    scope_lock(session,identity);row=get(session,Transaction,identity,record_id)
    require_active(row)
    review_guard(session,identity,row,data)
    if row.latest_version!=data['expected_version']:raise DomainError(409,'STALE_VERSION','Refresh the case before revising.')
    if row.branch!=data['transaction']['branch']:raise DomainError(409,'BRANCH_IMMUTABLE','Create a separate transaction for a different branch.')
    release(session,identity,row.id)
    row.latest_version+=1;row.row_version+=1;row.eligible=False;row.decision=None;row.processing_state='RECEIVED'
    append_version(session,identity,row,data['transaction'],row.latest_version,data['reason'],normalizer_version=normalizer_version)
    if copy_document_links:
        from app.services.document_facts import copy_links
        copy_links(session,identity,row.id,row.latest_version-1,row.latest_version)
    audit(session,identity,'TRANSACTION_REVISED',row.id,row.latest_version,data['reason'],correlation)
    audit(session,identity,'ELIGIBILITY_INVALIDATED',row.id,row.latest_version,'Material revision requires fresh approvals, allocations and screening',correlation,{'previous_version':row.latest_version-1,'previous_evaluation_id':str(row.latest_evaluation_id) if row.latest_evaluation_id else None})
    return {'id':str(row.id),'version':row.latest_version,'processing_state':row.processing_state}


def enqueue(session,identity,record_id,expected,reason,correlation,intent,evaluated_at=None):
    scope_lock(session,identity);row=get(session,Transaction,identity,record_id)
    require_active(row)
    if row.latest_version!=expected:raise DomainError(409,'STALE_VERSION','Evaluation must target the latest version.')
    latest=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==row.id,TransactionVersion.version==expected))
    snap=snapshot(session,identity,latest.business_date.isoformat() if latest.business_date else None)
    catalog=pinned(session,identity,snap.id)
    stage_version='rules-p3-v1' if any(r.get('_kind')=='finance_profiles' for r in catalog.values()) else RULESET
    key=digest({'transaction':row.id,'version':expected,'snapshot':snap.id,'stage':stage_version,'intent':intent})
    job=session.scalar(scope_query(select(Job),Job,identity).where(Job.stage_key==key))
    if job:return {'job_id':str(job.id),'state':job.state,'transaction_id':str(row.id)}
    release(session,identity,row.id);row.eligible=False;row.decision=None;row.processing_state='QUEUED';row.row_version+=1
    job=Job(**identity.scope(),id=uuid4(),transaction_id=row.id,transaction_version=expected,snapshot_id=snap.id,stage_key=key,generation=row.row_version,stage_version=stage_version,evaluated_at=evaluated_at or utcnow(),actor_id=identity.actor_id)
    session.add(job);session.flush()
    session.add(OutboxEvent(**identity.scope(),job_id=job.id,event_type='EVALUATION_REQUESTED',aggregate_id=row.id,aggregate_version=expected,payload={'job_id':str(job.id),'stage':stage_version}))
    audit(session,identity,'EVALUATION_REQUESTED',row.id,expected,reason,correlation,{'job_id':str(job.id),'snapshot_id':str(snap.id)})
    return {'job_id':str(job.id),'state':job.state,'transaction_id':str(row.id)}


def build_context(session,identity,job,version):
    with localcontext() as dc:
        dc.prec=60
        return _build_context(session,identity,job,version)


def _build_context(session,identity,job,version):
    p=version.payload;refs=pinned(session,identity,job.snapshot_id);vendor=p['branch']=='VENDOR_INVOICE'
    from app.services.document_facts import source_context
    refs,document_sources,document_valid=source_context(session,identity,version,refs)
    # Exact predicates use scope/party/number/currency/amount/date index, not a global history scan.
    duplicate_refs=[];duplicates=[]
    if vendor and all(v is not None for v in [version.party_id,version.number_key,version.total_amount,version.currency,version.business_date]):
        q=scope_query(select(ReferenceRecord),ReferenceRecord,identity).where(ReferenceRecord.kind=='historical_transactions',ReferenceRecord.party_id==version.party_id,ReferenceRecord.number_key==version.number_key,ReferenceRecord.amount==version.total_amount,ReferenceRecord.currency==version.currency,ReferenceRecord.business_date==version.business_date)
        duplicate_refs=[r.payload|{'_kind':r.kind} for r in session.scalars(q.limit(100)) if r.payload['lifecycle'] not in ('CANCELLED','REVERSED')]
        q=scope_query(select(TransactionVersion).join(Transaction,(TransactionVersion.transaction_id==Transaction.id)&(TransactionVersion.tenant_id==Transaction.tenant_id)&(TransactionVersion.legal_entity_id==Transaction.legal_entity_id)),TransactionVersion,identity).where(TransactionVersion.transaction_id!=version.transaction_id,TransactionVersion.version==Transaction.latest_version,Transaction.eligible.is_(True),TransactionVersion.party_id==version.party_id,TransactionVersion.number_key==version.number_key,TransactionVersion.total_amount==version.total_amount,TransactionVersion.currency==version.currency,TransactionVersion.business_date==version.business_date)
        duplicates=[{'id':str(r.transaction_id),'version':r.version} for r in session.scalars(q)]
    daily=[];conflicts=[]
    if not vendor:
        q=scope_query(select(ReferenceRecord),ReferenceRecord,identity).where(ReferenceRecord.kind=='historical_transactions',ReferenceRecord.party_id==version.party_id,ReferenceRecord.business_date==version.business_date,ReferenceRecord.currency==version.currency)
        daily=[r.payload|{'_kind':r.kind} for r in session.scalars(q.limit(201)) if r.payload.get('category')==p.get('category') and r.payload.get('local_timezone')==p.get('local_timezone') and r.payload.get('capacity_state') in ('RESERVED','CONSUMED')]
        q=scope_query(select(TransactionVersion).join(Transaction,(TransactionVersion.transaction_id==Transaction.id)&(TransactionVersion.tenant_id==Transaction.tenant_id)&(TransactionVersion.legal_entity_id==Transaction.legal_entity_id)),TransactionVersion,identity).where(Transaction.branch=='EMPLOYEE_EXPENSE',Transaction.eligible.is_(True),TransactionVersion.transaction_id!=version.transaction_id,TransactionVersion.version==Transaction.latest_version,TransactionVersion.currency==version.currency)
        if len(daily)>200:raise DomainError(503,'HISTORY_LIMIT','Daily history requires a narrower query.')
        sources={i.get('source_document_id') for i in p['items']}
        active_claims=session.scalars(q.limit(201)).all()
        if len(active_claims)>200:raise DomainError(503,'ACTIVE_CLAIM_LIMIT','Active claim capacity requires a narrower query.')
        for r in active_claims:
            if any(i.get('source_document_id') in sources for i in r.payload['items']):conflicts.append(str(r.transaction_id))
            if r.party_id==version.party_id and r.business_date==version.business_date and r.payload.get('category')==p.get('category') and r.payload.get('local_timezone')==p.get('local_timezone'):
                daily.append({'id':str(r.transaction_id),'version':r.version,'claimed_amount':str(sum((Decimal(i['claimed_amount']) for i in r.payload['items']),Decimal('0')))})
    if vendor:
        line_ids=[i['po_line_id'] for i in p['lines'] if i.get('po_line_id')]
        q=scope_query(select(ReferenceRecord),ReferenceRecord,identity).where(ReferenceRecord.kind=='matching_allocations',ReferenceRecord.payload['po_line_id'].as_string().in_(line_ids)).limit(201)
        allocations=session.scalars(q).all()
        if len(allocations)>200:raise DomainError(503,'ALLOCATION_LIMIT','PO allocation history requires a narrower query.')
        refs.update({str(r.id):r.payload|{'_kind':r.kind} for r in allocations})
    refs.update({r['id']:r for r in duplicate_refs+daily if r.get('_kind')})
    capacity={};commitments={};capacity_evidence=[]
    q=scope_query(select(CapacityReservation),CapacityReservation,identity).where(CapacityReservation.state=='ACTIVE',CapacityReservation.transaction_id!=version.transaction_id)
    with localcontext() as dc:
        dc.prec=60
        reservations=session.scalars(q.limit(2001)).all()
        if len(reservations)>2000:raise DomainError(503,'CAPACITY_LIMIT','Active capacity requires a narrower scope.')
        for r in reservations:
            bucket=capacity.setdefault(str(r.reference_id),{'amount':Decimal('0'),'quantity':Decimal('0')});bucket['amount']+=r.amount;bucket['quantity']+=r.quantity
            capacity_evidence.append({'id':str(r.id),'version':1,'reference_id':str(r.reference_id),'kind':r.kind,'amount':str(r.amount),'quantity':str(r.quantity),'transaction_id':str(r.transaction_id)})
            if r.kind=='PO_LINE':
                po=refs[str(r.reference_id)]['po_id'];commitments[po]=commitments.get(po,Decimal('0'))+r.amount
    q=scope_query(select(ApprovalRecord),ApprovalRecord,identity).where(ApprovalRecord.transaction_id==version.transaction_id,ApprovalRecord.transaction_version==version.version).order_by(ApprovalRecord.sequence)
    approvals=[{'id':str(a.id),'version':1,'transaction_version':a.transaction_version,'policy_id':str(a.policy_id),'policy_version':a.policy_version,'actor_id':str(a.actor_id),'role':a.role,'sequence':a.sequence,'state':a.state,'approved_at':a.approved_at.isoformat()} for a in session.scalars(q)]
    source=session.scalar(scope_query(select(ImportRow),ImportRow,identity).where(ImportRow.transaction_id==version.transaction_id))
    core_context=RuleContext.pin(transaction=p,transaction_id=str(version.transaction_id),transaction_version=version.version,tenant_id=str(identity.tenant_id),legal_entity_id=str(identity.legal_entity_id),author_id=str(version.author_id),snapshot_id=str(job.snapshot_id),references=refs,duplicates=duplicate_refs+duplicates,daily_history=daily,receipt_conflicts=conflicts,capacity=capacity,capacity_evidence=capacity_evidence,po_commitment_used=commitments,approvals=approvals,evaluated_at=job.evaluated_at.isoformat(),context_complete=True,import_source={'id':str(source.id),'batch_id':str(source.batch_id),'sheet':source.sheet,'row_number':source.row_number} if source else None)
    data=json_context(core_context)
    data.update(document_sources=document_sources,document_source_validation=document_valid)
    if source:
        from app.db.document_models import ImportCell
        cells=session.scalars(scope_query(select(ImportCell),ImportCell,identity).where(ImportCell.row_id==source.id,ImportCell.column!='transaction_json')).all()
        data['import_cells']=[{'column':cell.column,'field_path':cell.field_path} for cell in cells]
    from app.services.finance_controls import augment
    data=augment(session,identity,version,data)
    return RuleContext.pin(**data)


def report_html(content):
    esc=lambda value:html.escape(str(value),quote=True)
    sections=[]
    for rule in content['rules']:
        links=''.join('<li><a href="../../evidence/'+esc(e['id'])+'">'+esc(e['reference']['kind'])+' / '+esc(e['reference']['record_id'])+' / version '+esc(e['reference']['record_version'])+'</a></li>' for e in rule['evidence'])
        sections.append('<section><h2>'+esc(rule['rule_id'])+' · '+esc(rule['status'])+'</h2><p>Rule version '+esc(rule['version'])+' · effect '+esc(rule['decision_effect'])+'</p><p>'+esc(rule['reason'])+'</p><h3>Observed</h3><pre>'+esc(canonical_json(rule['observed']))+'</pre><h3>Expected / tolerance</h3><pre>'+esc(canonical_json({'expected':rule['expected'],'tolerance':rule['tolerance']}))+'</pre><h3>Evidence references</h3><ul>'+links+'</ul></section>')
    intelligence=content.get('intelligence',{})
    risk_summary='<p>'+esc(content.get('evaluation_mode','RULES_ONLY'))+' · intelligence '+esc(content.get('model_status','NOT_CONFIGURED'))+' · Versioned source evidence is linked below.</p>'
    if intelligence and intelligence.get('mode')!='RULES_ONLY':
        sections.insert(0,'<section><h2>Transaction intelligence</h2><p>Statistical review support; finance controls remain authoritative. Synthetic development observations are not production validation.</p><p>Score kind: '+esc(intelligence.get('score_kind') or 'Unavailable')+' · Value: '+esc(intelligence.get('score') if intelligence.get('score') is not None else 'Unavailable')+' · Explanation: '+esc(intelligence.get('explanation_status'))+'</p><p>Artifact version: '+esc(intelligence.get('model_version') or 'Unavailable')+'</p><ul>'+''.join('<li>'+esc(f['text'])+'</li>' for f in intelligence.get('factors',[]))+'</ul><p>Review reason: '+esc(intelligence.get('review_reason') or 'None')+'</p></section>')
    metadata={key:content.get(key) for key in ['schema_version','evaluation_id','evaluation_version','transaction_id','transaction_version','reference_snapshot_id','ruleset_version','decision_policy_version','completeness','input_digest','evaluated_at','supersedes_id','reason_codes']}
    sections.insert(0,'<section><h2>Waiver dispositions</h2><pre>'+esc(canonical_json(content.get('waiver_dispositions',[])))+'</pre><p>Original rule findings remain visible below.</p></section>' if content.get('waiver_dispositions') else '')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Screening report</title><style>body{font:15px/1.5 system-ui;margin:2rem;color:#16324f}section{border-top:1px solid #ccd5df;margin-top:2rem;padding-top:1rem}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6fa;padding:12px;font-size:12px}h1{font-size:24px}h2{font-size:18px}h3{font-size:14px}a{color:#185b8a;overflow-wrap:anywhere}</style><h1>'+esc(content['decision'])+' — Synthetic screening report</h1><p>Transaction '+esc(content['transaction_id'])+' · version '+esc(content['transaction_version'])+'</p><p>Eligibility at evaluation: '+esc(content['eligible'])+'. No payment execution.</p>'+risk_summary+'<h2>Pinned evaluation metadata</h2><pre>'+esc(canonical_json(metadata))+'</pre><h2>Next actions</h2><ul>'+''.join('<li>'+esc(action)+'</li>' for action in content['next_actions'])+'</ul>'+''.join(sections)+'</html>'


def finalize(session,identity,job_id,lease_owner):
    scope_lock(session,identity)
    job=session.scalar(scope_query(select(Job),Job,identity).where(Job.id==job_id).with_for_update())
    if job is None:raise unavailable()
    if job.state=='SUCCEEDED':return job.result_evaluation_id
    if job.stage!='EVALUATE' or job.stage_version not in (RULESET,'rules-p3-v1'):raise DomainError(409,'STAGE_VERSION_UNSUPPORTED','A compatible worker is required for this stage version.')
    if job.state!='RUNNING' or job.lease_owner!=lease_owner or job.lease_until<=utcnow():raise DomainError(409,'LEASE_LOST','The job lease is no longer valid.')
    transaction=get(session,Transaction,identity,job.transaction_id)
    if transaction.processing_state=='CANCELLED':
        job.state='CANCELLED';job.lease_until=None;job.updated_at=utcnow();return None
    if transaction.latest_version!=job.transaction_version or transaction.row_version!=job.generation:
        job.state='STALE';job.lease_until=None;job.updated_at=utcnow()
        audit(session,identity,'JOB_STALE',job.id,1,'A newer canonical version or evaluation request superseded this job',str(job.id));return None
    version=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==transaction.id,TransactionVersion.version==job.transaction_version))
    context=build_context(session,identity,job,version)
    context_data=json_context(context)
    evaluated_snapshot=snapshot_records(session,identity,[(UUID(r['id']),r['version']) for r in context_data['references'].values()])
    context_data['snapshot_id']=str(evaluated_snapshot.id)
    context=RuleContext.pin(**context_data)
    from app.rules.finance_phase3 import evaluate as evaluate_finance
    decision=evaluate_finance(context)
    selected_ruleset='rules-p3-v1' if context_data.get('finance_v3') else RULESET
    from app.rules.import_evidence import mapped_evidence
    decision=mapped_evidence(decision,context_data)
    from app.services import intelligence
    decision,feature_data,risk_data,risk_deployment,risk_model=intelligence.prepare(session,identity,job,version,context_data,decision)
    evaluation=Evaluation(**identity.scope(),id=uuid4(),transaction_id=transaction.id,transaction_version=version.version,reference_snapshot_id=evaluated_snapshot.id,ruleset_version=selected_ruleset,decision_policy_version=DECISION_POLICY,evaluation_mode=risk_data['mode'],completeness=decision.completeness,decision=decision.decision,eligible=decision.eligible,input_digest=digest(context.encoded),evaluated_at=job.evaluated_at,supersedes_id=transaction.latest_evaluation_id)
    session.add(evaluation);session.flush()
    intelligence.persist(session,identity,evaluation,feature_data,risk_data,risk_deployment,risk_model)
    session.add(EvaluationInput(**identity.scope(),evaluation_id=evaluation.id,encoded=context.encoded,content_digest=digest(context.encoded)));session.flush()
    rules=[]
    for result in decision.results:
        body=result.json();rule=RuleResultRow(**identity.scope(),id=uuid4(),evaluation_id=evaluation.id,rule_id=result.rule_id,rule_version=result.version,status=result.status,decision_effect=result.decision_effect,result=body)
        session.add(rule);session.flush();evidence=[]
        for reference in body['evidence']:
            item=EvidenceObject(**identity.scope(),id=uuid4(),evaluation_id=evaluation.id,rule_result_id=rule.id,reference=reference);session.add(item);evidence.append({'id':str(item.id),'reference':reference})
        body['evidence']=evidence;body['result_id']=str(rule.id);rules.append(body)
    # Persist the capacity basis used in this evaluation and expose genuine reservation references.
    context_data=json_context(context)
    capacity_refs=context_data['capacity_evidence']
    for body in rules:
        if body['rule_id'] in ('BUD-001','PO-003','PO-004','GRN-001'):
            for reservation in capacity_refs:
                reference={'kind':'HISTORICAL_AGGREGATE','record_id':reservation['id'],'record_version':1,'tenant_id':str(identity.tenant_id),'legal_entity_id':str(identity.legal_entity_id),'snapshot_id':str(evaluated_snapshot.id),'field_path':None,'document_id':None,'page':None,'bbox':None,'observed_value':None,'import_cell':None}
                item=EvidenceObject(**identity.scope(),id=uuid4(),evaluation_id=evaluation.id,rule_result_id=UUID(body['result_id']),reference=reference);session.add(item);body['evidence'].append({'id':str(item.id),'reference':reference})
    release(session,identity,transaction.id)
    if decision.eligible:
        if context_data.get('finance_v3'):
            from app.services.finance_controls import reserve as reserve_finance
            reserve_finance(session,identity,evaluation,version,context_data,decision)
        else:reserve(session,identity,evaluation,version,context_data,decision)
    if decision.decision!='PASS':
        previous_review=session.scalar(scope_query(select(ReviewCase),ReviewCase,identity).where(ReviewCase.transaction_id==transaction.id).order_by(ReviewCase.created_at.desc()).limit(1))
        review=ReviewCase(**identity.scope(),id=uuid4(),evaluation_id=evaluation.id,transaction_id=transaction.id,decision=decision.decision,branch=transaction.branch,reasons=[r.rule_id for r in decision.results if r.decision_effect!='NONE']+([risk_data['review_reason']] if risk_data['review_reason'] else []),state='OPEN')
        if previous_review and previous_review.owner_id and previous_review.state!='CANCELLED':review.owner_id=previous_review.owner_id;review.state='ASSIGNED'
        session.add(review);session.flush()
        audit(session,identity,'REVIEW_CASE_CREATED',review.id,1,'Required controls need resolution',str(job.id),{'evaluation_id':str(evaluation.id),'transaction_id':str(transaction.id),'reason_codes':review.reasons})
    content=projection({'schema_version':'report-p1-v2','evaluation_version':1,'reason_codes':[r.rule_id for r in decision.results if r.decision_effect!='NONE'],'evaluation_id':evaluation.id,'transaction_id':transaction.id,'transaction_version':version.version,'reference_snapshot_id':evaluated_snapshot.id,'ruleset_version':selected_ruleset,'decision_policy_version':DECISION_POLICY,'evaluation_mode':'RULES_ONLY','extraction_mode':'STRUCTURED_SYNTHETIC','model_status':'NOT_CONFIGURED','completeness':decision.completeness,'decision':decision.decision,'eligible':decision.eligible,'input_digest':evaluation.input_digest,'evaluated_at':job.evaluated_at,'supersedes_id':evaluation.supersedes_id,'transaction':redact(version.payload),'rules':rules,'next_actions':[r.reason for r in decision.results if r.decision_effect!='NONE'] or ['Screening checks complete. Authorized human processing remains separate.'],'capacity_basis':capacity_refs})
    if context_data.get('document_sources'):
        from app.rules.document_sources import DOCUMENT_RULE_VERSION
        content.update(extraction_mode='DOCUMENT_DERIVED',document_sources=context_data['document_sources'],
            normalizer_version=version.normalizer_version,document_rules_version=DOCUMENT_RULE_VERSION,schema_version='report-p2-v1')
    if context_data.get('finance_v3'):
        content.update(schema_version='report-p3-v1',finance_controls=projection(context_data['finance_v3']),waiver_dispositions=context_data['finance_v3'].get('waivers',[]))
    content.update(evaluation_mode=risk_data['mode'],model_status=risk_data['status'],intelligence=risk_data)
    if risk_data['review_reason']:
        content['reason_codes'].append(risk_data['review_reason'])
        content['next_actions'].append('Review unusual transaction history' if risk_data['review_reason']=='ANOMALY_ESCALATION' else 'Resolve required intelligence availability or insufficient history')
    generated_html=report_html(content)
    if context_data.get('document_sources'):
        generated_html=generated_html.replace('Versioned source evidence is linked below.',
            'DOCUMENT_DERIVED. Authorized physical page evidence is available; field boxes are shown only where measured.')
    session.add(Report(**identity.scope(),evaluation_id=evaluation.id,content=content,html=generated_html,content_digest=digest(content)))
    if job.lease_until<=utcnow():raise DomainError(409,'LEASE_EXPIRED','Execution exceeded the durable lease deadline.')
    transaction.latest_evaluation_id=evaluation.id;transaction.processing_state='COMPLETED';transaction.decision=decision.decision;transaction.eligible=decision.eligible;transaction.row_version+=1
    job.state='SUCCEEDED';job.result_evaluation_id=evaluation.id;job.lease_until=None;job.updated_at=utcnow();job.last_error=None
    audit(session,identity,'EVALUATION_FINALIZED',transaction.id,version.version,'Deterministic rules evaluated',str(job.id),{'evaluation_id':str(evaluation.id),'decision':decision.decision,'input_digest':evaluation.input_digest})
    if evaluation.supersedes_id:audit(session,identity,'EVALUATION_SUPERSEDED',evaluation.supersedes_id,1,'A new immutable evaluation is current',str(job.id),{'transaction_id':str(transaction.id),'superseded_by':str(evaluation.id)})
    audit(session,identity,'REPORT_GENERATED',evaluation.id,1,'Deterministic JSON and HTML materialized',str(job.id),{'content_digest':digest(content)})
    session.flush();return evaluation.id


def json_context(context):
    import json
    return json.loads(context.encoded)


def redact(payload):
    if isinstance(payload,list):return [redact(v) for v in payload]
    if not isinstance(payload,dict):return payload
    return {k:('[secure equality token redacted]' if k in ('payment_account_token','equality_token') and v else redact(v)) for k,v in payload.items()}


def reserve(session,identity,evaluation,version,context,decision):
    p=version.payload;refs=context['references'];budget=refs[p['budget_id']]
    budget_result=next(r for r in decision.results if r.rule_id=='BUD-001')
    incremental=Decimal(budget_result.observed['incremental_exposure'])
    session.add(CapacityReservation(**identity.scope(),transaction_id=version.transaction_id,transaction_version=version.version,evaluation_id=evaluation.id,reference_id=UUID(budget['id']),reference_version=budget['version'],kind='BUDGET',amount=incremental,quantity=Decimal('0'),currency=p['currency']))
    if p['branch']=='VENDOR_INVOICE':
        with localcontext() as dc:
            dc.prec=60
            for key,kind in [('po_line_id','PO_LINE'),('grn_line_id','GRN_LINE')]:
                aggregate={}
                for line in p['lines']:
                    bucket=aggregate.setdefault(line[key],[Decimal('0'),Decimal('0')]);bucket[0]+=Decimal(line['gross_amount']);bucket[1]+=Decimal(line['quantity'])
                for rid,(amt,qty) in aggregate.items():
                    session.add(CapacityReservation(**identity.scope(),transaction_id=version.transaction_id,transaction_version=version.version,evaluation_id=evaluation.id,reference_id=UUID(rid),reference_version=refs[rid]['version'],kind=kind,amount=amt,quantity=qty,currency=p['currency']))


def transaction_projection(row,versions,job):
    return projection({'job':{'id':job.id,'state':job.state,'stage':job.stage,'attempts':job.attempts,'maximum_attempts':job.maximum_attempts,'last_error':job.last_error} if job else None,'id':row.id,'branch':row.branch,'version':row.latest_version,'processing_state':row.processing_state,'decision':row.decision,'eligible':row.eligible,'latest_evaluation_id':row.latest_evaluation_id,'created_at':row.created_at,'versions':[{'version':v.version,'payload':redact(v.payload),'digest':v.content_digest,'author_id':v.author_id,'reason':v.change_reason,'created_at':v.created_at} for v in versions]})


def transaction_detail(session,identity,record_id):
    row=get(session,Transaction,identity,record_id)
    versions=session.scalars(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==row.id).order_by(TransactionVersion.version)).all()
    job=session.scalar(scope_query(select(Job),Job,identity).where(Job.transaction_id==row.id).order_by(Job.generation.desc(),Job.id.desc()).limit(1))
    from app.services.operations import eligibility
    output=transaction_projection(row,versions,job)
    current=eligibility(session,identity,row)
    return output|{'eligible':current['current_eligible'],'eligibility':current}


def transaction_list(session,identity,query):
    # The list needs only current facts; full revision history belongs to case detail.
    rows=list(session.scalars(query))
    if not rows:return []
    ids=[row.id for row in rows]
    versions=session.scalars(scope_query(select(TransactionVersion).join(Transaction,TransactionVersion.transaction_id==Transaction.id),TransactionVersion,identity).where(TransactionVersion.transaction_id.in_(ids),TransactionVersion.version==Transaction.latest_version)).all()
    current={v.transaction_id:v for v in versions}
    ranked=scope_query(select(Job.id,func.row_number().over(partition_by=Job.transaction_id,order_by=(Job.generation.desc(),Job.id.desc())).label('position')),Job,identity).where(Job.transaction_id.in_(ids)).subquery()
    jobs=session.scalars(scope_query(select(Job).join(ranked,ranked.c.id==Job.id),Job,identity).where(ranked.c.position==1)).all()
    latest={job.transaction_id:job for job in jobs}
    from app.services.operations import eligibility
    output=[]
    for row in rows:
        view=transaction_projection(row,[current[row.id]],latest.get(row.id))
        live=eligibility(session,identity,row)
        output.append(view|{'eligible':live['current_eligible'],'eligibility':live})
    return output


def authorized_report(identity,content):
    """Employee reports retain own facts and aggregate controls, with peer detail masked."""
    if 'EMPLOYEE' not in identity.roles or {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER'}&identity.roles:return content
    import copy
    safe=copy.deepcopy(content)
    if safe.get('finance_controls'):
        safe['finance_controls']['duplicates']=[{'classification':r['classification'],'disposition':r.get('disposition'),'cross_employee_details':'MASKED'} for r in safe['finance_controls'].get('duplicates',[])]
        for key in ('allocations','receipt_usage'):safe['finance_controls'][key]=[{'amount':r.get('amount'),'kind':r.get('kind'),'state':r.get('state'),'cross_employee_details':'MASKED'} for r in safe['finance_controls'].get(key,[])]
    for rule in safe['rules']:
        if rule['rule_id'] in ('DUP-001','DUP-003','EXP-005','PAT-001'):
            rule['observed']={'cross_employee_details':'MASKED','status':rule['status']}
            rule['evidence']=[e for e in rule['evidence'] if e['reference']['kind']=='TRANSACTION' and e['reference']['record_id']==safe['transaction_id']]
    return safe
