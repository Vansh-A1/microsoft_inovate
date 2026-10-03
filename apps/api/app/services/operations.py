"""Scoped operational projections and guarded recovery over retained facts."""
import csv
import io
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID
from sqlalchemy import select, func, or_, and_, cast, text
from sqlalchemy.dialects.postgresql import JSONB
from app.core.errors import DomainError
from app.core.serialization import projection, digest, utcnow, canonical_json
from app.db.models import (Transaction, TransactionVersion, Evaluation, EvaluationInput, Report,
    ReviewCase, Job, OutboxEvent, AuditEvent, RuleResultRow, EvidenceObject, ReferenceRecord, ImportBatch, CapacityReservation)
from app.db.document_models import (Document, DocumentJob, DocumentOutbox, DocumentPage, DocumentVersion, UploadSession, TransactionDocument)
from app.db.workflow_models import ReviewAction, OperationRecord
from app.db.session import scope_query
from app.services import finance

OPEN=('OPEN','ASSIGNED','AWAITING_INFORMATION')
NEXT={'DOC-001':('CORRECT_AMBIGUOUS_TOTAL','Verify unreadable or ambiguous source facts'),
 'DOC-002':('CONFIRM_SUPPORTED_DOCUMENT','Confirm supported document type and page segmentation'),
 'GRN-001':('VERIFY_GOODS_RECEIPT','Verify accepted goods or service evidence'),
 'EXP-001':('REQUEST_RECEIPT','Request actual receipt evidence'),
 'APR-001':('OBTAIN_REQUIRED_APPROVAL','Obtain the missing authorized approval'),
 'APR-002':('VERIFY_APPROVAL_AUTHORITY','Verify approval authority and separation of duties'),
 'VEN-003':('VERIFY_PAYMENT_ACCOUNT','Verify payment instructions against approved master data'),
 'DUP-001':('RESOLVE_DUPLICATE','Compare independently submitted source documents'),
 'DUP-002':('RESOLVE_DUPLICATE','Resolve the corroborated duplicate obligation'),
 'DUP-003':('RESOLVE_DUPLICATE','Compare the possible duplicate'),
 'BUD-001':('VERIFY_BUDGET_CAPACITY','Resolve budget coverage or available capacity'),
 'EXP-003':('REVIEW_ALLOWANCE','Review the allowance and applicable waiver authority'),
 'REF-001':('REFRESH_REFERENCE_DATA','Supply current authorized reference data'),
 'SYS-001':('RESTORE_REQUIRED_DEPENDENCY','Resolve missing required dependencies')}
NEXT.update({'ANOMALY_ESCALATION':('REVIEW_UNUSUAL_TRANSACTION','Review unusual transaction history'),
 'MODEL_UNAVAILABLE':('RESTORE_REQUIRED_INTELLIGENCE','Resolve required intelligence availability or insufficient history'),
 'PASS_AUDIT':('AUDIT_PASS_CASE','Adjudicate the sampled screening result')})

def read_permission(identity):
    if not {'FINANCE_REVIEWER','AUDITOR','OPERATIONS_READER','OPERATIONS_ADMIN'}&identity.roles:
        raise DomainError(403,'FORBIDDEN','Scoped operational or audit access is required.')

def operation(session,identity,kind,object_id,key,details,reason,correlation):
    hashed=digest(key)
    prior=session.scalar(scope_query(select(OperationRecord),OperationRecord,identity).where(OperationRecord.operation_key==hashed))
    if prior:return prior
    row=OperationRecord(**identity.scope(),kind=kind,object_id=object_id,operation_key=hashed,actor_id=identity.actor_id,details=projection(details))
    session.add(row);session.flush()
    finance.audit(session,identity,kind,object_id,1,reason,correlation,{'operation_id':str(row.id),'code':details.get('code')})
    return row

def next_actions(rules):
    return [{'action':NEXT.get(r['rule_id'],('REVIEW_REQUIRED_CONTROL','Resolve the required control'))[0],
        'label':NEXT.get(r['rule_id'],('REVIEW_REQUIRED_CONTROL','Resolve the required control'))[1],
        'rule_id':r['rule_id'],'reason':r['reason']} for r in rules if r['decision_effect']!='NONE' or r['status'] in ('UNKNOWN','ERROR')]

