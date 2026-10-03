"""Typed Phase-4 workflow boundaries. Actors, roles and scope are server owned."""
from typing import Literal, Annotated
from uuid import UUID
from fastapi import Depends, Header, Request
from fastapi.responses import Response
from pydantic import Field, model_validator
from app.schemas.canonical import Strict, Canonical
from app.documents.routes import DocumentCommit
from app.db.models import ReviewCase, Transaction
from app.services import finance, reviews, operations

class ReviewWrite(Strict):
    expected_review_version:int=Field(ge=1)
    expected_transaction_version:int=Field(ge=1)
    reason_code:str=Field(min_length=1,max_length=80,pattern='^[A-Z0-9_]+$')
    comment:str=Field(min_length=3,max_length=500)

class Assignment(ReviewWrite):
    action:Literal['CLAIM','RELEASE','REASSIGN']
    owner_id:UUID|None=None
    @model_validator(mode='after')
    def target(self):
        if (self.action=='REASSIGN') != (self.owner_id is not None):raise ValueError('Only reassignment accepts a target owner.')
        return self

class ReviewCommand(ReviewWrite):
    action:Literal['REQUEST_INFORMATION','CORRECT_FIELD','MARK_DUPLICATE','MARK_DISTINCT','SHARED_RECEIPT_RESOLUTION','RESOLVE_EXCEPTION','PROPOSE_WAIVER','CANCEL_TRANSACTION']
    evidence_ids:list[UUID]=Field(default_factory=list,max_length=20)
    requested_input:str|None=Field(default=None,min_length=3,max_length=1000)
    transaction:Canonical|None=None
    document_commit:DocumentCommit|None=None
    document_id:UUID|None=None
    comparison_id:UUID|None=None
    rule_id:str|None=Field(default=None,max_length=32)
    expires_at:str|None=Field(default=None,max_length=40)
    @model_validator(mode='after')
    def source(self):
        if bool(self.document_commit)!=bool(self.document_id):raise ValueError('Document correction requires its document and typed commit together.')
        if self.document_commit and self.transaction:raise ValueError('Choose one correction path.')
        return self

class Reason(Strict):
    reason:str=Field(min_length=3,max_length=500)
class Retry(Reason):
    expected_attempts:int=Field(ge=0)
class Export(Strict):
    format:Literal['json','html','csv']='json'

def mount(app,settings,database,storage,identity,mutation):
    @app.get('/api/v1/reviews/{review_id}')
    def detail(review_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:
            operations.read_permission(ctx)
            row=finance.get(s,ReviewCase,ctx,review_id)
            return reviews.view(s,ctx,row)
    @app.post('/api/v1/reviews/{review_id}/assign')
    def assign(review_id:UUID,body:Assignment,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        def run(s):
            s.info['settings']=settings
            return reviews.assign(s,ctx,review_id,body.model_dump(mode='json'),request.state.correlation)
        return mutation(request,ctx,key,body.model_dump(mode='json'),200,run)
    @app.post('/api/v1/reviews/{review_id}/actions')
    def act(review_id:UUID,body:ReviewCommand,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),200,lambda s:reviews.act(s,ctx,review_id,body.model_dump(mode='json'),request.state.correlation))
    @app.get('/api/v1/transactions/{transaction_id}/review-history')
    def history(transaction_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:return operations.review_history(s,ctx,transaction_id)
    @app.get('/api/v1/transactions/{transaction_id}/timeline')
    def timeline(transaction_id:UUID,after_sequence:int=0,limit:int=50,ctx=Depends(identity)):
        with database.session(ctx) as s:return operations.timeline(s,ctx,transaction_id,after_sequence,limit)
    @app.get('/api/v1/operations/dashboard')
    def dashboard(ctx=Depends(identity)):
        with database.session(ctx) as s:return operations.dashboard(s,ctx)
    @app.get('/api/v1/operations/jobs')
    def jobs(state:Literal['FAILED','RETRYABLE','RUNNING']='FAILED',limit:int=50,offset:int=0,ctx=Depends(identity)):
        with database.session(ctx) as s:return operations.jobs(s,ctx,state,limit,offset)
    @app.post('/api/v1/operations/jobs/{kind}/{job_id}/retry')
    def retry(kind:Literal['finance','document'],job_id:UUID,body:Retry,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(),200,lambda s:operations.retry(s,ctx,kind,job_id,body.model_dump(),request.state.correlation))
    @app.get('/api/v1/operations/dependencies')
    def dependencies(ctx=Depends(identity)):
        operations.read_permission(ctx)
        return operations.dependencies(database,storage,settings,ctx)
    @app.post('/api/v1/operations/reconcile')
    def reconcile(body:Reason,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(),200,lambda s:operations.reconcile(s,ctx,storage,body.reason,request.state.correlation))
    @app.post('/api/v1/evaluations/{evaluation_id}/replay')
    def replay(evaluation_id:UUID,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,{},200,lambda s:operations.replay(s,ctx,evaluation_id,request.state.correlation))
    @app.post('/api/v1/evaluations/{evaluation_id}/exports')
    def export(evaluation_id:UUID,body:Export,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(),201,lambda s:operations.prepare_export(s,ctx,evaluation_id,body.format,request.state.correlation))
    @app.get('/api/v1/exports/{export_id}')
    def download(export_id:UUID,request:Request,ctx=Depends(identity)):
        with database.session(ctx) as s:
            data,media,filename=operations.download(s,ctx,export_id,request.state.correlation)
        return Response(data,media_type=media,headers={'Content-Disposition':f'attachment; filename="{filename}"','Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"sandbox; default-src 'none'; style-src 'unsafe-inline'"})
