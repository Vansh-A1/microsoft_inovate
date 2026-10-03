"""Pinned Phase-3 orchestration; pure rules receive no live database handles."""
from datetime import date,timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy import select,or_
from app.core.errors import DomainError
from app.core.serialization import projection,utcnow
from app.db.models import Transaction,TransactionVersion,CapacityReservation,ReferenceRecord
from app.db.finance_models import ReceiptShare,Waiver,DuplicateComparison,DuplicateResolution,FinanceAllocation
from app.db.session import scope_query
from app.services import finance_ledger as ledger,approvals,duplicates
from app.services.reference_imports import effective
D=Decimal
Z=D('0')


def augment(session,identity,version,data):
    refs=data['references'];profiles=[r for r in refs.values() if r.get('_kind')=='finance_profiles']
    if not profiles:return data
    p=version.payload;day=p.get('invoice_date' if p['branch']=='VENDOR_INVOICE' else 'expense_date');current=[r for r in profiles if effective(r,day)]
    if len(current)!=1:raise DomainError(409,'FINANCE_PROFILE_AMBIGUOUS','Exactly one effective finance-control profile is required.')
    profile=current[0]
    from app.integrations.blob_storage import configured_storage
    settings=session.info.get('settings')
    # Runtime storage is only used to fingerprint actual already-safe previews.
    if settings:
        documents={UUID(s) for s in [p.get('source_document_id')]+[i.get('source_document_id') for i in p['items']] if s}
        storage=configured_storage(settings)
        for did in documents:duplicates.ensure_fingerprints(session,identity,did,storage)
    comparisons,coverage=duplicates.search(session,identity,version,profile)
    all_allocations=ledger.active(session,identity,exclude=version.transaction_id)
    allocations=projection([{'id':r.id,'version':1,'resource_id':r.resource_id,'kind':r.kind,'amount':r.amount,'quantity':r.quantity,'currency':r.currency,'state':state,'transaction_id':r.transaction_id,'transaction_version':r.transaction_version,'metadata':r.metadata_json} for r,state in all_allocations])
    # Minimal Phase-1 admissions remain valid when a new control profile activates.
    legacy=session.scalars(scope_query(select(CapacityReservation),CapacityReservation,identity).where(CapacityReservation.state=='ACTIVE',CapacityReservation.transaction_id!=version.transaction_id)).all()
    allocations+=projection([{'id':r.id,'version':1,'resource_id':r.reference_id,'kind':r.kind,'amount':r.amount,'quantity':r.quantity,'currency':r.currency,'state':'RESERVED','transaction_id':r.transaction_id,'transaction_version':r.transaction_version,'metadata':{'commercial_id':refs.get(str(r.reference_id),{}).get('po_id')}} for r in legacy])
    budget=refs.get(str(p.get('budget_id')));balance=ledger.balance(session,identity,budget,exclude=version.transaction_id,po_id=p.get('po_id')) if budget and budget.get('_kind')=='budgets' else None
    if balance:
        old_reserved=sum((r.amount for r in legacy if r.kind=='BUDGET' and str(r.reference_id)==budget['id']),Z)
        old_coverage=sum((r.amount for r in legacy if r.kind=='PO_LINE' and refs.get(str(r.reference_id),{}).get('po_id')==p.get('po_id')),Z)
        balance['active_reservations']=str(D(balance['active_reservations'])+old_reserved);balance['available']=str(D(balance['available'])-old_reserved);balance['po_commitment_coverage']=str(max(Z,D(balance['po_commitment_coverage'])-old_coverage))
    shares=session.scalars(scope_query(select(ReceiptShare),ReceiptShare,identity).where(ReceiptShare.transaction_id==version.transaction_id,ReceiptShare.transaction_version==version.version)).all()
    shares=projection([{'id':r.id,'version':1,'document_id':r.document_id,'item_id':r.item_id,'employee_id':r.employee_id,'amount':r.amount,'quantity':r.quantity,'reason':r.reason,'actor_id':r.actor_id} for r in shares])
    receipt_usage=[r for r in allocations if r['kind']=='RECEIPT']
    payments=[r for r in refs.values() if r.get('_kind')=='company_payments' and r.get('employee_id')==p.get('employee_id')]
    delegation=approvals.delegation(refs,p.get('employee_id'),str(version.author_id),p,day,'SUBMIT') if p.get('employee_id') else None
    preapprovals=[]
    for r in refs.values():
        if r.get('_kind')!='preapprovals' or r.get('employee_id')!=p.get('employee_id'):continue
        actor=refs.get(r.get('approver_id'),{})
        if (r.get('status')=='APPROVED' and effective(r,day) and r.get('approved_date','9999-12-31')<=day
            and r.get('currency')==p.get('currency') and r.get('category')==p.get('category')
            and r.get('cost_center_id')==p.get('cost_center_id') and D(r['ceiling_amount'])>=D(p.get('requested_amount') or '0')
            and actor.get('status')=='ACTIVE' and effective(actor,r['approved_date']) and 'PREAPPROVER' in actor.get('roles',[])
            and actor.get('cost_center_id')==p.get('cost_center_id') and actor.get('id') not in (p.get('employee_id'),str(version.author_id))):preapprovals.append(r)
    employee=p.get('employee_id');aggregates={};split=None
    if employee and day:
        facts=[]
        q=scope_query(select(TransactionVersion,Transaction).join(Transaction,Transaction.id==TransactionVersion.transaction_id),TransactionVersion,identity).where(TransactionVersion.party_id==UUID(employee),TransactionVersion.currency==p.get('currency'),TransactionVersion.transaction_id!=version.transaction_id,TransactionVersion.version==Transaction.latest_version,Transaction.processing_state.not_in(['CANCELLED','REVERSED','FAILED_FINAL']),or_(TransactionVersion.business_date.between(date.fromisoformat(day).replace(day=1),date.fromisoformat(day)),TransactionVersion.payload['trip_reference'].as_string()==p['trip_reference'] if p.get('trip_reference') else False)).limit(1001)
        rows=session.execute(q).all()
        if len(rows)>1000:raise DomainError(503,'EXPENSE_AGGREGATE_LIMIT','Expense aggregation requires narrower dimensions.')
        for fact,t in rows:
            if fact.payload.get('category')!=p.get('category') or fact.payload.get('local_timezone')!=p.get('local_timezone'):continue
            facts.append({'id':str(fact.transaction_id),'version':fact.version,'amount':str(sum((D(i['claimed_amount']) for i in fact.payload['items'] if i.get('claimed_amount') is not None),Z)),'expense_date':fact.payload.get('expense_date'),'trip_reference':fact.payload.get('trip_reference'),'merchant':fact.payload.get('merchant'),'expense_policy_id':fact.payload.get('expense_policy_id'),'active':t.eligible or t.processing_state in ('QUEUED','PROCESSING')})
        current=sum((D(i['claimed_amount']) for i in p['items'] if i.get('claimed_amount') is not None),Z)
        active=[r for r in facts if r['active'] and r['expense_policy_id']==p.get('expense_policy_id')]
        aggregates['ITEM']={'amount':str(max((D(i['claimed_amount']) for i in p['items'] if i.get('claimed_amount')),default=Z)),'related_ids':[]}
        if p.get('trip_reference'):
            trip=[r for r in active if r['trip_reference']==p['trip_reference']];aggregates['TRIP']={'amount':str(current+sum((D(r['amount']) for r in trip),Z)),'related_ids':[r['id'] for r in trip]}
        monthly=[r for r in active if r['expense_date'][:7]==day[:7]]
        aggregates['MONTH']={'amount':str(current+sum((D(r['amount']) for r in monthly),Z)),'related_ids':[r['id'] for r in monthly]}
        policy=refs.get(str(p.get('expense_policy_id')));threshold=policy and policy.get('split_threshold_amount');fraction=policy and policy.get('split_near_fraction','0.8')
        if threshold and p.get('merchant'):
            related=[r for r in active if r['merchant']==p['merchant'] and r['trip_reference']==p.get('trip_reference') and r['expense_date']==day and D(r['amount'])>=D(threshold)*D(fraction) and D(r['amount'])<=D(threshold)]
            if related and D(threshold)*D(fraction)<=current<=D(threshold) and current+sum((D(r['amount']) for r in related),Z)>D(threshold):split={'threshold':threshold,'near_fraction':fraction,'aggregate':str(current+sum((D(r['amount']) for r in related),Z)),'related_records':related,'related_ids':[r['id'] for r in related],'dimensions':{'employee_id':employee,'merchant':p['merchant'],'category':p['category'],'trip_reference':p.get('trip_reference'),'local_date':day}}
        # Extend daily aggregation with active Phase-3 admissions; exclude legacy rows already present.
        existing={r['id'] for r in data['daily_history']}
        data['daily_history'] += [{'id':r['id'],'version':r['version'],'claimed_amount':r['amount']} for r in active if r['expense_date']==day and r['id'] not in existing]
    waiver_rows=session.scalars(scope_query(select(Waiver),Waiver,identity).where(Waiver.transaction_id==version.transaction_id,Waiver.transaction_version==version.version,Waiver.expires_at>utcnow())).all()
    waivers=projection([{'id':r.id,'rule_id':r.rule_id,'rule_version':r.rule_version,'actor_id':r.actor_id,'reason':r.reason,'expires_at':r.expires_at,'evidence_ids':r.evidence,'policy_id':r.policy_id,'policy_version':r.policy_version} for r in waiver_rows])
    stale=[]
    for r in refs.values():
        if r.get('imported_at'):
            from datetime import datetime
            imported=datetime.fromisoformat(r['imported_at']);cutoff=datetime.fromisoformat(data['evaluated_at'].replace('Z','+00:00'))
            if cutoff-imported>timedelta(days=profile['freshness_days']):stale.append(r['id'])
    authenticated_roles=set()
    if settings:
        accounts=settings.identities.values() if settings.development else (a for a in settings.enterprise_identity.get('memberships',{}).values() if a.get('enabled',False))
        for account in accounts:
            if account['actor_id']==str(version.author_id) and account['tenant_id']==str(identity.tenant_id) and account['legal_entity_id']==str(identity.legal_entity_id):authenticated_roles.update(account['roles'])
    else:authenticated_roles=set(identity.roles)
    from app.services.reference_imports import active_records
    current_master=active_records(session,identity).get(str(p.get('vendor_id'))) if p.get('vendor_id') else None
    restriction=current_master.payload|{'_kind':current_master.kind} if current_master else None
    if restriction:refs['_current_vendor:'+restriction['id']]=restriction
    v={'profile':profile,'duplicates':comparisons,'duplicate_coverage':coverage,'allocations':allocations,'budget':balance,'approval':approvals.state(session,identity,version,refs),'receipt_shares':shares,'receipt_usage':receipt_usage,'company_payments':payments,'submission_delegation':delegation,'finance_submission_authorized':'FINANCE_SUBMITTER' in authenticated_roles,'aggregates':aggregates,'split_pattern':split,'waivers':waivers,'stale_references':stale,'current_vendor_restriction':restriction,'already_consumed':any(r.transaction_id==version.transaction_id and state=='CONSUMED' for r,state in all_allocations)}
    v['verified_preapproval']=preapprovals[0] if len(preapprovals)==1 else None
    data['finance_v3']=v
    # Conditional authority is driven by computed facts, never a client-declared exception.
    if any(r.get('exception_roles') for r in refs.values() if r.get('_kind')=='approval_policies'):
        from app.rules.engine import RuleContext
        from app.rules.finance_phase3 import evaluate
        preliminary=evaluate(RuleContext.pin(**data))
        exceptions=[r.rule_id for r in preliminary.results if r.rule_id not in ('APR-001','APR-002') and r.status in ('FAIL','UNKNOWN','ERROR')]
        v['approval']=approvals.state(session,identity,version,refs,exceptions)
    return data


