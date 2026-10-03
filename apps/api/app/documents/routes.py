"""Authenticated document routes mounted onto the existing application."""
from typing import Annotated, Literal
from uuid import UUID
from fastapi import Depends, Header, Request
from fastapi.responses import Response
from pydantic import Field, model_validator
from sqlalchemy import select
from app.schemas.canonical import Strict, Canonical
from app.services import documents
from app.services.finance import get
from app.db.document_models import Document, DocumentVersion, DocumentPage
from app.db.session import scope_query
from app.core.errors import DomainError
from app.services import document_facts


class UploadRequest(Strict):
    filename: str = Field(min_length=1,max_length=160)
    mime: Literal['application/pdf','image/png','image/jpeg']
    source_type: Literal['VENDOR_INVOICE','EMPLOYEE_RECEIPT','SUPPORTING_DOCUMENT']


class FieldCorrection(Strict):
    field_path: str = Field(min_length=1,max_length=160)
    value: str = Field(min_length=1,max_length=500)
    page: int = Field(ge=1,le=30)
    reason: str = Field(min_length=3,max_length=500)


class DocumentCommit(Strict):
    draft_id: UUID
    transaction: Canonical
    source_confirmed: bool
    reason: str = Field(min_length=3,max_length=500)
    corrections: list[FieldCorrection] = Field(default_factory=list,max_length=500)
    first_page: int = Field(default=1,ge=1,le=30)
    last_page: int | None = Field(default=None,ge=1,le=30)
    date_order: Literal['DMY','MDY'] | None = None
    transaction_id: UUID | None = None
    expected_version: int | None = Field(default=None,ge=1)

    @model_validator(mode='after')
    def bounded_identity(self):
        if bool(self.transaction_id)!=bool(self.expected_version):raise ValueError('Revision requires transaction UUID and expected version together.')
        if len({c.field_path for c in self.corrections})!=len(self.corrections):raise ValueError('Each field may be corrected once per request.')
        return self


class Attachment(Strict):
    expected_version: int = Field(ge=1)
    document_id: UUID
    role: Literal['INVOICE','RECEIPT','PO','SUPPORT']
    item_index: int | None = Field(default=None,ge=0,le=199)
    first_page: int = Field(default=1,ge=1,le=30)
    last_page: int | None = Field(default=None,ge=1,le=30)
    reason: str = Field(min_length=3,max_length=500)


def mount(app,settings,database,storage,identity,writer,mutation):
    @app.post('/api/v1/documents/{document_id}/commit',status_code=201)
    def commit(document_id:UUID,body:DocumentCommit,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json')
        return mutation(request,ctx,key,data,201,lambda s:document_facts.commit(s,ctx,document_id,data,request.state.correlation))

    @app.get('/api/v1/transactions/{transaction_id}/sources')
    def sources(transaction_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:return document_facts.sources(session,ctx,transaction_id)

    @app.post('/api/v1/transactions/{transaction_id}/attachments',status_code=201)
    def attach(transaction_id:UUID,body:Attachment,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json')
        return mutation(request,ctx,key,data,201,lambda s:document_facts.attach(s,ctx,transaction_id,data,request.state.correlation))
    @app.post('/api/v1/uploads',status_code=201)
    def create(body:UploadRequest,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        data=body.model_dump(mode='json')
        return mutation(request,ctx,key,data,201,lambda s:documents.create_upload(s,ctx,data,settings.document_limits,request.state.correlation))

    @app.post('/api/v1/uploads/{upload_id}/bytes')
    async def upload(upload_id:UUID,request:Request,ctx=Depends(writer)):
        return await documents.store_bytes(database,ctx,upload_id,storage,request.stream(),settings.document_limits,request.state.correlation)

    @app.post('/api/v1/uploads/{upload_id}/finalize',status_code=202)
    def finalize(upload_id:UUID,request:Request,ctx=Depends(writer),key:Annotated[str|None,Header(alias='Idempotency-Key')]=None):
        return mutation(request,ctx,key,{'upload_id':str(upload_id)},202,
            lambda s:documents.finalize_upload(s,ctx,upload_id,storage,settings.document_limits,request.state.correlation))

    @app.get('/api/v1/documents')
    def listing(ctx=Depends(identity)):
        with database.session(ctx) as session:
            q=scope_query(select(Document),Document,ctx).order_by(Document.created_at.desc()).limit(100)
            if 'EMPLOYEE' in ctx.roles and not {'FINANCE_REVIEWER','AUDITOR','FINANCE_CONTROLLER'}&ctx.roles:q=q.where(Document.actor_id==ctx.actor_id)
            rows=session.scalars(q)
            return {'items':[{'id':str(d.id),'display_name':d.display_name,'source_type':d.source_type,'state':d.state,'last_error':d.last_error} for d in rows]}

    @app.get('/api/v1/documents/{document_id}')
    def detail(document_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:return documents.detail(session,ctx,document_id)

    @app.get('/api/v1/documents/{document_id}/original')
    def original(document_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:
            doc=get(session,Document,ctx,document_id)
            if doc.state=='QUARANTINED': raise DomainError(409,'QUARANTINED','Quarantined content is unavailable for download.')
            if not doc.last_successful_stage:raise DomainError(409,'SOURCE_NOT_READY','Safety preprocessing must finish before downloading the original.')
            row=session.scalar(scope_query(select(DocumentVersion),DocumentVersion,ctx).where(DocumentVersion.id==doc.id,DocumentVersion.version==1))
            if row is None:raise DomainError(404,'NOT_FOUND','No finalized original.')
            return Response(storage.get(ctx,row.storage_key),media_type=row.detected_mime,headers={
                'Content-Disposition':f'attachment; filename="document-{doc.id}"','X-Content-Type-Options':'nosniff','Cache-Control':'private, no-store',
                'Content-Security-Policy':"sandbox; default-src 'none'"})

    @app.get('/api/v1/documents/{document_id}/pages/{page}/preview')
    def preview(document_id:UUID,page:int,ctx=Depends(identity)):
        with database.session(ctx) as session:
            doc=get(session,Document,ctx,document_id)
            if doc.state=='QUARANTINED':raise DomainError(409,'QUARANTINED','Quarantined content has no viewable source.')
            row=session.scalar(scope_query(select(DocumentPage),DocumentPage,ctx).where(DocumentPage.document_id==doc.id,DocumentPage.document_version==1,DocumentPage.page==page))
            if row is None:raise DomainError(404,'NOT_FOUND','Source page is unavailable.')
            return Response(storage.get(ctx,row.preview_key),media_type='image/png',headers={'X-Content-Type-Options':'nosniff','Cache-Control':'private, no-store'})
