"""Typed business edits; reuse immutable reference import/activation, never finance decisions."""
from copy import deepcopy
from typing import Annotated, Literal
from uuid import UUID
from fastapi import Depends, Header, Request
from pydantic import Field, model_validator
from sqlalchemy import select
from app.schemas.canonical import Strict, Amount, ISODate
from app.core.errors import DomainError
from app.core.serialization import projection
from app.db.models import ReferenceRecord,AuditEvent
from app.db.finance_models import ReferenceBatch
from app.db.session import scope_query
from app.services import reference_imports as refs, finance

POLICIES={'expense_policies','approval_policies','delegations','waiver_policies'}
MASTER={'vendors','employees','cost_centers'}
class Band(Strict):
    from_amount:Amount
    to_amount:Amount|None=None
    roles:list[str]=Field(min_length=1,max_length=10)
class BusinessChange(Strict):
    expected_version:int=Field(ge=1)
    reason:str=Field(min_length=3)
    effective_from:ISODate|None=None
    effective_to:ISODate|None=None
    allowance_amount:Amount|None=None
    submission_window_days:int|None=Field(default=None,ge=0,le=365)
    receipt_required:bool|None=None
    bands:list[Band]|None=Field(default=None,max_length=20)
    ceiling_amount:Amount|None=None
    roles:list[str]|None=Field(default=None,max_length=10)
    maximum_days:int|None=Field(default=None,ge=1,le=365)
    name:str|None=Field(default=None,min_length=1)
    legal_name:str|None=Field(default=None,min_length=1)
    status:Literal['ACTIVE','INACTIVE','APPROVED','BLOCKED']|None=None
    department:str|None=None
    @model_validator(mode='after')
    def changes(self):
        if not any(k not in ('expected_version','reason') for k in self.model_fields_set):raise ValueError('Provide a business change.')
        return self
class Reason(Strict):
    reason:str=Field(min_length=3)

def permitted(ctx,kind):
    if kind in POLICIES and 'POLICY_ADMIN' in ctx.roles:return True
    return 'REFERENCE_ADMIN' in ctx.roles