def eligibility(session,identity,t,evaluation=None,now=None):
    """Current operational eligibility is separate from immutable screening outcomes."""
    now=now or utcnow()
    e=evaluation or (finance.get(session,Evaluation,identity,t.latest_evaluation_id) if t.latest_evaluation_id else None)
    status='CURRENT';reason=None
    if not e:return {'current_eligible':False,'evaluation_status':'STALE','eligibility_reason':'EVALUATION_REQUIRED'}
    if e.id!=t.latest_evaluation_id:status='SUPERSEDED';reason='NEWER_EVALUATION'
    elif e.transaction_version!=t.latest_version:status='STALE';reason='FACTS_CHANGED'
    elif t.processing_state!='COMPLETED':status='STALE';reason='CANCELLED' if t.processing_state=='CANCELLED' else 'REEVALUATION_REQUIRED'
    if status=='CURRENT':
        from app.services.intelligence import deployment
        from app.db.risk_models import RiskScore
        current=deployment(session,identity)
        retained=session.scalar(scope_query(select(RiskScore),RiskScore,identity).where(RiskScore.evaluation_id==e.id))
        if (current.id if current else None)!=(retained.deployment_id if retained else None):
            status='STALE';reason='RISK_CONFIGURATION_CHANGED'
    eligible=bool(status=='CURRENT' and t.eligible and e.eligible)
    if eligible:
        stored=session.scalar(scope_query(select(EvaluationInput),EvaluationInput,identity).where(EvaluationInput.evaluation_id==e.id))
        c=json.loads(stored.encoded)
        if c.get('finance_v3'):
            from app.services.reference_imports import active_records,select_policy
            from app.services import finance_ledger
            p=c['transaction'];day=p.get('invoice_date' if p['branch']=='VENDOR_INVOICE' else 'expense_date')
            refs={k:r.payload|{'_kind':r.kind} for k,r in active_records(session,identity,day).items()}
            relevant={'vendors','employees','purchase_orders','po_lines','grn_lines','service_lines','contracts','contract_lines','expense_policies','approval_policies','finance_profiles','budgets','delegations','uom_conversions','company_payments','preapprovals'}
            changed=any(r.get('_kind') in relevant and (r['id'] not in refs or refs[r['id']]['version']!=r['version']) for r in c['references'].values())
            # Newly confirmed payments can invalidate a retained reimbursement even without replacing a master version.
            if p['branch']=='EMPLOYEE_EXPENSE':
                payments={r['id']:r['version'] for r in refs.values() if r.get('_kind')=='company_payments' and r.get('employee_id')==p.get('employee_id')}
                retained={r['id']:r['version'] for r in c['references'].values() if r.get('_kind')=='company_payments' and r.get('employee_id')==p.get('employee_id')}
                changed=changed or payments!=retained
            for kind,key in [('approval_policies','approval_policy_id'),('expense_policies','expense_policy_id')]:
                if kind=='expense_policies' and p['branch']!='EMPLOYEE_EXPENSE':continue
                selected,_=select_policy(refs,kind,p,day,refs.get(p.get('employee_id')))
                if not selected or selected['id']!=p.get(key):changed=True
            profiles=[r for r in refs.values() if r.get('_kind')=='finance_profiles']
            age=profiles[0]['freshness_days'] if len(profiles)==1 else 0
            # The retained decision cannot be eligible indefinitely between evaluations.
            if changed:status='STALE';reason='REFERENCES_CHANGED'
            elif now>e.evaluated_at+timedelta(days=age):status='STALE';reason='SCREENING_EXPIRED'
            elif any(now>=__import__('datetime').datetime.fromisoformat(w['expires_at'].replace('Z','+00:00')) for w in c['finance_v3'].get('waivers',[])):
                status='STALE';reason='WAIVER_EXPIRED'
            from app.db.finance_models import FinanceAllocation
            owned=session.scalars(scope_query(select(FinanceAllocation),FinanceAllocation,identity).where(FinanceAllocation.evaluation_id==e.id)).all()
            lifecycle=finance_ledger.states(session,identity,owned)
            if not owned or any(lifecycle.get(a.id)!='RESERVED' for a in owned):status='STALE';reason='ACTIVE_RESERVATION_REQUIRED'
            budget=refs.get(p.get('budget_id'))
            if budget and Decimal(finance_ledger.balance(session,identity,budget)['available'])<0:status='STALE';reason='BUDGET_REVALIDATION_REQUIRED'
            eligible=status=='CURRENT'
    return {'current_eligible':eligible,'evaluation_status':status,'eligibility_reason':reason,'current_version':t.latest_version}

