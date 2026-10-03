"""Local development API. Trusted server identities and PostgreSQL persistence."""
from datetime import timedelta
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import FastAPI, Depends, Header, UploadFile, File, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.exceptions import HTTPException
from app.core.limits import BoundedBody
from sqlalchemy import select, text, func
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import Settings
from app.core.identity import authenticate
from app.core.errors import DomainError
from app.core.serialization import projection, utcnow, digest
from app.db.session import Database, scope_query
from app.db.models import Transaction, Evaluation, Report, EvidenceObject, ReferenceRecord, TransactionVersion, ApprovalRecord, ImportRow, CapacityReservation, ReviewCase, Job, AuditEvent
from app.integrations.storage import LocalStorage
from app.schemas.canonical import Canonical, Revision, EvaluationRequest
from app.services import finance, imports


def create_app(settings=None,database=None):
    settings=settings or Settings.load();database=database or Database(settings.database_url);storage=LocalStorage(settings.storage_root)
    app=FastAPI(title='AP Exception Assistant',version='1.0.0',description='Synthetic development / RULES_ONLY / no payment execution')
    app.add_middleware(BoundedBody)
    app.state.database=database;app.state.settings=settings
    @app.exception_handler(HTTPException)
    async def http_error(request,exc):
        return JSONResponse(status_code=exc.status_code,content={'error':{'code':'HTTP_'+str(exc.status_code),'message':'Request route or method is unavailable.' if exc.status_code in (404,405) else 'Request could not be processed.','details':{},'retryable':False},'correlation_id':getattr(request.state,'correlation','')})
    @app.exception_handler(DomainError)
    async def domain_error(request,exc):
        return JSONResponse(status_code=exc.status,content={'error':{'code':exc.code,'message':exc.message,'details':exc.details,'retryable':exc.retryable},'correlation_id':getattr(request.state,'correlation','')})
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        errors=[{'field':'.'.join(str(v) for v in e['loc']),'code':e['type'],'message':e['msg']} for e in exc.errors()]
        return JSONResponse(status_code=422,content={'error':{'code':'VALIDATION_ERROR','message':'Structured input is invalid.','details':errors,'retryable':False},'correlation_id':getattr(request.state,'correlation','')})
    @app.exception_handler(SQLAlchemyError)
    async def database_error(request,exc):
        return JSONResponse(status_code=503,content={'error':{'code':'DATABASE_UNAVAILABLE','message':'Persistence is temporarily unavailable.','details':None,'retryable':True},'correlation_id':getattr(request.state,'correlation','')})
    @app.middleware('http')
    async def correlation(request,call_next):
        request.state.correlation=str(uuid4());response=await call_next(request);response.headers['X-Correlation-ID']=request.state.correlation;return response
    def identity(authorization:Annotated[str|None,Header()]=None):
        found=authenticate(authorization[7:] if authorization and authorization.startswith('Bearer ') else '',settings)
        if found is None:raise DomainError(401,'UNAUTHENTICATED','A trusted development identity is required.')
        return found
    def writer(ctx=Depends(identity)):
        if 'FINANCE_REVIEWER' not in ctx.roles:raise DomainError(403,'FORBIDDEN','Finance reviewer permission is required.')
        return ctx
    def mutation(request,ctx,key,body,status,operation):
        with database.session(ctx) as session:
            response,code=finance.idempotent(session,ctx,request.url.path,key,body,status,lambda:operation(session))
        return JSONResponse(status_code=code,content=response)
    @app.get('/api/v1/health/live')
    def live():return {'status':'alive','mode':'RULES_ONLY','extraction':'STRUCTURED_SYNTHETIC','model_status':'NOT_CONFIGURED',
        'document_pipeline':'document-pipeline-v1','document_providers':{'native_text':'AVAILABLE','ocr':'CONFIGURED' if settings.document_providers.ocr_executable else 'NOT_CONFIGURED',
            'enterprise_vlm':'CONFIGURED_UNVERIFIED' if settings.document_providers.endpoint else 'NOT_CONFIGURED'},'malware':'NOT_CONFIGURED','enterprise_runtime':'DEFERRED_EXTERNAL_HOST'}
    @app.get('/api/v1/health/ready')
    def ready():
        try:
            with database.engine.connect() as conn:version=conn.scalar(text('SELECT version_num FROM alembic_version'))
            if version!='0004_documents':raise ValueError()
        except Exception:raise DomainError(503,'NOT_READY','Apply the database migration before serving requests.',retryable=True) from None
        return {'status':'ready','database':'PostgreSQL','migration':version}
    @app.get('/api/v1/me')
    def me(ctx=Depends(identity)):return projection({'tenant_id':ctx.tenant_id,'legal_entity_id':ctx.legal_entity_id,'actor_id':ctx.actor_id,'roles':sorted(ctx.roles),'label':ctx.label,'development':True})
    @app.get('/api/v1/references')
    def references(ctx=Depends(identity)):
        with database.session(ctx) as session:
            return {'records':[{'id':str(r.id),'version':r.version,'kind':r.kind,'label':r.label,'payload':finance.redact(r.payload)} for r in session.scalars(scope_query(select(ReferenceRecord),ReferenceRecord,ctx)) if r.kind!='historical_transactions']}
    @app.get('/api/v1/development/templates/{branch}')
    def template(branch:str,ctx=Depends(identity)):
        if branch not in ('vendor','employee'):raise DomainError(400,'BRANCH_INVALID','Use vendor or employee.')
        from app.core.config import ROOT
        from app.schemas.canonical import fixture_canonical
        import json
        case='vendor/clean' if branch=='vendor' else 'employee/clean_taxi'
        return fixture_canonical(json.loads((ROOT/f'data/golden_cases/{case}.json').read_text())['transaction'])
    @app.post('/api/v1/transactions',status_code=201)
    def create(body:Canonical,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        payload=body.model_dump(mode='json')
        return mutation(request,ctx,key,payload,201,lambda s:finance.create_transaction(s,ctx,payload,'Structured synthetic intake',request.state.correlation))
    @app.get('/api/v1/overview')
    def overview(ctx=Depends(identity)):
        with database.session(ctx) as session:
            rows=session.execute(scope_query(select(Transaction.decision,func.count()).group_by(Transaction.decision),Transaction,ctx)).all()
            counts={decision or 'PENDING':count for decision,count in rows}
            return {'counts':counts,'total':sum(counts.values())}
    @app.get('/api/v1/transactions')
    def transactions(decision:str|None=None,branch:str|None=None,limit:int=100,ctx=Depends(identity)):
        if decision and decision not in ('PASS','REVIEW','HOLD'):raise DomainError(400,'FILTER_INVALID','Unknown screening decision.')
        if branch and branch not in ('VENDOR_INVOICE','EMPLOYEE_EXPENSE'):raise DomainError(400,'FILTER_INVALID','Unknown branch.')
        if not 1<=limit<=200:raise DomainError(400,'FILTER_INVALID','Limit must be 1–200.')
        with database.session(ctx) as session:
            q=scope_query(select(Transaction),Transaction,ctx).order_by(Transaction.created_at.desc()).limit(limit)
            if decision:q=q.where(Transaction.decision==decision)
            if branch:q=q.where(Transaction.branch==branch)
            return {'items':finance.transaction_list(session,ctx,q)}
    @app.get('/api/v1/transactions/{record_id}')
    def transaction(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:return finance.transaction_detail(session,ctx,record_id)
    @app.post('/api/v1/transactions/{record_id}/revisions',status_code=201)
    def revision(record_id:UUID,body:Revision,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json');return mutation(request,ctx,key,data,201,lambda s:finance.revise(s,ctx,record_id,data,request.state.correlation))
    @app.post('/api/v1/transactions/{record_id}/evaluate',status_code=202)
    def evaluation(record_id:UUID,body:EvaluationRequest,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json');return mutation(request,ctx,key,data,202,lambda s:finance.enqueue(s,ctx,record_id,body.expected_version,body.reason,request.state.correlation,key))
    @app.get('/api/v1/jobs/{record_id}')
    def job(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:
            row=finance.get(session,Job,ctx,record_id)
            return projection({'id':row.id,'state':row.state,'stage':row.stage,'attempts':row.attempts,'maximum_attempts':row.maximum_attempts,'transaction_id':row.transaction_id,'transaction_version':row.transaction_version,'evaluation_id':row.result_evaluation_id,'last_error':row.last_error,'updated_at':row.updated_at})
    @app.get('/api/v1/evaluations/{record_id}')
    def evaluated(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:
            row=finance.get(session,Evaluation,ctx,record_id);transaction=finance.get(session,Transaction,ctx,row.transaction_id)
            report=session.scalar(scope_query(select(Report),Report,ctx).where(Report.evaluation_id==row.id))
            return report.content|{'current_eligible':transaction.eligible and transaction.latest_evaluation_id==row.id,'current_version':transaction.latest_version}
    @app.get('/api/v1/evaluations/{record_id}/report')
    def report(record_id:UUID,format:str='json',ctx=Depends(identity)):
        with database.session(ctx) as session:
            finance.get(session,Evaluation,ctx,record_id);row=session.scalar(scope_query(select(Report),Report,ctx).where(Report.evaluation_id==record_id))
            if format=='html':return HTMLResponse(row.html,headers={'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'"})
            if format!='json':raise DomainError(400,'FORMAT_INVALID','Use json or html.')
            return row.content
    @app.get('/api/v1/evidence/{record_id}')
    def evidence(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:
            row=finance.get(session,EvidenceObject,ctx,record_id);r=row.reference;rid=UUID(r['record_id']);kind=r['kind'];value=None
            if kind=='DOCUMENT_FIELD':
                from app.db.document_models import DocumentVersion
                original=session.scalar(scope_query(select(DocumentVersion),DocumentVersion,ctx).where(DocumentVersion.id==rid,DocumentVersion.version==r['record_version']))
                if original:
                    from app.services import documents
                    document=documents.detail(session,ctx,rid)
                    return {'id':str(row.id),'reference':r,'source':{'original':document['original'],'observations':document['observations'],'draft':document['draft']},
                        'document':document,'source_image_available':bool(document['pages']) and document['state']!='QUARANTINED',
                        'preview_url':f'/api/v1/documents/{rid}/pages/{r["page"]}/preview' if r.get('page') else None,'bbox':r.get('bbox')}
            if kind=='TRANSACTION':
                version=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,ctx).where(TransactionVersion.transaction_id==rid,TransactionVersion.version==r['record_version']));value=finance.redact(version.payload) if version else None
            elif kind=='APPROVAL':
                a=finance.get(session,ApprovalRecord,ctx,rid);value=projection({'id':a.id,'actor_id':a.actor_id,'role':a.role,'state':a.state,'transaction_version':a.transaction_version,'approved_at':a.approved_at})
            elif kind=='IMPORT_CELL':
                source=finance.get(session,ImportRow,ctx,rid);value={'raw_values':source.raw_values,'row_digest':source.row_digest,'sheet':source.sheet,'row_number':source.row_number}
                from app.db.document_models import ImportCell
                locator=r.get('import_cell') or {}
                cell=session.scalar(scope_query(select(ImportCell),ImportCell,ctx).where(ImportCell.row_id==rid,ImportCell.column==locator.get('column')))
                if cell:value['cell']={'column':cell.column,'field_path':cell.field_path,'raw_value':cell.raw_value,'parsed_value':cell.parsed_value,'validation':cell.validation}
            else:
                reference=session.scalar(scope_query(select(ReferenceRecord),ReferenceRecord,ctx).where(ReferenceRecord.id==rid,ReferenceRecord.version==r['record_version']))
                if reference:value=finance.redact(reference.payload)
                elif kind=='HISTORICAL_AGGREGATE':
                    reservation=session.scalar(scope_query(select(CapacityReservation),CapacityReservation,ctx).where(CapacityReservation.id==rid))
                    if reservation:value=projection({'id':reservation.id,'evaluation_id':reservation.evaluation_id,'transaction_id':reservation.transaction_id,'reference_id':reservation.reference_id,'amount':reservation.amount,'quantity':reservation.quantity,'state':reservation.state})
                    else:
                        version=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,ctx).where(TransactionVersion.transaction_id==rid,TransactionVersion.version==r['record_version']));value=finance.redact(version.payload) if version else None
            if value is None:raise DomainError(404,'EVIDENCE_UNAVAILABLE','The referenced scoped fact is unavailable.')
            return {'id':str(row.id),'reference':r,'source':value,'source_image_available':False,'bbox':None}
    @app.get('/api/v1/reviews')
    def reviews(decision:str|None=None,branch:str|None=None,reason:str|None=None,minimum_age_days:int=0,ctx=Depends(identity)):
        if minimum_age_days<0 or minimum_age_days>3650:raise DomainError(400,'FILTER_INVALID','Age must be 0–3650 days.')
        with database.session(ctx) as session:
            q=scope_query(select(ReviewCase),ReviewCase,ctx).where(ReviewCase.state=='OPEN',ReviewCase.created_at<=utcnow()-timedelta(days=minimum_age_days)).order_by(ReviewCase.created_at).limit(200)
            if decision:q=q.where(ReviewCase.decision==decision)
            if branch:q=q.where(ReviewCase.branch==branch)
            return {'items':[projection({'id':r.id,'transaction_id':r.transaction_id,'evaluation_id':r.evaluation_id,'decision':r.decision,'branch':r.branch,'reasons':r.reasons,'created_at':r.created_at}) for r in session.scalars(q) if not reason or reason in r.reasons]}
    @app.get('/api/v1/audit')
    def audit(object_id:UUID|None=None,ctx=Depends(identity)):
        with database.session(ctx) as session:
            q=scope_query(select(AuditEvent),AuditEvent,ctx).order_by(AuditEvent.sequence).limit(200)
            if object_id:q=q.where(AuditEvent.object_id==object_id)
            return {'items':[projection({'id':r.id,'sequence':r.sequence,'action':r.action,'object_id':r.object_id,'version':r.object_version,'actor_id':r.actor_id,'reason':r.reason,'correlation_id':r.correlation_id,'created_at':r.created_at,'previous_hash':r.previous_hash,'event_hash':r.event_hash}) for r in session.scalars(q)]}
    @app.post('/api/v1/imports/preview',status_code=201)
    async def preview(request:Request,file:UploadFile=File(...),mapping_json:str|None=Form(None),defaults_json:str|None=Form(None),date_order:str|None=Form(None),ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        content=await file.read(2*1024*1024+1);filename=file.filename or 'upload.csv'
        if mapping_json:
            import json
            from app.services import import_mapping
            try:
                mapping=json.loads(mapping_json);defaults=Canonical.model_validate(json.loads(defaults_json or '{}')).model_dump(mode='json')
                if not isinstance(mapping,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in mapping.items()) or date_order not in (None,'DMY','MDY'):raise ValueError()
            except (ValueError,TypeError):raise DomainError(422,'MAPPING_INVALID','Supply an explicit column-to-field mapping, canonical defaults and optional DMY/MDY date order.') from None
            return mutation(request,ctx,key,{'filename':filename,'digest':digest(content.hex()),'mapping':mapping,'defaults':defaults,'date_order':date_order},201,
                lambda s:import_mapping.preview(s,ctx,storage,filename,content,mapping,defaults,date_order,request.state.correlation))
        return mutation(request,ctx,key,{'filename':filename,'digest':digest(content.hex())},201,lambda s:imports.preview(s,ctx,storage,filename,content,request.state.correlation))
    @app.post('/api/v1/imports/{record_id}/commit')
    def import_commit(record_id:UUID,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,{'batch_id':str(record_id)},200,lambda s:imports.commit(s,ctx,record_id,request.state.correlation))
    @app.get('/api/v1/imports/{record_id}')
    def import_status(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:return imports.detail(session,ctx,record_id)
    from app.documents.routes import mount
    mount(app,settings,database,storage,identity,writer,mutation)
    return app
