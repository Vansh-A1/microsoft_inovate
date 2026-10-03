"""Authenticated document routes mounted onto the existing application."""
from typing import Annotated, Literal
from uuid import UUID
from fastapi import Depends, Header, Request
from fastapi.responses import Response
from pydantic import Field
from sqlalchemy import select
from app.schemas.canonical import Strict
from app.services import documents
from app.services.finance import get
from app.db.document_models import Document, DocumentVersion, DocumentPage
from app.db.session import scope_query
from app.core.errors import DomainError


class UploadRequest(Strict):
    filename: str = Field(min_length=1,max_length=160)
    mime: Literal['application/pdf','image/png','image/jpeg']
    source_type: Literal['VENDOR_INVOICE','EMPLOYEE_RECEIPT','SUPPORTING_DOCUMENT']


def mount(app,settings,database,storage,identity,writer,mutation):
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
            rows=session.scalars(scope_query(select(Document),Document,ctx).order_by(Document.created_at.desc()).limit(100))
            return {'items':[{'id':str(d.id),'display_name':d.display_name,'source_type':d.source_type,'state':d.state,'last_error':d.last_error} for d in rows]}

    @app.get('/api/v1/documents/{document_id}')
    def detail(document_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:return documents.detail(session,ctx,document_id)

    @app.get('/api/v1/documents/{document_id}/original')
    def original(document_id:UUID,ctx=Depends(identity)):
        with database.session(ctx) as session:
            doc=get(session,Document,ctx,document_id)
            if doc.state=='QUARANTINED': raise DomainError(409,'QUARANTINED','Quarantined content is unavailable for download.')
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