def report_view(session,identity,evaluation_id):
    e=finance.get(session,Evaluation,identity,evaluation_id);t=finance.get(session,Transaction,identity,e.transaction_id)
    r=session.scalar(scope_query(select(Report),Report,identity).where(Report.evaluation_id==e.id))
    if not r:raise DomainError(503,'REPORT_UNAVAILABLE','The retained report needs operational reconciliation.',retryable=False)
    return finance.authorized_report(identity,r.content)|eligibility(session,identity,t,e)|{'suggested_actions':next_actions(r.content['rules']),'current_eligibility_as_of':utcnow().isoformat()}

def review_queue(session,identity,*,decision=None,branch=None,reason=None,minimum_age_days=0,owner=None,state=None,processing_state=None,minimum_amount=None,maximum_amount=None,limit=50,offset=0):
    if 'EMPLOYEE' not in identity.roles:read_permission(identity)
    def amount_filter(raw):
        from app.schemas.canonical import decimal_text
        try:return Decimal(decimal_text(raw))
        except ValueError:raise DomainError(400,'FILTER_INVALID','Amount filters require exact decimal strings.') from None
    if not 1<=limit<=100 or offset<0 or offset>100000 or not 0<=minimum_age_days<=3650:raise DomainError(400,'FILTER_INVALID','Use bounded pagination and age filters.')
    if decision and decision not in ('PASS','REVIEW','HOLD') or branch and branch not in ('VENDOR_INVOICE','EMPLOYEE_EXPENSE') or state and state not in (*OPEN,'RESOLVED','CANCELLED','SUPERSEDED'):raise DomainError(400,'FILTER_INVALID','Unknown workflow filter.')
    q=scope_query(select(ReviewCase,TransactionVersion).join(Evaluation,Evaluation.id==ReviewCase.evaluation_id).join(Transaction,Transaction.id==ReviewCase.transaction_id).join(TransactionVersion,and_(TransactionVersion.transaction_id==ReviewCase.transaction_id,TransactionVersion.version==Evaluation.transaction_version)),ReviewCase,identity)
    q=q.where(ReviewCase.state==state if state else ReviewCase.state.in_(OPEN),ReviewCase.created_at<=utcnow()-timedelta(days=minimum_age_days))
    if 'EMPLOYEE' in identity.roles and not {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER'}&identity.roles:q=q.where(TransactionVersion.party_id==identity.actor_id)
    if decision:q=q.where(ReviewCase.decision==decision)
    if branch:q=q.where(ReviewCase.branch==branch)
    if reason:q=q.where(cast(ReviewCase.reasons,JSONB).contains([reason]))
    if owner=='unassigned':q=q.where(ReviewCase.owner_id.is_(None))
    elif owner:
        try:target=identity.actor_id if owner=='me' else UUID(owner)
        except ValueError:raise DomainError(400,'FILTER_INVALID','Unknown reviewer filter.') from None
        q=q.where(ReviewCase.owner_id==target)
    if processing_state:
        if processing_state not in ('RECEIVED','QUEUED','PROCESSING','COMPLETED','FAILED_RETRYABLE','FAILED_FINAL','CANCELLED'):raise DomainError(400,'FILTER_INVALID','Unknown processing state.')
        q=q.where(Transaction.processing_state==processing_state)
    if minimum_amount is not None and maximum_amount is not None:
        if amount_filter(minimum_amount)>amount_filter(maximum_amount):raise DomainError(400,'FILTER_INVALID','Minimum amount must not exceed maximum amount.')
    for amount,operator in [(minimum_amount,'min'),(maximum_amount,'max')]:
        if amount is None:continue
        parsed=amount_filter(amount)
        q=q.where(TransactionVersion.total_amount>=parsed if operator=='min' else TransactionVersion.total_amount<=parsed)
    rows=session.execute(q.order_by(ReviewCase.created_at,ReviewCase.id).offset(offset).limit(limit+1)).all()
    items=[]
    for r,v in rows[:limit]:
        items.append(reviews_view(session,identity,r)|{'display_number':v.payload.get('invoice_number') or v.payload.get('claim_number'),'amount':projection(v.total_amount),'currency':v.currency,'next_actions':[{'rule_id':key,'action':NEXT.get(key,('REVIEW_REQUIRED_CONTROL','Resolve the required control'))[0],'label':NEXT.get(key,('REVIEW_REQUIRED_CONTROL','Resolve the required control'))[1]} for key in r.reasons]})
    return {'items':items,'next_offset':offset+limit if len(rows)>limit else None}

def reviews_view(session,identity,r):
    from app.services.reviews import view
    return view(session,identity,r)

def review_history(session,identity,transaction_id):
    if 'EMPLOYEE' not in identity.roles:read_permission(identity)
    t=finance.get(session,Transaction,identity,transaction_id)
    rows=session.scalars(scope_query(select(ReviewCase),ReviewCase,identity).where(ReviewCase.transaction_id==t.id).order_by(ReviewCase.created_at.desc()).limit(100)).all()
    actions=session.scalars(scope_query(select(ReviewAction),ReviewAction,identity).where(ReviewAction.review_case_id.in_([r.id for r in rows])).order_by(ReviewAction.created_at).limit(200)).all() if rows else []
    return {'items':[reviews_view(session,identity,r) for r in rows],
        'actions':projection([{'id':a.id,'review_case_id':a.review_case_id,'action':a.action,'actor_id':a.actor_id,'reason_code':a.reason_code,'comment':a.comment,'transaction_version':a.transaction_version,'review_version':a.review_version,'evidence':a.evidence,'details':finance.redact(a.details),'created_at':a.created_at} for a in actions])}

def timeline(session,identity,transaction_id,after=0,limit=50):
    read_permission(identity);finance.get(session,Transaction,identity,transaction_id)
    if not 1<=limit<=100 or after<0:raise DomainError(400,'FILTER_INVALID','Use bounded timeline pagination.')
    from app.db.finance_models import ApprovalRequest,Waiver,FinanceAllocation,DuplicateComparison,DuplicateResolution,ReceiptShare
    ids=[select(m.id).where(m.transaction_id==transaction_id) for m in (Evaluation,ReviewCase,Job,ApprovalRequest,Waiver,FinanceAllocation,DuplicateComparison,ReceiptShare)]
    ids.extend([select(DuplicateResolution.id).where(DuplicateResolution.comparison_id.in_(select(DuplicateComparison.id).where(DuplicateComparison.transaction_id==transaction_id))),
        select(OperationRecord.id).where(OperationRecord.object_id.in_(select(Evaluation.id).where(Evaluation.transaction_id==transaction_id)))])
    docs=select(TransactionDocument.document_id).where(TransactionDocument.transaction_id==transaction_id)
    q=scope_query(select(AuditEvent),AuditEvent,identity).where(AuditEvent.sequence>after,
        or_(AuditEvent.object_id==transaction_id,AuditEvent.object_id.in_(docs),*(AuditEvent.object_id.in_(q) for q in ids),AuditEvent.payload['transaction_id'].as_string()==str(transaction_id)))
    rows=session.scalars(q.order_by(AuditEvent.sequence).limit(limit+1)).all()
    return {'items':projection([{'id':r.id,'sequence':r.sequence,'action':r.action,'actor_id':r.actor_id,'created_at':r.created_at,'version':r.object_version,'reason':r.reason,'object_id':r.object_id,'evidence':{k:v for k,v in r.payload.items() if k in ('evaluation_id','document_id','superseded_by','transaction_version','reason_code','state')}} for r in rows[:limit]]),'next_sequence':rows[limit-1].sequence if len(rows)>limit else None}

def dashboard(session,identity):
    read_permission(identity);now=utcnow()
    counts=dict(session.execute(scope_query(select(Transaction.decision,func.count()).group_by(Transaction.decision),Transaction,identity)).all())
    q=scope_query(select(ReviewCase),ReviewCase,identity).where(ReviewCase.state.in_(OPEN))
    oldest=session.scalar(q.order_by(ReviewCase.created_at).limit(1))
    by_state=dict(session.execute(scope_query(select(ReviewCase.state,func.count()).group_by(ReviewCase.state),ReviewCase,identity).where(ReviewCase.state.in_(OPEN))).all())
    by_branch=dict(session.execute(scope_query(select(ReviewCase.branch,func.count()).group_by(ReviewCase.branch),ReviewCase,identity).where(ReviewCase.state.in_(OPEN))).all())
    by_owner=[{'owner_id':str(owner) if owner else None,'count':count} for owner,count in session.execute(scope_query(select(ReviewCase.owner_id,func.count()).group_by(ReviewCase.owner_id),ReviewCase,identity).where(ReviewCase.state.in_(OPEN))).all()]
    reason_q=scope_query(select(ReviewCase.reasons),ReviewCase,identity).where(ReviewCase.state.in_(OPEN)).subquery()
    reasons=select(func.jsonb_array_elements_text(cast(reason_q.c.reasons,JSONB)).label('reason')).subquery()
    by_reason=dict(session.execute(select(reasons.c.reason,func.count()).group_by(reasons.c.reason)).all())
    failures={}
    for model,label in [(Job,'finance'),(DocumentJob,'document')]:failures[label]=dict(session.execute(scope_query(select(model.state,func.count()).group_by(model.state),model,identity).where(model.state.in_(['FAILED','RETRYABLE']))).all())
    recent=session.scalars(scope_query(select(AuditEvent),AuditEvent,identity).where(AuditEvent.action.like('REVIEW_%')).order_by(AuditEvent.sequence.desc()).limit(10)).all()
    return projection({'counts':{k or 'PENDING':v for k,v in counts.items()},'open_cases':sum(by_state.values()),'oldest_case_id':oldest.id if oldest else None,'oldest_age_seconds':max(0,(now-oldest.created_at).total_seconds()) if oldest else None,'by_state':by_state,'by_branch':by_branch,'by_owner':by_owner,'by_reason':by_reason,'failures':failures,'recent_activity':[{'action':r.action,'reason':r.reason,'actor_id':r.actor_id,'created_at':r.created_at} for r in recent],'measured_at':now})

def job_view(row,kind):
    state={'RUNNING':'PROCESSING','RETRYABLE':'FAILED_RETRYABLE','FAILED':'DEAD_LETTER','SUCCEEDED':'COMPLETED'}.get(row.state,row.state)
    return projection({'id':row.id,'kind':kind,'state':state,'stored_state':row.state,'stage':row.stage,'attempts':row.attempts,'maximum_attempts':row.maximum_attempts,'retryable':row.failure_retryable,'manual_retries':row.manual_retries,'first_failure_at':row.first_failure_at,'last_failure_at':row.last_failure_at,'last_error':row.last_error,'transaction_id':getattr(row,'transaction_id',None),'document_id':getattr(row,'document_id',None),'correlation_id':getattr(row,'correlation_id',str(row.id)),'updated_at':row.updated_at})

def jobs(session,identity,state,limit,offset):
    read_permission(identity)
    if not 1<=limit<=100 or not 0<=offset<=100000:raise DomainError(400,'FILTER_INVALID','Use bounded pagination.')
    items=[];has_more=False
    for model,kind in [(Job,'finance'),(DocumentJob,'document')]:
        rows=session.scalars(scope_query(select(model),model,identity).where(model.state==state).order_by(model.updated_at.desc(),model.id).offset(offset).limit(limit+1)).all()
        has_more=has_more or len(rows)>limit
        items.extend(job_view(r,kind) for r in rows[:limit])
    items.sort(key=lambda r:(r['updated_at'],r['id']),reverse=True)
    # Separate per-queue offsets preserve coverage across both durable queues.
    return {'items':items,'next_offset':offset+limit if has_more else None}

def classify_failure(exc):
    from sqlalchemy.exc import DBAPIError, OperationalError
    if isinstance(exc,DomainError):return exc.code,exc.retryable
    if isinstance(exc,(TimeoutError,ConnectionError)):return 'DEPENDENCY_TIMEOUT',True
    if isinstance(exc,OperationalError):return 'DATABASE_UNAVAILABLE',True
    if isinstance(exc,DBAPIError):return 'DATABASE_CONFLICT',getattr(exc.orig,'sqlstate',None) in ('40P01','40001','55P03')
    if isinstance(exc,(ValueError,TypeError)):return 'UNSUPPORTED_INPUT_SCHEMA',False
    if isinstance(exc,FileNotFoundError):return 'STORAGE_ARTIFACT_MISSING',False
    return 'EXECUTION_FAILED',True

def mark_failure(row,code,retryable,now):
    row.failure_retryable=retryable;row.first_failure_at=row.first_failure_at or now;row.last_failure_at=now
    row.last_error=code;row.state='RETRYABLE' if retryable and row.attempts<row.maximum_attempts else 'FAILED'
    row.lease_until=None;row.updated_at=now
    # Stable bounded jitter avoids synchronized retries without affecting finance replay.
    jitter=int(digest(str(row.id))[:2],16)/255
    row.available_at=now+timedelta(seconds=min(60,2**row.attempts)+jitter)

def retry(session,identity,kind,job_id,data,correlation):
    from app.services.reviews import require
    require(identity,'OPERATIONS_ADMIN');finance.scope_lock(session,identity)
    model=Job if kind=='finance' else DocumentJob;row=finance.get(session,model,identity,job_id)
    if row.attempts!=data['expected_attempts']:raise DomainError(409,'STALE_JOB_ATTEMPT','Job attempts changed; refresh operational details.')
    if row.state not in ('FAILED','RETRYABLE') or not row.failure_retryable or row.manual_retries>=2:
        raise DomainError(409,'RETRY_NOT_PERMITTED','Resolve permanent input failures; only bounded retryable failures may be retried.')
    if kind=='finance':
        t=finance.get(session,Transaction,identity,row.transaction_id);finance.require_active(t)
        if t.latest_version!=row.transaction_version or t.row_version!=row.generation:raise DomainError(409,'JOB_SUPERSEDED','A newer transaction or evaluation request superseded this job.')
        t.processing_state='QUEUED';t.eligible=False
    else:
        d=finance.get(session,Document,identity,row.document_id)
        if d.generation!=row.generation or d.state=='QUARANTINED':raise DomainError(409,'JOB_SUPERSEDED','This document stage cannot be retried.')
        d.state='QUEUED'
    row.manual_retries+=1;row.maximum_attempts=max(row.maximum_attempts,row.attempts+3);row.state='QUEUED';row.available_at=utcnow();row.lease_owner=None;row.lease_until=None
    operation(session,identity,'JOB_MANUAL_RETRY',row.id,{'job':row.id,'manual_retry':row.manual_retries}, {'kind':kind,'attempts':row.attempts,'manual_retry':row.manual_retries},data['reason'],correlation)
    return job_view(row,kind)

def dependencies(database,storage,settings,identity):
    db_state='AVAILABLE'
    risk_status='UNKNOWN'
    try:
        with database.session(identity) as s:
            s.execute(text('SELECT 1'))
            from app.services.intelligence import deployment,load_artifact
            from app.db.risk_models import ModelVersion
            current=deployment(s,identity)
            risk_status='NOT_CONFIGURED' if not current or current.mode=='RULES_ONLY' else 'MODEL_UNAVAILABLE'
            if current and current.model_id and current.mode!='RULES_ONLY':
                try:load_artifact(s,identity,finance.get(s,ModelVersion,identity,current.model_id));risk_status='AVAILABLE'
                except (ValueError,OSError,DomainError):pass
    except Exception:db_state='UNAVAILABLE'
    storage_state='AVAILABLE' if storage.root.is_dir() and __import__('os').access(storage.root,__import__('os').R_OK|__import__('os').W_OK) else 'UNAVAILABLE'
    return {'database':db_state,'storage':storage_state,'job_executor':'DATABASE_LEASED_POLLING',
        'ocr':'CONFIGURED' if settings.document_providers.ocr_executable else 'NOT_CONFIGURED',
        'enterprise_vlm':'CONFIGURED_UNVERIFIED' if settings.document_providers.endpoint else 'NOT_CONFIGURED',
        'enterprise_runtime':'DEFERRED_EXTERNAL_PREREQUISITE','malware':'NOT_CONFIGURED','risk_model':risk_status}

def replay(session,identity,evaluation_id,correlation):
    read_permission(identity);finance.scope_lock(session,identity)
    e=finance.get(session,Evaluation,identity,evaluation_id)
    stored=session.scalar(scope_query(select(EvaluationInput),EvaluationInput,identity).where(EvaluationInput.evaluation_id==e.id))
    if not stored or digest(stored.encoded)!=e.input_digest or stored.content_digest!=e.input_digest:raise DomainError(409,'REPLAY_INPUT_INTEGRITY','Pinned input is unavailable or fails its digest.')
    from app.rules.engine import RuleContext,RULESET
    from app.rules.finance_phase3 import evaluate
    from app.rules.import_evidence import mapped_evidence
    if e.ruleset_version not in (RULESET,'rules-p3-v1'):raise DomainError(409,'REPLAY_RULESET_UNAVAILABLE','The retained ruleset is not available in this runtime.')
    c=json.loads(stored.encoded);decision=mapped_evidence(evaluate(RuleContext(stored.encoded)),c)
    from app.services.intelligence import replay as replay_intelligence
    decision=replay_intelligence(session,identity,e,decision)
    actual={'decision':decision.decision,'completeness':decision.completeness,'eligible':decision.eligible,'rules':sorted([r.json() for r in decision.results],key=lambda r:r['rule_id'])}
    rows=session.scalars(scope_query(select(RuleResultRow),RuleResultRow,identity).where(RuleResultRow.evaluation_id==e.id)).all()
    expected={'decision':e.decision,'completeness':e.completeness,'eligible':e.eligible,'rules':sorted([r.result for r in rows],key=lambda r:r['rule_id'])}
    details={'evaluation_id':str(e.id),'input_digest':e.input_digest,'expected_digest':digest(expected),'replayed_digest':digest(actual),'matches':digest(expected)==digest(actual),'ruleset':e.ruleset_version,'evaluated_at':e.evaluated_at.isoformat(),'extraction_reexecuted':False}
    operation(session,identity,'AUDIT_REPLAY',e.id,{'evaluation':e.id,'result_digest':digest(actual)},details,'Pinned rules-only inputs replayed',correlation)
    return details

def csv_safe(value):
    raw=str(value) if value is not None else ''
    return "'"+raw if raw.lstrip().startswith(('=','+','-','@','\t','\r','\n')) or raw.startswith(('\t','\r','\n')) else raw

def render_export(content,format):
    if format=='json':return canonical_json(content).encode(),'application/json'
    if format=='html':return finance.report_html(content).encode(),'text/html'
    stream=io.StringIO(newline='');writer=csv.writer(stream)
    writer.writerow(['Transaction','Version','Decision at evaluation','Current eligibility','Evaluation status','Rule','Status','Reason'])
    for rule in content['rules']:writer.writerow([csv_safe(v) for v in [content['transaction_id'],content['transaction_version'],content['decision'],content['current_eligible'],content['evaluation_status'],rule['rule_id'],rule['status'],rule['reason']]])
    return stream.getvalue().encode(),'text/csv'

def export_permission(identity):
    if not {'AUDITOR','REPORT_EXPORTER'}&identity.roles:raise DomainError(403,'EXPORT_FORBIDDEN','Explicit report export permission is required.')

def prepare_export(session,identity,evaluation_id,format,correlation):
    export_permission(identity);content=report_view(session,identity,evaluation_id)
    data,media=render_export(content,format)
    row=operation(session,identity,'REPORT_EXPORT_GENERATED',evaluation_id,
        {'evaluation':evaluation_id,'actor':identity.actor_id,'format':format,'digest':digest(content)},
        {'evaluation_id':str(evaluation_id),'format':format,'content':content,'sha256':__import__('hashlib').sha256(data).hexdigest(),'media_type':media},'Authorized report export generated',correlation)
    return {'id':str(row.id),'format':format,'download_url':'/api/v1/exports/'+str(row.id),'sha256':row.details['sha256']}

def download(session,identity,export_id,correlation):
    export_permission(identity);row=finance.get(session,OperationRecord,identity,export_id)
    if row.kind!='REPORT_EXPORT_GENERATED':raise DomainError(404,'EXPORT_UNAVAILABLE','Export is unavailable.')
    finance.get(session,Evaluation,identity,UUID(row.details['evaluation_id']))
    # The export is an immutable authorized snapshot; its eligibility timestamp remains explicit.
    data,media=render_export(row.details['content'],row.details['format'])
    if __import__('hashlib').sha256(data).hexdigest()!=row.details['sha256']:raise DomainError(409,'EXPORT_INTEGRITY','Export integrity check failed.')
    finance.audit(session,identity,'REPORT_EXPORT_ACCESSED',row.id,1,'Authorized report download',correlation)
    return data,media,'screening-'+str(row.object_id)+'.'+row.details['format']

def reconcile(session,identity,storage,reason,correlation):
    from app.services.reviews import require
    from app.services import finance_ledger
    require(identity,'OPERATIONS_ADMIN');finance.scope_lock(session,identity);now=utcnow();findings=[]
    def finding(code,oid,state,details=None):
        item={'code':code,'object_id':str(oid),'status':state}|(details or {})
        operation(session,identity,'RECONCILIATION',oid,{'code':code,'object':oid,'details':details},item,reason,correlation)
        findings.append(item)
    for model,parent,kind in [(Job,Transaction,'finance'),(DocumentJob,Document,'document')]:
        rows=session.scalars(scope_query(select(model),model,identity).where(model.state=='RUNNING',model.lease_until<=now).order_by(model.created_at).limit(100)).all()
        for row in rows:
            mark_failure(row,'LEASE_EXPIRED',True,now)
            owner=finance.get(session,parent,identity,row.transaction_id if kind=='finance' else row.document_id)
            if kind=='finance' and owner.processing_state=='CANCELLED':row.state='CANCELLED'
            elif kind=='finance' and owner.row_version==row.generation and owner.latest_version==row.transaction_version:owner.processing_state='FAILED_RETRYABLE' if row.state=='RETRYABLE' else 'FAILED_FINAL';owner.eligible=False
            elif kind=='document' and owner.generation==row.generation:owner.state='FAILED_RETRYABLE' if row.state=='RETRYABLE' else 'NEEDS_INPUT'
            finding('STALE_LEASE',row.id,'REPAIRED',{'attempt':row.attempts,'kind':kind})
    for t in session.scalars(scope_query(select(Transaction),Transaction,identity).where(Transaction.processing_state=='CANCELLED').limit(100)):
        live=[a for a,state in finance_ledger.active(session,identity) if a.transaction_id==t.id and state=='RESERVED']
        legacy=session.scalars(scope_query(select(CapacityReservation),CapacityReservation,identity).where(CapacityReservation.transaction_id==t.id,CapacityReservation.state=='ACTIVE')).all()
        if live or legacy:
            finance.release(session,identity,t.id)
            finding('CANCELLED_RESERVATION',t.id,'REPAIRED',{'allocations':[str(a.id) for a in live],'legacy_reservations':[str(a.id) for a in legacy]})
    # Mark delayed local notifications delivered only when a retained completed effect proves consumption.
    for model,jmodel in [(OutboxEvent,Job),(DocumentOutbox,DocumentJob)]:
        rows=session.scalars(scope_query(select(model).join(jmodel,jmodel.id==model.job_id),model,identity).where(model.delivered_at.is_(None),jmodel.state=='SUCCEEDED').limit(100)).all()
        for row in rows:row.delivered_at=now;finding('DELAYED_OUTBOX',row.id,'REPAIRED')
    completed=session.scalars(scope_query(select(Job),Job,identity).where(Job.state=='SUCCEEDED').order_by(Job.created_at.desc()).limit(100)).all()
    for row in completed:
        e=finance.get(session,Evaluation,identity,row.result_evaluation_id);t=finance.get(session,Transaction,identity,row.transaction_id)
        if t.processing_state!='CANCELLED' and t.latest_version==row.transaction_version and t.row_version in (row.generation,row.generation+1) and t.latest_evaluation_id!=e.id:
            # Require fresh admission; never restore eligibility from a historical PASS.
            finance.enqueue(session,identity,t.id,t.latest_version,'Projection reconciliation requires fresh admission',correlation,'reconcile-projection:'+str(row.id))
            finding('COMPLETED_PROJECTION_MISSING',row.id,'REPAIRED_REEVALUATION_QUEUED')
        report=session.scalar(scope_query(select(Report),Report,identity).where(Report.evaluation_id==e.id))
        if not report:finding('REPORT_MISSING',e.id,'UNRESOLVED_RETAINED_ARTIFACT_REQUIRED')
    uploads=session.scalars(scope_query(select(UploadSession),UploadSession,identity).where(UploadSession.state=='UPLOADED').order_by(UploadSession.created_at).limit(100)).all()
    for row in uploads:
        # Bytes alone do not prove user finalization intent or safety. Preserve them for completion.
        finding('UPLOAD_AWAITING_FINALIZATION',row.id,'NEEDS_USER_FINALIZATION')
    pages=session.scalars(scope_query(select(DocumentPage),DocumentPage,identity).order_by(DocumentPage.created_at.desc()).limit(100)).all()
    for row in pages:
        if not storage.path(identity,row.preview_key).is_file():finding('PAGE_ARTIFACT_MISSING',row.id,'UNRESOLVED_SOURCE_REPAIR_REQUIRED')
    originals=session.scalars(scope_query(select(DocumentVersion),DocumentVersion,identity).limit(100)).all()
    for row in originals:
        if not storage.path(identity,row.storage_key).is_file():finding('ORIGINAL_ARTIFACT_MISSING',row.id,'UNRESOLVED_ORIGINAL_REQUIRED')
    # Inspect a bounded scoped directory; never delete evidence or guess retained object ownership.
    directory=storage.root/str(identity.tenant_id)/str(identity.legal_entity_id)
    inspected=[]
    if directory.is_dir():
        for index,path in enumerate(directory.iterdir()):
            if index>=1000:findings.append({'code':'STORAGE_INSPECTION_BOUND','status':'INCOMPLETE'});break
            if path.is_file() and not path.is_symlink():inspected.append(path)
    keys=[str(path.relative_to(storage.root)) for path in inspected];known=set()
    for model,column in [(DocumentVersion,DocumentVersion.storage_key),(DocumentPage,DocumentPage.preview_key),(UploadSession,UploadSession.storage_key),(ImportBatch,ImportBatch.object_key)]:
        if keys:known.update(session.scalars(scope_query(select(column),model,identity).where(column.in_(keys))))
    for path,key in zip(inspected,keys):
        if key not in known:
            try:oid=UUID(path.name)
            except ValueError:continue
            finding('ORPHAN_STORAGE_OBJECT',oid,'PRESERVED_NEEDS_RETENTION_DECISION')
    session.flush()
    return {'findings':findings,'limit_per_category':100,'storage_inspection_limit':1000,'coverage':'BOUNDED_LOCAL_INSPECTION','measured_at':now.isoformat()}