def reserve(session,identity,evaluation,version,context,decision):
    p=version.payload;refs=context['references'];v=context['finance_v3'];budget=refs[p['budget_id']];b=next(r for r in decision.results if r.rule_id=='BUD-001').observed
    total=D(p.get('total_amount' if p['branch']=='VENDOR_INVOICE' else 'requested_amount'));coverage=min(total,D(b['po_commitment_coverage']));incremental=D(b['incremental_exposure'])
    allocation=ledger.allocate(session,identity,evaluation,version,'BUDGET',budget['id'],incremental,'0',p['currency'],reference=budget,metadata={'commitment_coverage':str(coverage),'po_id':p.get('po_id'),'gross_budget_basis':str(total)})
    ledger.event(session,identity,budget,'RESERVATION',incremental,f'reserve:{allocation.id}','Atomic eligible budget admission',allocation=allocation,owner=str(version.transaction_id),metadata={'commitment_coverage':str(coverage)})
    if p['branch']=='VENDOR_INVOICE':
        rows=next(r for r in decision.results if r.rule_id=='PO-003').observed;groups={}
        for row in rows:
            for field,kind in [('commercial_line_id',row['allocation_kind']),('receipt_id',row['receipt_kind'])]:
                rid=row[field]
                if not rid:continue
                bucket=groups.setdefault((kind,rid),[Z,Z]);bucket[0]+=D(row['amount']);bucket[1]+=D(row['requested_quantity'])
        for (kind,rid),(amount,quantity) in groups.items():ledger.allocate(session,identity,evaluation,version,kind,rid,amount,quantity,p['currency'],reference=refs.get(rid),metadata={'commercial_id':p.get('po_id') or p.get('contract_id')})
    else:
        grouped={}
        for item in p['items']:
            bucket=grouped.setdefault(item['source_document_id'],Z);grouped[item['source_document_id']]=bucket+D(item['claimed_amount'])
        for did,amount in grouped.items():ledger.allocate(session,identity,evaluation,version,'RECEIPT',did,amount,'1',p['currency'],metadata={'employee_id':p['employee_id'],'share_ids':[s['id'] for s in v['receipt_shares'] if s['document_id']==did]})