def mount(app,database,identity,mutation):
    @app.get('/api/v1/admin/catalog')
    def catalog(ctx=Depends(identity)):
        if not {'POLICY_ADMIN','REFERENCE_ADMIN','LEDGER_ADMIN'}&ctx.roles:raise DomainError(403,'FORBIDDEN','Configuration permission is required.')
        with database.session(ctx) as s:
            active=refs.active_records(s,ctx)
            rows=[r for r in active.values() if (r.kind in POLICIES|MASTER and permitted(ctx,r.kind)) or (r.kind=='budgets' and 'LEDGER_ADMIN' in ctx.roles)]
            return {'items':[{'id':str(r.id),'version':r.version,'kind':r.kind,'label':r.label,'payload':finance.redact(r.payload)} for r in rows]}
    @app.get('/api/v1/admin/records/{record_id}/versions')
    def versions(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:
            rows=s.scalars(scope_query(select(ReferenceRecord),ReferenceRecord,ctx).where(ReferenceRecord.id==record_id).order_by(ReferenceRecord.version)).all()
            if not rows:raise DomainError(404,'NOT_FOUND','Configuration record not found.')
            if not permitted(ctx,rows[-1].kind):raise DomainError(403,'FORBIDDEN','Configuration permission is required.')
            items=[]
            for r in rows:
                audit=None
                if r.payload.get('import_batch_id'):
                    audit=s.scalar(scope_query(select(AuditEvent),AuditEvent,ctx).where(AuditEvent.object_id==UUID(r.payload['import_batch_id']),AuditEvent.action=='REFERENCE_ACTIVATED'))
                items.append({'version':r.version,'payload':finance.redact(r.payload),'change':None if not audit else {'actor_id':str(audit.actor_id),'reason':audit.reason,'at':audit.created_at.isoformat()}})
            return {'items':items}
    @app.post('/api/v1/admin/records/{record_id}/drafts',status_code=201)
    def draft(record_id:UUID,body:BusinessChange,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        # Authorization also precedes cached idempotency responses after role revocation.
        with database.session(ctx) as s:
            current=refs.active_records(s,ctx).get(str(record_id))
            if not current:raise DomainError(404,'NOT_FOUND','Configuration record not found.')
            if not permitted(ctx,current.kind):raise DomainError(403,'FORBIDDEN','Configuration permission is required.')
        data=body.model_dump(mode='json',exclude_unset=True)
        def operation(s):
            finance.scope_lock(s,ctx);r=refs.active_records(s,ctx).get(str(record_id))
            if not r:raise DomainError(404,'NOT_FOUND','Configuration record not found.')
            if not permitted(ctx,r.kind):raise DomainError(403,'FORBIDDEN','Configuration permission is required.')
            if r.version!=body.expected_version:raise DomainError(409,'CONFIGURATION_CHANGED','Refresh the current configuration version.',details={'current_version':r.version})
            allowed={'expense_policies':{'allowance_amount','submission_window_days','receipt_required'},'approval_policies':{'bands'},'delegations':{'ceiling_amount','roles'},'waiver_policies':{'maximum_days','roles'},'vendors':{'legal_name','status'},'employees':{'name','status','department'},'cost_centers':{'name','department'}}.get(r.kind,set())
            if r.kind in POLICIES|{'vendors','employees'}:allowed|={'effective_from','effective_to'}
            changed=set(data)-{'expected_version','reason'}
            if not changed<=allowed:raise DomainError(422,'CHANGE_UNSUPPORTED','These fields are not editable for this configuration record.')
            if any(data[k] is None for k in changed):raise DomainError(422,'VALUE_REQUIRED','Business form values cannot be cleared implicitly.')
            payload=deepcopy(r.payload)
            for k in ('import_batch_id','imported_at','validation_result'):payload.pop(k,None)
            payload.update({k:data[k] for k in changed});payload['version']=r.version+1
            # Existing approval schema uses lower/upper bounds and required_roles.
            if body.bands is not None:
                payload['bands']=[{'lower_bound_amount':b.from_amount,'lower_inclusive':True,'upper_bound_amount':b.to_amount,'upper_inclusive':False,'required_roles':b.roles} for b in body.bands]
            policy_only='REFERENCE_ADMIN' not in ctx.roles
            staged=refs.stage(s,ctx,{'source_system':'BUSINESS_ADMIN','source_version':f'v{payload["version"]}','reason':body.reason,'records':[{'kind':r.kind,'payload':payload}]},request.state.correlation,policy_only=policy_only)
            checked=refs.validate(s,ctx,UUID(staged['id']),request.state.correlation,policy_only=policy_only)
            return checked
        return mutation(request,ctx,key,data,201,operation)
    @app.post('/api/v1/admin/drafts/{batch_id}/activate')
    def activate(batch_id:UUID,body:Reason,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        refs.authorize_batch(ctx,[],policy_only='REFERENCE_ADMIN' not in ctx.roles)
        with database.session(ctx) as s:
            row=finance.get(s,ReferenceBatch,ctx,batch_id)
            refs.authorize_batch(ctx,row.records,policy_only='REFERENCE_ADMIN' not in ctx.roles)
        def operation(s):
            if not {'POLICY_ADMIN','REFERENCE_ADMIN'}&ctx.roles:raise DomainError(403,'FORBIDDEN','Configuration permission is required.')
            row=finance.get(s,ReferenceBatch,ctx,batch_id)
            if row.source_system!='BUSINESS_ADMIN':raise DomainError(403,'DRAFT_SCOPE','Use the reference-import workflow for imported batches.')
            return refs.activate(s,ctx,batch_id,body.reason,request.state.correlation,policy_only='REFERENCE_ADMIN' not in ctx.roles)
        return mutation(request,ctx,key,body.model_dump(),200,operation)
