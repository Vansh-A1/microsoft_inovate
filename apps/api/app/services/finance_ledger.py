"""Append-only budget/allocation lifecycle. Call under the finance scope lock."""
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import select
from app.core.errors import DomainError
from app.core.serialization import digest, projection
from app.db.finance_models import FinanceAllocation, AllocationEvent, BudgetEvent
from app.db.session import scope_query
D=Decimal
ZERO=D('0')

def event(session,identity,budget,kind,amount,key,reason,*,allocation=None,owner=None,metadata=None):
    existing=session.scalar(scope_query(select(BudgetEvent),BudgetEvent,identity).where(BudgetEvent.operation_key==digest(key)))
    if existing:return existing
    row=BudgetEvent(**identity.scope(),budget_id=UUID(budget['id']),budget_version=budget['version'],allocation_id=allocation.id if allocation else None,owner_id=UUID(owner) if owner else None,entry_type=kind,amount=D(amount),currency=budget['currency'],actor_id=identity.actor_id,reason=reason,operation_key=digest(key),metadata_json=metadata or {})
    session.add(row);session.flush();return row

def import_budget(session,identity,record,batch_id):
    for row in record.payload.get('ledger',[]):
        # A new version is a fresh source snapshot; previous versions remain pinned.
        kind={'PO_COMMITMENT':'COMMITMENT','CLAIM_RESERVATION':'RESERVATION'}.get(row['entry_type'],row['entry_type'])
        event(session,identity,record.payload,kind,row['amount'],f'import:{batch_id}:{row["id"]}','Validated synthetic source ledger',owner=row.get('owner_id'),metadata={'source_record_id':row['id'],'source_version':record.version,'source_import':True,'direction':row.get('direction','INCREASE')})

def states(session,identity,allocations):
    ids=[r.id for r in allocations]
    if not ids:return {}
    rows=session.scalars(scope_query(select(AllocationEvent),AllocationEvent,identity).where(AllocationEvent.allocation_id.in_(ids)).order_by(AllocationEvent.created_at,AllocationEvent.id)).all()
    result={}
    for r in rows:result[r.allocation_id]=r.action
    return result

def active(session,identity,*,exclude=None,kind=None,resource=None):
    q=scope_query(select(FinanceAllocation),FinanceAllocation,identity)
    if kind:q=q.where(FinanceAllocation.kind==kind)
    if resource:q=q.where(FinanceAllocation.resource_id==resource)
    rows=session.scalars(q.limit(10001)).all()
    if len(rows)>10000:raise DomainError(503,'ALLOCATION_LIMIT','Allocation query coverage exceeds its configured bound.')
    lifecycle=states(session,identity,rows)
    return [(r,lifecycle.get(r.id)) for r in rows if lifecycle.get(r.id) in ('RESERVED','CONSUMED') and not (exclude and r.transaction_id==exclude and lifecycle.get(r.id)=='RESERVED')]