def resolve_duplicate(session,identity,comparison_id,data,correlation):
    from app.services import finance
    from app.services.reference_imports import require
    require(identity,'DUPLICATE_REVIEWER');finance.scope_lock(session,identity);r=finance.get(session,DuplicateComparison,identity,comparison_id);t=finance.get(session,Transaction,identity,r.transaction_id)
    finance.require_active(t);finance.review_guard(session,identity,t,data)
    if t.latest_version!=data['expected_version'] or t.latest_version!=r.transaction_version:raise DomainError(409,'STALE_COMPARISON','Source transaction facts changed.')
    if r.candidate_type=='TRANSACTION':
        candidate=finance.get(session,Transaction,identity,r.candidate_id)
        if candidate.latest_version!=r.candidate_version:raise DomainError(409,'STALE_COMPARISON','Candidate facts changed; compare again.')
    if not data['evidence_ids']:raise DomainError(422,'RESOLUTION_EVIDENCE_REQUIRED','Cite existing source documents or compared transactions.')
    allowed=set(r.signals['source_document_ids']+r.signals['candidate_document_ids']+[str(r.transaction_id),str(r.candidate_id)])
    if any(str(e) not in allowed for e in data['evidence_ids']):raise DomainError(422,'RESOLUTION_EVIDENCE_INVALID','Evidence must belong to the pinned pair.')
    if data['disposition']=='SHARED_RECEIPT_ALLOCATION':
        shares=session.scalars(scope_query(select(ReceiptShare),ReceiptShare,identity).where(ReceiptShare.transaction_id==r.transaction_id,ReceiptShare.transaction_version==r.transaction_version)).all()
        common=set(r.signals['source_document_ids'])&set(r.signals['candidate_document_ids'])
        if not common:raise DomainError(409,'SHARED_SOURCE_REQUIRED','Shared capacity must cite the same actual receipt UUID; attach and verify that source before resolving copied documents.')
        if not shares:raise DomainError(409,'SHARED_ALLOCATION_REQUIRED','Create an authorized receipt share before resolving as shared.')
    row=DuplicateResolution(**identity.scope(),comparison_id=r.id,disposition=data['disposition'],actor_id=identity.actor_id,reason=data['reason'],evidence=data['evidence_ids']);session.add(row);session.flush();finance.audit(session,identity,'DUPLICATE_RESOLVED',row.id,1,data['reason'],correlation,{'comparison_id':str(r.id),'source_version':r.transaction_version,'candidate_version':r.candidate_version,'disposition':row.disposition})
    finance.enqueue(session,identity,t.id,t.latest_version,'Duplicate disposition requires fresh controls',correlation,str(row.id));return projection({'id':row.id,'comparison_id':r.id,'disposition':row.disposition})


