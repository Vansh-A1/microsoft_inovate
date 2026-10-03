"""Typed, authorized intelligence boundaries; all mutations use existing idempotency."""
from typing import Literal,Annotated
from uuid import UUID
from decimal import Decimal,InvalidOperation
from fastapi import Depends,Header,Request
from pydantic import Field,field_validator
from app.schemas.canonical import Strict
from app.workflow_routes import ReviewWrite,Reason
from app.services import intelligence as ml
from app.db.risk_models import DatasetVersion,ModelVersion
from app.core.errors import DomainError
from app.services import finance

class HistoryPin(Strict):
    id:UUID
    version:int=Field(ge=1)
class History(Reason):
    records:list[HistoryPin]=Field(min_length=1,max_length=10000)
class Feedback(ReviewWrite):
    label:Literal['CLEAN_CONFIRMED','DUPLICATE_CONFIRMED','POLICY_EXCEPTION','DOCUMENT_CORRECTION_ONLY','DISTINCT_CONFIRMED','INSUFFICIENT_INFORMATION']
    expected_label_id:UUID|None=None
    evidence_ids:list[UUID]=Field(min_length=1,max_length=20)
class Window(Reason):
    start:str=Field(max_length=40)
    end:str=Field(max_length=40)
    @field_validator('start','end')
    @classmethod
    def instant_bound(cls,v):
        try:ml.features.instant(v)
        except (ValueError,TypeError):raise ValueError('Use an explicit ISO timestamp with a timezone.') from None
        return v
class Sample(Window):
    campaign:str=Field(min_length=3,max_length=80,pattern='^[A-Za-z0-9_-]+$')
    rate:str=Field(max_length=20)
    @field_validator('rate')
    @classmethod
    def rate_bound(cls,v):
        try:amount=Decimal(v)
        except InvalidOperation:raise ValueError('Rate must be an exact decimal in (0,1].') from None
        if not amount.is_finite() or not 0<amount<=1:raise ValueError('Rate must be an exact decimal in (0,1].')
        return v
class Dataset(Reason):
    train_end:str=Field(max_length=40)
    validation_end:str=Field(max_length=40)
    test_end:str=Field(max_length=40)
    heldout_parties:list[UUID]=Field(default_factory=list,max_length=1000)
    @field_validator('train_end','validation_end','test_end')
    @classmethod
    def instant_bound(cls,v):
        try:ml.features.instant(v)
        except (ValueError,TypeError):raise ValueError('Use an explicit ISO timestamp with a timezone.') from None
        return v
class Training(Reason):
    dataset_id:UUID
    supervised:bool=False
class Transition(Reason):
    expected_version:int=Field(ge=1)
    state:Literal['EVALUATED','APPROVED','RETIRED','REJECTED']
class Deployment(Reason):
    expected_version:int=Field(ge=0)
    mode:Literal['RULES_ONLY','SHADOW','RULES_PLUS_ANOMALY','RULES_PLUS_MODEL']
    model_id:UUID|None=None
    threshold:str='60.0'
    @field_validator('threshold')
    @classmethod
    def threshold_bound(cls,v):
        try:amount=Decimal(v)
        except InvalidOperation:raise ValueError('Anomaly threshold must be an exact decimal in (0,100].') from None
        if len(v)>20 or not amount.is_finite() or not 0<amount<=100:raise ValueError('Anomaly threshold must be an exact decimal in (0,100].')
        return v
class Rollback(Reason):
    expected_version:int=Field(ge=1)
    target_id:UUID
class Monitoring(Window):
    dataset_id:UUID|None=None

def mount(app,database,identity,mutation):
    @app.get('/api/v1/intelligence/status')
    def status(ctx=Depends(identity)):
        with database.session(ctx) as s:
            current=ml.deployment(s,ctx)
            available='NOT_CONFIGURED'
            if current and current.mode!='RULES_ONLY':
                available='MODEL_UNAVAILABLE'
                if current.model_id:
                    try:
                        ml.load_artifact(s,ctx,finance.get(s,ModelVersion,ctx,current.model_id))
                        available='AVAILABLE'
                    except (ValueError,OSError,DomainError):pass
            return {'mode':current.mode if current else 'RULES_ONLY','status':available,'configuration_version':current.version if current else 0}
    @app.get('/api/v1/evaluations/{evaluation_id}/intelligence')
    def inspect(evaluation_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as s:return ml.inspect(s,ctx,evaluation_id)
    @app.get('/api/v1/intelligence/registry')
    def registry(ctx=Depends(identity)):
        with database.session(ctx) as s:return ml.registry(s,ctx)
    @app.get('/api/v1/intelligence/datasets/{dataset_id}')
    def dataset(dataset_id:UUID,ctx=Depends(identity)):
        ml.require(ctx,{'ML_ADMIN','ML_GOVERNANCE','AUDITOR'})
        with database.session(ctx) as s:return ml.dataset_view(finance.get(s,DatasetVersion,ctx,dataset_id))
    @app.post('/api/v1/intelligence/history')
    def history(body:History,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),200,lambda s:ml.register_history(s,ctx,body.model_dump(mode='json')['records'],body.reason,request.state.correlation))
    @app.post('/api/v1/reviews/{review_id}/feedback')
    def feedback(review_id:UUID,body:Feedback,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),201,lambda s:ml.feedback(s,ctx,review_id,body.model_dump(mode='json'),request.state.correlation))
    @app.post('/api/v1/intelligence/pass-samples')
    def sample(body:Sample,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),201,lambda s:ml.sample_pass(s,ctx,body.model_dump(mode='json'),request.state.correlation))
    @app.post('/api/v1/intelligence/datasets')
    def datasets(body:Dataset,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),201,lambda s:ml.create_dataset(s,ctx,body.model_dump(mode='json'),request.state.correlation))
    @app.post('/api/v1/intelligence/training-runs')
    def train(body:Training,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),201,lambda s:ml.build_candidate(s,ctx,body.dataset_id,body.reason,request.state.correlation,body.supervised))
    @app.post('/api/v1/intelligence/models/{model_id}/events')
    def events(model_id:UUID,body:Transition,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),200,lambda s:ml.transition(s,ctx,model_id,body.model_dump(mode='json'),request.state.correlation))
    @app.post('/api/v1/intelligence/deployments')
    def deploy(body:Deployment,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),201,lambda s:ml.deploy(s,ctx,body.model_dump(mode='json'),request.state.correlation))
    @app.post('/api/v1/intelligence/rollback')
    def rollback(body:Rollback,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),201,lambda s:ml.rollback(s,ctx,body.model_dump(mode='json'),request.state.correlation))
    @app.post('/api/v1/intelligence/monitoring')
    def monitoring(body:Monitoring,request:Request,ctx=Depends(identity),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,body.model_dump(mode='json'),201,lambda s:ml.monitor(s,ctx,body.model_dump(mode='json'),request.state.correlation))