def balance(session,identity,budget,*,exclude=None,po_id=None):
    events=session.scalars(scope_query(select(BudgetEvent),BudgetEvent,identity).where(BudgetEvent.budget_id==UUID(budget['id']),BudgetEvent.budget_version==budget['version']).order_by(BudgetEvent.created_at,BudgetEvent.id)).all()
    source=[r for r in events if r.metadata_json.get('source_import') or r.allocation_id is None]
    if source:
        allocation=sum((r.amount for r in source if r.entry_type=='ALLOCATION'),ZERO)
        adjustment=sum((r.amount*(D('-1') if r.metadata_json.get('direction')=='DECREASE' else D('1')) for r in source if r.entry_type=='ADJUSTMENT'),ZERO)
        consumed=sum((r.amount for r in source if r.entry_type=='CONSUMPTION'),ZERO)
        committed=sum((r.amount for r in source if r.entry_type=='COMMITMENT'),ZERO)
        fixed_reserved=sum((r.amount for r in source if r.entry_type=='RESERVATION'),ZERO)
        covered=sum((r.amount for r in source if r.entry_type=='COMMITMENT' and str(r.owner_id)==po_id),ZERO)
    else:
        ledger=budget.get('ledger',[])
        allocation=sum((D(r['amount']) for r in ledger if r['entry_type']=='ALLOCATION'),ZERO);adjustment=ZERO
        consumed=sum((D(r['amount']) for r in ledger if r['entry_type']=='CONSUMPTION'),ZERO)
        committed=sum((D(r['amount']) for r in ledger if r['entry_type']=='PO_COMMITMENT'),ZERO)
        fixed_reserved=sum((D(r['amount']) for r in ledger if r['entry_type']=='CLAIM_RESERVATION'),ZERO)
        covered=sum((D(r['amount']) for r in ledger if r['entry_type']=='PO_COMMITMENT' and r.get('owner_id')==po_id),ZERO)
    live=active(session,identity,exclude=exclude,kind='BUDGET',resource=UUID(budget['id']))
    reserved=ZERO;coverage_used=ZERO;total_consumed=ZERO;total_transferred=ZERO
    for a,state in live:
        coverage=D(a.metadata_json.get('commitment_coverage','0'))
        if state=='RESERVED':reserved+=a.amount
        else:total_consumed+=a.amount+coverage;total_transferred+=coverage
        if a.metadata_json.get('po_id')==po_id:coverage_used+=coverage
    committed=max(ZERO,committed-total_transferred)
    consumed+=total_consumed
    return projection({'allocation':allocation,'adjustments':adjustment,'consumed':consumed,'open_po_commitments':committed,'active_reservations':fixed_reserved+reserved,'available':allocation+adjustment-consumed-committed-fixed_reserved-reserved,'po_commitment_coverage':max(ZERO,covered-coverage_used),'ledger_event_ids':[str(r.id) for r in events]})

def allocate(session,identity,evaluation,version,kind,resource,amount,quantity,currency,*,reference=None,metadata=None):
    key=digest({'evaluation':str(evaluation.id),'kind':kind,'resource':str(resource)})
    old=session.scalar(scope_query(select(FinanceAllocation),FinanceAllocation,identity).where(FinanceAllocation.operation_key==key))
    if old:return old
    row=FinanceAllocation(**identity.scope(),transaction_id=version.transaction_id,transaction_version=version.version,evaluation_id=evaluation.id,kind=kind,resource_id=UUID(str(resource)),reference_id=UUID(reference['id']) if reference else None,reference_version=reference['version'] if reference else None,amount=D(amount),quantity=D(quantity),currency=currency,metadata_json=metadata or {},operation_key=key)
    session.add(row);session.flush();session.add(AllocationEvent(**identity.scope(),allocation_id=row.id,action='RESERVED',actor_id=identity.actor_id,reason='Eligible finalization capacity admission'));session.flush();return row

def transition(session,identity,allocation,action,reason):
    state=states(session,identity,[allocation]).get(allocation.id)
    allowed={'RESERVED':{'CONSUMED','RELEASED'},'CONSUMED':{'REVERSED'}}
    if state==action:return False
    if action not in allowed.get(state,set()):raise DomainError(409,'ALLOCATION_TRANSITION','Consumed capacity requires a reversal; released capacity cannot be consumed.')
    session.add(AllocationEvent(**identity.scope(),allocation_id=allocation.id,action=action,actor_id=identity.actor_id,reason=reason));session.flush();return True

def release_transaction(session,identity,transaction_id,reason='Canonical version or evaluation superseded'):
    rows=session.scalars(scope_query(select(FinanceAllocation),FinanceAllocation,identity).where(FinanceAllocation.transaction_id==transaction_id)).all();latest=states(session,identity,rows)
    for r in rows:
        if latest.get(r.id)!='RESERVED':continue
        transition(session,identity,r,'RELEASED',reason)
        if r.kind=='BUDGET':
            budget={'id':str(r.reference_id),'version':r.reference_version,'currency':r.currency}
            event(session,identity,budget,'RELEASE',r.amount,f'release:{r.id}',reason,allocation=r,owner=str(transaction_id),metadata={'commitment_coverage':r.metadata_json.get('commitment_coverage','0')})
