"""Phase-3 authenticated controls; bodies never supply actor, role or tenant."""
from typing import Annotated
from uuid import UUID
from fastapi import Depends, Header, Request
from pydantic import Field
from sqlalchemy import select
from app.schemas.canonical import Strict,Amount,ISODate
from app.services import reference_imports as refs
from app.services import finance
from app.db.finance_models import ReferenceBatch
from app.db.session import scope_query

class ReferenceEntry(Strict):
    kind:str=Field(min_length=1,max_length=48)
    payload:dict

class StageReference(Strict):
    source_system:str=Field(min_length=1,max_length=100)
    source_version:str=Field(min_length=1,max_length=100)
    records:list[ReferenceEntry]=Field(min_length=1,max_length=500)
    reason:str=Field(min_length=3)
class Reason(Strict):
    reason:str=Field(min_length=3)
class ResolveIdentity(Strict):
    kind:str
    identifier:str|None=None
    name:str|None=None
    business_date:ISODate|None=None

def mount(app,database,identity,mutation):
    @app.get('/api/v1/reference-imports')
    def batches(ctx=Depends(identity)):
        refs.require(ctx,'REFERENCE_ADMIN')
        with database.session(ctx) as s:return {'items':[refs.batch_view(r) for r in s.scalars(scope_query(select(ReferenceBatch),ReferenceBatch,ctx).order_by(ReferenceBatch.created_at.desc()).limit(100))]}
    @app.post('/api/v1/reference-imports',status_code=201)
    def stage(body:StageReference,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json');return mutation(request,ctx,key,data,201,lambda s:refs.stage(s,ctx,data,request.state.correlation))
    @app.post('/api/v1/reference-imports/{batch_id}/validate')
    def validate(batch_id:UUID,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,{},200,lambda s:refs.validate(s,ctx,batch_id,request.state.correlation))
    @app.post('/api/v1/reference-imports/{batch_id}/activate')
    def activate(batch_id:UUID,body:Reason,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(),200,lambda s:refs.activate(s,ctx,batch_id,body.reason,request.state.correlation))
    @app.post('/api/v1/identity-resolutions')
    def resolve(body:ResolveIdentity,ctx=Depends(identity)):
        if not {'FINANCE_REVIEWER','REFERENCE_ADMIN','AUDITOR','FINANCE_CONTROLLER'}&ctx.roles:refs.require(ctx,'REFERENCE_ADMIN')
        if body.kind not in ('vendors','employees'):raise __import__('app.core.errors',fromlist=['DomainError']).DomainError(422,'IDENTITY_KIND_INVALID','Use vendors or employees.')
        with database.session(ctx) as s:
            records={k:r.payload|{'_kind':r.kind} for k,r in refs.active_records(s,ctx).items()}
            result=refs.resolve(records,body.kind,body.identifier,body.name,body.business_date)
            return finance.redact(result)

class CurrentReason(Reason):
    expected_version:int=Field(ge=1)
    review_case_id:UUID|None=None
    expected_review_version:int|None=Field(default=None,ge=1)
class ApprovalCommand(CurrentReason):
    sequence:int=Field(ge=1,le=20)
    action:str=Field(pattern='^(APPROVED|DECLINED)$')
class DuplicateCommand(CurrentReason):
    disposition:str=Field(pattern='^(DISTINCT|CONFIRMED_DUPLICATE|SHARED_RECEIPT_ALLOCATION)$')
    evidence_ids:list[str]=Field(min_length=1,max_length=20)
class ShareCommand(CurrentReason):
    document_id:UUID
    item_id:UUID
    amount:Amount
    quantity:Amount='1'
    evidence_ids:list[str]=Field(min_length=1,max_length=20)
class WaiverCommand(CurrentReason):
    rule_id:str
    expires_at:str
    evidence_ids:list[str]=Field(min_length=1,max_length=20)
class AllocationCommand(Reason):
    action:str=Field(pattern='^(CONSUMED|RELEASED|REVERSED)$')
class BudgetCommand(Reason):
    amount:Amount
    direction:str=Field(pattern='^(INCREASE|DECREASE)$')


def mount_controls(app,database,identity,mutation):
    from fastapi.responses import JSONResponse
    from app.db.models import Transaction,TransactionVersion,Evaluation,Report,ReferenceRecord
    from app.db.finance_models import DuplicateComparison,DuplicateResolution,ApprovalRequest,ReceiptShare,FinanceAllocation,BudgetEvent,Waiver
    from app.services import finance_controls,approvals,finance_ledger
    from app.core.serialization import projection,digest
    from app.schemas.canonical import decimal_text
    from decimal import Decimal
    def visible(ctx):return bool({'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER','DUPLICATE_REVIEWER'}&ctx.roles)
    def version(s,ctx,tid):
        t=finance.get(s,Transaction,ctx,tid)
        v=s.scalar(scope_query(select(TransactionVersion),TransactionVersion,ctx).where(TransactionVersion.transaction_id==t.id,TransactionVersion.version==t.latest_version))
        if not visible(ctx) and v.party_id!=ctx.actor_id:raise __import__('app.core.errors',fromlist=['DomainError']).DomainError(404,'NOT_FOUND','Record is unavailable.')
        return t,v
    @app.get('/api/v1/transactions/{record_id}/finance-controls')
    def controls(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:
            t,v=version(s,ctx,record_id);report=s.scalar(scope_query(select(Report),Report,ctx).where(Report.evaluation_id==t.latest_evaluation_id)) if t.latest_evaluation_id else None
            data=report.content.get('finance_controls') if report else None
            if data and not visible(ctx):
                data=dict(data);data['duplicates']=[{'classification':r['classification'],'signals':{'cross_employee_details':'MASKED'},'disposition':r.get('disposition')} for r in data.get('duplicates',[])];data['allocations']=[{'kind':r['kind'],'amount':r['amount'],'state':r['state']} for r in data.get('allocations',[])];data['receipt_usage']=[{'amount':r['amount'],'state':r['state']} for r in data.get('receipt_usage',[])]
            return {'transaction_version':t.latest_version,'evaluated_version':report.content['transaction_version'] if report else None,'controls':data,'status':'AVAILABLE' if data else 'AWAITING_PHASE3_EVALUATION'}
    @app.get('/api/v1/transactions/{record_id}/duplicate-candidates')
    def comparisons(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:
            t,v=version(s,ctx,record_id);rows=s.scalars(scope_query(select(DuplicateComparison),DuplicateComparison,ctx).where(DuplicateComparison.transaction_id==record_id,DuplicateComparison.transaction_version==t.latest_version).order_by(DuplicateComparison.created_at)).all()
            items=[]
            latest={}
            for row in rows:latest[(row.candidate_id,row.candidate_version,row.candidate_type)]=row
            for r in latest.values():
                pair_ids=[x.id for x in rows if x.candidate_id==r.candidate_id and x.candidate_version==r.candidate_version and x.candidate_type==r.candidate_type]
                disposition=s.scalar(scope_query(select(DuplicateResolution),DuplicateResolution,ctx).where(DuplicateResolution.comparison_id.in_(pair_ids)).order_by(DuplicateResolution.created_at.desc()).limit(1))
                item=projection({'id':r.id,'candidate_id':r.candidate_id,'candidate_version':r.candidate_version,'classification':r.classification,'signals':r.signals,'disposition':disposition.disposition if disposition else None}) if visible(ctx) else {'classification':r.classification,'cross_employee_details':'MASKED','disposition':disposition.disposition if disposition else None}
                items.append(item)
            return {'items':items,'transaction_version':t.latest_version,'detail_access':'FINANCE' if visible(ctx) else 'MASKED'}
    @app.post('/api/v1/duplicate-candidates/{comparison_id}/resolutions',status_code=201)
    def resolve(comparison_id:UUID,body:DuplicateCommand,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json');return mutation(request,ctx,key,data,201,lambda s:finance_controls.resolve_duplicate(s,ctx,comparison_id,data,request.state.correlation))
    @app.get('/api/v1/transactions/{record_id}/matching-allocations')
    def allocations(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:
            t,v=version(s,ctx,record_id);rows=s.scalars(scope_query(select(FinanceAllocation),FinanceAllocation,ctx).where(FinanceAllocation.transaction_id==t.id)).all();states=finance_ledger.states(s,ctx,rows)
            return {'items':projection([{'id':r.id,'transaction_version':r.transaction_version,'kind':r.kind,'resource_id':r.resource_id,'amount':r.amount,'quantity':r.quantity,'currency':r.currency,'state':states.get(r.id),'metadata':r.metadata_json} for r in rows])}
    @app.post('/api/v1/allocations/{allocation_id}/actions')
    def allocation_action(allocation_id:UUID,body:AllocationCommand,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        refs.require(ctx,'LEDGER_ADMIN');data=body.model_dump()
        def operation(s):
            r=finance.get(s,FinanceAllocation,ctx,allocation_id);finance.scope_lock(s,ctx)
            owner_rows=s.scalars(scope_query(select(FinanceAllocation),FinanceAllocation,ctx).where(FinanceAllocation.evaluation_id==r.evaluation_id)).all()
            states=finance_ledger.states(s,ctx,owner_rows)
            expected={'CONSUMED':'RESERVED','RELEASED':'RESERVED','REVERSED':'CONSUMED'}[body.action]
            if any(states.get(a.id) not in (expected,body.action) for a in owner_rows):raise __import__('app.core.errors',fromlist=['DomainError']).DomainError(409,'ALLOCATION_TRANSITION','All owner resources must transition together; consumed capacity requires an explicit reversal.')
            if body.action=='CONSUMED' and any(states.get(a.id)=='RESERVED' for a in owner_rows):
                from app.services.operations import eligibility
                t=finance.get(s,Transaction,ctx,r.transaction_id)
                if t.latest_evaluation_id!=r.evaluation_id or not eligibility(s,ctx,t)['current_eligible']:
                    raise __import__('app.core.errors',fromlist=['DomainError']).DomainError(409,'ELIGIBILITY_STALE','Fresh current screening and reservations are required before capacity consumption.')
            changed=False
            for owned in owner_rows:
                did_change=finance_ledger.transition(s,ctx,owned,body.action,body.reason);changed=changed or did_change
                if owned.kind=='BUDGET' and did_change:
                    budget={'id':str(owned.reference_id),'version':owned.reference_version,'currency':owned.currency};finance_ledger.event(s,ctx,budget,{'CONSUMED':'CONSUMPTION','RELEASED':'RELEASE','REVERSED':'REVERSAL'}[body.action],owned.amount,f'api-transition:{owned.id}:{body.action}',body.reason,allocation=owned,owner=str(owned.transaction_id),metadata={'commitment_coverage':owned.metadata_json.get('commitment_coverage','0')})
                    if body.action=='CONSUMED' and Decimal(owned.metadata_json.get('commitment_coverage','0'))>0:finance_ledger.event(s,ctx,budget,'COMMITMENT_TRANSFER',owned.metadata_json['commitment_coverage'],f'transfer:{owned.id}',body.reason,allocation=owned,owner=owned.metadata_json.get('po_id'))
            if changed and body.action in ('RELEASED','REVERSED') and finance.get(s,Transaction,ctx,r.transaction_id).processing_state!='CANCELLED':
                t=finance.get(s,Transaction,ctx,r.transaction_id);t.eligible=False;t.decision=None;t.processing_state='RECEIVED';t.row_version+=1
            return {'id':str(r.id),'state':body.action,'changed':changed}
        return mutation(request,ctx,key,data,200,operation)
    @app.post('/api/v1/transactions/{record_id}/cancellations')
    def cancel(record_id:UUID,body:CurrentReason,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        from app.services.reviews import cancel as cancel_transaction
        def operation(s):
            finance.scope_lock(s,ctx);finance.review_guard(s,ctx,finance.get(s,Transaction,ctx,record_id),body.model_dump(mode='json'))
            return cancel_transaction(s,ctx,record_id,body.expected_version,body.reason,request.state.correlation)
        return mutation(request,ctx,key,body.model_dump(mode='json'),200,operation)
    @app.get('/api/v1/budgets/{budget_id}/ledger')
    def budget_ledger(budget_id:UUID,ctx=Depends(identity)):
        if not visible(ctx):refs.require(ctx,'AUDITOR')
        with database.session(ctx) as s:
            budget=refs.active_records(s,ctx).get(str(budget_id))
            if not budget or budget.kind!='budgets':raise __import__('app.core.errors',fromlist=['DomainError']).DomainError(404,'NOT_FOUND','Budget unavailable.')
            rows=s.scalars(scope_query(select(BudgetEvent),BudgetEvent,ctx).where(BudgetEvent.budget_id==budget_id).order_by(BudgetEvent.created_at,BudgetEvent.id)).all()
            return {'budget':finance.redact(budget.payload),'balance':finance_ledger.balance(s,ctx,budget.payload),'events':projection([{'id':r.id,'budget_version':r.budget_version,'entry_type':r.entry_type,'amount':r.amount,'currency':r.currency,'allocation_id':r.allocation_id,'owner_id':r.owner_id,'reason':r.reason,'created_at':r.created_at,'metadata':r.metadata_json} for r in rows])}
    @app.post('/api/v1/budgets/{budget_id}/adjustments',status_code=201)
    def budget_adjustment(budget_id:UUID,body:BudgetCommand,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        refs.require(ctx,'LEDGER_ADMIN');amount=decimal_text(body.amount)
        def operation(s):
            finance.scope_lock(s,ctx);budget=refs.active_records(s,ctx).get(str(budget_id))
            if not budget or budget.kind!='budgets':raise __import__('app.core.errors',fromlist=['DomainError']).DomainError(404,'NOT_FOUND','Budget unavailable.')
            if body.direction=='DECREASE' and Decimal(amount)>Decimal(finance_ledger.balance(s,ctx,budget.payload)['available']):raise __import__('app.core.errors',fromlist=['DomainError']).DomainError(409,'BUDGET_CAPACITY','Adjustment cannot make available capacity negative.')
            r=finance_ledger.event(s,ctx,budget.payload,'ADJUSTMENT',amount,'adjustment:'+key,body.reason,metadata={'direction':body.direction});finance.audit(s,ctx,'BUDGET_ADJUSTED',r.id,1,body.reason,request.state.correlation);return projection({'id':r.id,'amount':r.amount,'direction':body.direction})
        return mutation(request,ctx,key,body.model_dump(),201,operation)
    @app.post('/api/v1/transactions/{record_id}/receipt-shares',status_code=201)
    def receipt_share(record_id:UUID,body:ShareCommand,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        decimal_text(body.amount);decimal_text(body.quantity);data=body.model_dump(mode='json');return mutation(request,ctx,key,data,201,lambda s:finance_controls.share_receipt(s,ctx,record_id,data,request.state.correlation))
    @app.get('/api/v1/transactions/{record_id}/receipt-shares')
    def receipt_shares(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:
            t,v=version(s,ctx,record_id);rows=s.scalars(scope_query(select(ReceiptShare),ReceiptShare,ctx).where(ReceiptShare.transaction_id==record_id)).all();return {'items':projection([{'id':r.id,'transaction_version':r.transaction_version,'item_id':r.item_id,'document_id':r.document_id,'employee_id':r.employee_id,'amount':r.amount,'quantity':r.quantity,'reason':r.reason,'actor_id':r.actor_id} for r in rows])}
    @app.post('/api/v1/transactions/{record_id}/approval-requests',status_code=201)
    def approval_request(record_id:UUID,body:CurrentReason,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        refs.require(ctx,'FINANCE_REVIEWER');data=body.model_dump();return mutation(request,ctx,key,data,201,lambda s:approvals.create_request(s,ctx,record_id,body.expected_version,body.reason,request.state.correlation))
    @app.get('/api/v1/transactions/{record_id}/approval-requests')
    def approval_requests(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:
            version(s,ctx,record_id);rows=s.scalars(scope_query(select(ApprovalRequest),ApprovalRequest,ctx).where(ApprovalRequest.transaction_id==record_id).order_by(ApprovalRequest.created_at)).all();return {'items':[approvals.view_request(s,ctx,r) for r in rows]}
    @app.post('/api/v1/approval-requests/{request_id}/actions')
    def approval_action(request_id:UUID,body:ApprovalCommand,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump()
        # Rejected attempts commit their audit/action before returning HTTP 403.
        with database.session(ctx) as s:result,status=finance.idempotent(s,ctx,request.url.path,key,data,200,lambda:approvals.act(s,ctx,request_id,data,request.state.correlation))
        if result.get('rejected'):return JSONResponse(status_code=403,content={'error':{'code':result['code'],'message':'Approval rejected by configured authority or sequence.','details':{},'retryable':False},'request':result['request']})
        return JSONResponse(status_code=status,content=result)
    @app.post('/api/v1/transactions/{record_id}/waivers',status_code=201)
    def waiver(record_id:UUID,body:WaiverCommand,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump();return mutation(request,ctx,key,data,201,lambda s:approvals.waive(s,ctx,record_id,data,request.state.correlation))
    @app.get('/api/v1/transactions/{record_id}/waivers')
    def waivers(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:
            t,v=version(s,ctx,record_id);rows=s.scalars(scope_query(select(Waiver),Waiver,ctx).where(Waiver.transaction_id==record_id)).all();return {'items':projection([{'id':r.id,'transaction_version':r.transaction_version,'rule_id':r.rule_id,'rule_version':r.rule_version,'reason':r.reason,'actor_id':r.actor_id,'expires_at':r.expires_at,'stale':r.transaction_version!=t.latest_version} for r in rows])}