def share_receipt(session,identity,transaction_id,data,correlation):
    from app.services import finance
    from app.services.reference_imports import require
    require(identity,'RECEIPT_ALLOCATOR');finance.scope_lock(session,identity);t=finance.get(session,Transaction,identity,transaction_id)
    finance.require_active(t);finance.review_guard(session,identity,t,data)
    if t.latest_version!=data['expected_version']:raise DomainError(409,'STALE_VERSION','Receipt allocation must target current facts.')
    version=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==t.id,TransactionVersion.version==t.latest_version));p=version.payload
    if D(data['amount'])<=0 or D(data['quantity'])<=0:raise DomainError(422,'RECEIPT_SHARE_POSITIVE','Allocated amount and quantity must be positive.')
    item=next((i for i in p['items'] if i['id']==data['item_id']),None)
    if p['branch']!='EMPLOYEE_EXPENSE' or not item or item.get('source_document_id')!=data['document_id'] or D(item.get('claimed_amount') or '0')!=D(data['amount']):raise DomainError(422,'RECEIPT_SHARE_FACT_MISMATCH','Share must cite the actual current claimant/item/document and exact claimed amount.')
    from app.db.document_models import TransactionDocument
    physical=session.scalar(scope_query(select(TransactionDocument),TransactionDocument,identity).where(TransactionDocument.transaction_id==t.id,TransactionDocument.transaction_version==t.latest_version,TransactionDocument.document_id==UUID(data['document_id']),TransactionDocument.role=='RECEIPT',TransactionDocument.verification_id.is_not(None)))
    synthetic=session.scalar(scope_query(select(ReferenceRecord),ReferenceRecord,identity).where(ReferenceRecord.id==UUID(data['document_id']),ReferenceRecord.kind=='documents'))
    if not physical and not (synthetic and synthetic.payload.get('verification')=='ADJUDICATED_SYNTHETIC_FACTS'):raise DomainError(409,'RECEIPT_SOURCE_REQUIRED','An actual verified attachment or explicitly synthetic source is required.')
    if not data['evidence_ids'] or str(t.id) not in data['evidence_ids']:raise DomainError(422,'RECEIPT_RATIONALE_REQUIRED','Cite the current claim as allocation evidence.')
    row=ReceiptShare(**identity.scope(),transaction_id=t.id,transaction_version=t.latest_version,document_id=UUID(data['document_id']),item_id=UUID(data['item_id']),employee_id=UUID(p['employee_id']),amount=D(data['amount']),quantity=D(data['quantity']),currency=p['currency'],actor_id=identity.actor_id,reason=data['reason'],evidence=data['evidence_ids']);session.add(row);session.flush();finance.audit(session,identity,'RECEIPT_SHARE_AUTHORIZED',row.id,1,data['reason'],correlation,{'document_id':data['document_id'],'transaction_version':t.latest_version,'amount':data['amount']})
    finance.enqueue(session,identity,t.id,t.latest_version,'Authorized receipt share requires capacity checks',correlation,str(row.id));return projection({'id':row.id,'amount':row.amount,'employee_id':row.employee_id,'document_id':row.document_id})


def evidence(session,identity,record_id):
    """Resolve real append-only control facts, always scope filtered."""
    from app.db.finance_models import BudgetEvent,ReceiptShare,ApprovalAction,Waiver,AllocationEvent
    for cls in (DuplicateComparison,DuplicateResolution,FinanceAllocation,BudgetEvent,ReceiptShare,ApprovalAction,Waiver,AllocationEvent):
        row=session.scalar(scope_query(select(cls),cls,identity).where(cls.id==record_id))
        if row is not None:
            if not {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER','DUPLICATE_REVIEWER'}&identity.roles:
                return {'kind':cls.__tablename__,'cross_employee_details':'MASKED','amount':str(getattr(row,'amount','UNKNOWN')),'classification':getattr(row,'classification',None)}
            data={c.name:getattr(row,c.name) for c in cls.__table__.columns}
            return projection(data)
    return None
