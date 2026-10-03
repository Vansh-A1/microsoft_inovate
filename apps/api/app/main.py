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
from app.integrations.blob_storage import configured_storage
from app.schemas.canonical import Canonical, Revision, EvaluationRequest
from app.services import finance, imports


def create_app(settings=None,database=None):
    settings=settings or Settings.load();database=database or Database(settings.database_url);storage=configured_storage(settings)
    app=FastAPI(title='AP Exception Assistant',version='1.0.0',description='Versioned finance screening, governed intelligence and private source evidence; no payment execution')
    app.add_middleware(BoundedBody)
    app.state.database=database;app.state.settings=settings;database.settings=settings
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
    def identity(request:Request,authorization:Annotated[str|None,Header()]=None):
        if not settings.development and request.url.path.startswith('/api/v1/development/'):raise DomainError(404,'NOT_FOUND','Development actions are unavailable.')
        found=authenticate(authorization[7:] if authorization and authorization.startswith('Bearer ') else '',settings)
        if found is None:raise DomainError(401,'UNAUTHENTICATED','A verified scoped identity is required.')
        finance_paths=('/api/v1/overview','/api/v1/transactions','/api/v1/evaluations','/api/v1/evidence','/api/v1/documents','/api/v1/uploads','/api/v1/reviews','/api/v1/jobs','/api/v1/imports')
        if request.url.path.startswith(finance_paths) and not {'FINANCE_REVIEWER','AUDITOR','EMPLOYEE','FINANCE_CONTROLLER','MANAGER','DEPARTMENT_HEAD','DEPT_HEAD','CFO','DIRECTOR','APPROVER','OPERATIONS_ADMIN'}&found.roles:raise DomainError(403,'FORBIDDEN','Finance workspace access is required.')
        return found
    def writer(ctx=Depends(identity)):
        if 'FINANCE_REVIEWER' not in ctx.roles:raise DomainError(403,'FORBIDDEN','Finance reviewer permission is required.')
        return ctx
    def mutation(request,ctx,key,body,status,operation):
        with database.session(ctx) as session:
            response,code=finance.idempotent(session,ctx,request.url.path,key,body,status,lambda:operation(session))
        return JSONResponse(status_code=code,content=response)
    @app.get('/api/v1/health/live')
    def live():return {'status':'alive'}
    @app.get('/api/v1/health/ready')
    def ready():
        try:
            with database.engine.connect() as conn:version=conn.scalar(text('SELECT version_num FROM alembic_version'))
            if version!='0008_intelligence_audit':raise ValueError()
        except Exception:raise DomainError(503,'NOT_READY','Required persistence is unavailable.',retryable=True) from None
        return {'status':'ready'}
    @app.get('/api/v1/me')
    def me(ctx=Depends(identity)):return projection({'tenant_id':ctx.tenant_id,'legal_entity_id':ctx.legal_entity_id,'actor_id':ctx.actor_id,'roles':sorted(ctx.roles),'label':ctx.label,'development':settings.development})
    @app.get('/api/v1/references')
    def references(ctx=Depends(identity)):
        with database.session(ctx) as session:
            if not {'FINANCE_REVIEWER','AUDITOR','REFERENCE_ADMIN'}&ctx.roles:raise DomainError(403,'FORBIDDEN','Finance reference access is required.')
            return {'records':[{'id':str(r.id),'version':r.version,'kind':r.kind,'label':r.label,'payload':finance.redact(r.payload)} for r in session.scalars(scope_query(select(ReferenceRecord),ReferenceRecord,ctx)) if r.kind!='historical_transactions']}
    @app.get('/api/v1/development/templates/{branch}')
    def template(branch:str,ctx=Depends(identity)):
        if not settings.development:raise DomainError(404,'NOT_FOUND','Development fixtures are unavailable.')
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
            q=scope_query(select(Transaction.decision,func.count()).group_by(Transaction.decision),Transaction,ctx)
            if 'EMPLOYEE' in ctx.roles and not {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER'}&ctx.roles:q=q.join(TransactionVersion,TransactionVersion.transaction_id==Transaction.id).where(TransactionVersion.version==Transaction.latest_version,TransactionVersion.party_id==ctx.actor_id)
            rows=session.execute(q).all()
            counts={decision or 'PENDING':count for decision,count in rows}
            return {'counts':counts,'total':sum(counts.values())}
    @app.get('/api/v1/transactions')
    def transactions(decision:str|None=None,branch:str|None=None,limit:int=100,offset:int=0,ctx=Depends(identity)):
        if decision and decision not in ('PASS','REVIEW','HOLD'):raise DomainError(400,'FILTER_INVALID','Unknown screening decision.')
        if branch and branch not in ('VENDOR_INVOICE','EMPLOYEE_EXPENSE'):raise DomainError(400,'FILTER_INVALID','Unknown branch.')
        if not 1<=limit<=200 or not 0<=offset<=100000:raise DomainError(400,'FILTER_INVALID','Use a limit of 1–200 and bounded offset.')
        with database.session(ctx) as session:
            q=scope_query(select(Transaction),Transaction,ctx).order_by(Transaction.created_at.desc(),Transaction.id.desc()).offset(offset).limit(limit+1)
            if 'EMPLOYEE' in ctx.roles and not {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER'}&ctx.roles:q=q.join(TransactionVersion,TransactionVersion.transaction_id==Transaction.id).where(TransactionVersion.version==Transaction.latest_version,TransactionVersion.party_id==ctx.actor_id)
            if decision:q=q.where(Transaction.decision==decision)
            if branch:q=q.where(Transaction.branch==branch)
            items=finance.transaction_list(session,ctx,q)
            return {'items':items[:limit],'next_offset':offset+limit if len(items)>limit else None}
    @app.get('/api/v1/transactions/{record_id}')
    def transaction(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:return finance.transaction_detail(session,ctx,record_id)
    @app.post('/api/v1/transactions/{record_id}/revisions',status_code=201)
    def revision(record_id:UUID,body:Revision,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json');return mutation(request,ctx,key,data,201,lambda s:finance.revise(s,ctx,record_id,data,request.state.correlation))
    @app.post('/api/v1/transactions/{record_id}/evaluate',status_code=202)
    def evaluation(record_id:UUID,body:EvaluationRequest,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json')
        def run(s):
            finance.scope_lock(s,ctx)
            finance.review_guard(s,ctx,finance.get(s,Transaction,ctx,record_id),data)
            return finance.enqueue(s,ctx,record_id,body.expected_version,body.reason,request.state.correlation,key)
        return mutation(request,ctx,key,data,202,run)
    @app.get('/api/v1/jobs/{record_id}')
    def job(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:
            row=finance.get(session,Job,ctx,record_id)
            return projection({'id':row.id,'state':row.state,'stage':row.stage,'attempts':row.attempts,'maximum_attempts':row.maximum_attempts,'transaction_id':row.transaction_id,'transaction_version':row.transaction_version,'evaluation_id':row.result_evaluation_id,'last_error':row.last_error,'updated_at':row.updated_at})
    @app.get('/api/v1/evaluations/{record_id}')
    def evaluated(record_id:UUID,ctx=Depends(identity)):
        from app.services.operations import report_view
        with database.session(ctx) as session:return report_view(session,ctx,record_id)
    @app.get('/api/v1/evaluations/{record_id}/report')
    def report(record_id:UUID,format:str='json',ctx=Depends(identity)):
        from app.services.operations import report_view
        with database.session(ctx) as session:
            content=report_view(session,ctx,record_id)
            if format=='html':return HTMLResponse(finance.report_html(content).replace('<h2>Pinned evaluation metadata</h2>', '<p>Evaluation status: '+content['evaluation_status']+'. Current eligibility: '+str(content['current_eligible'])+'.</p><h2>Pinned evaluation metadata</h2>'),headers={'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'",'Cache-Control':'private, no-store'})
            if format!='json':raise DomainError(400,'FORMAT_INVALID','Use json or html.')
            # Preserve the original immutable JSON report contract. Live eligibility is
            # a separate evaluation projection and is labeled in HTML/export snapshots.
            return {k:v for k,v in content.items() if k not in ('current_eligible','evaluation_status','eligibility_reason','current_version','suggested_actions','current_eligibility_as_of')}
    @app.get('/api/v1/evidence/{record_id}')
    def evidence(record_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:
            row=finance.get(session,EvidenceObject,ctx,record_id);r=row.reference;rid=UUID(r['record_id']);kind=r['kind'];value=None
            if 'EMPLOYEE' in ctx.roles and not {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER'}&ctx.roles and kind=='HISTORICAL_AGGREGATE':return {'id':str(row.id),'reference':{'kind':kind},'source':{'cross_employee_details':'MASKED'},'source_image_available':False,'bbox':None}
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
            if value is None:
                from app.services.finance_controls import evidence as control_evidence
                value=control_evidence(session,ctx,rid)
            if value is None:raise DomainError(404,'EVIDENCE_UNAVAILABLE','The referenced scoped fact is unavailable.')
            return {'id':str(row.id),'reference':r,'source':value,'source_image_available':False,'bbox':None}
    @app.get('/api/v1/reviews')
    def reviews(decision:str|None=None,branch:str|None=None,reason:str|None=None,minimum_age_days:int=0,owner:str|None=None,state:str|None=None,processing_state:str|None=None,minimum_amount:str|None=None,maximum_amount:str|None=None,limit:int=50,offset:int=0,ctx=Depends(identity)):
        from app.services.operations import review_queue
        with database.session(ctx) as session:return review_queue(session,ctx,decision=decision,branch=branch,reason=reason,minimum_age_days=minimum_age_days,owner=owner,state=state,processing_state=processing_state,minimum_amount=minimum_amount,maximum_amount=maximum_amount,limit=limit,offset=offset)
    @app.get('/api/v1/audit')
    def audit(object_id:UUID|None=None,ctx=Depends(identity)):
        from app.services.operations import read_permission
        if 'EMPLOYEE' not in ctx.roles:read_permission(ctx)
        with database.session(ctx) as session:
            q=scope_query(select(AuditEvent),AuditEvent,ctx).order_by(AuditEvent.sequence).limit(200)
            if 'EMPLOYEE' in ctx.roles and not {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER'}&ctx.roles:q=q.where(AuditEvent.actor_id==ctx.actor_id)
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
    from app.finance_routes import mount as mount_finance_controls
    mount_finance_controls(app,database,identity,mutation)
    from app.finance_routes import mount_controls
    mount_controls(app,database,identity,mutation)
    from app.workflow_routes import mount as mount_workflow
    mount_workflow(app,settings,database,storage,identity,mutation)
    from app.risk_routes import mount as mount_intelligence
    mount_intelligence(app,database,identity,mutation)
    from app.admin_routes import mount as mount_admin
    mount_admin(app,database,identity,mutation)
    from app.core.observability import mount as mount_telemetry
    mount_telemetry(app)
    return app
