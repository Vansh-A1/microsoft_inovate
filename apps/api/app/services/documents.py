"""Two-step private source intake. Filename, checksum and role are never authority."""
from datetime import timedelta
import hashlib
from pathlib import PurePath
from uuid import uuid4
from sqlalchemy import select
from app.core.errors import DomainError
from app.core.serialization import projection, utcnow, digest
from app.db.document_models import Document, UploadSession, DocumentVersion, DocumentPage, DocumentJob, DocumentOutbox, ExtractionRun, Observation, DocumentDraft
from app.db.session import scope_query, advisory_lock
from app.services.finance import get, audit
from app.documents.processor import sniff, DocumentFailure

PIPELINE_VERSION = 'document-pipeline-v1'
STAGES = ('PREPROCESS','EXTRACT','NORMALIZE','VALIDATE','FINALIZE')
MIMES = {'application/pdf': {'.pdf'}, 'image/png': {'.png'}, 'image/jpeg': {'.jpg','.jpeg'}}


def create_upload(session, identity, body, limits, correlation):
    name = PurePath(body['filename'].replace('\\','/')).name
    if body['mime'] not in MIMES or PurePath(name).suffix.lower() not in MIMES[body['mime']]:
        raise DomainError(400,'DOCUMENT_FORMAT','Declare PDF, PNG or JPEG with a matching filename.')
    if any(ord(c) < 32 for c in name): raise DomainError(400,'DOCUMENT_NAME','Control characters are unsupported.')
    document = Document(**identity.scope(), id=uuid4(), source_type='SUPPORTING_DOCUMENT' if body['source_type']=='AUTO' else body['source_type'], display_name=name[:160])
    session.add(document); session.flush()
    upload = UploadSession(**identity.scope(),id=uuid4(),document_id=document.id,actor_id=identity.actor_id,
        correlation_id=correlation,declared_mime=body['mime'],expires_at=utcnow()+timedelta(seconds=limits.upload_lifetime_seconds))
    session.add(upload); session.flush()
    audit(session,identity,'UPLOAD_SESSION_CREATED',document.id,1,'Private document upload session created',correlation,{'intake_hint':body['source_type']})
    return projection({'id':upload.id,'document_id':document.id,'state':upload.state,'expires_at':upload.expires_at,
        'maximum_bytes':limits.maximum_bytes,'bytes_url':f'/api/v1/uploads/{upload.id}/bytes'})


async def store_bytes(database, identity, upload_id, storage, chunks, limits, correlation):
    # Hold one scoped upload row lock while streaming; other sessions cannot replace it.
    with database.session(identity) as session:
        upload = session.scalar(scope_query(select(UploadSession),UploadSession,identity).where(UploadSession.id==upload_id).with_for_update())
        if upload is None: raise DomainError(404,'NOT_FOUND','Scoped upload is unavailable.')
        if upload.actor_id != identity.actor_id: raise DomainError(403,'FORBIDDEN','Only the upload actor can store bytes.')
        if upload.state not in ('OPEN','UPLOADED') or upload.expires_at <= utcnow():
            raise DomainError(409,'UPLOAD_CLOSED','Upload is closed or expired.')
        doc = get(session,Document,identity,upload.document_id)
        try: key, checksum, size = await storage.ingest(identity,chunks,maximum=limits.maximum_bytes,timeout_seconds=limits.upload_receive_timeout_seconds)
        except (ValueError,TimeoutError) as exc:
            code = 'UPLOAD_TIMEOUT' if isinstance(exc,TimeoutError) else str(exc) if str(exc) in ('DOCUMENT_SIZE_LIMIT','EMPTY_DOCUMENT') else 'UPLOAD_FAILED'
            if upload.state=='OPEN': upload.state='QUARANTINED';doc.state='QUARANTINED';doc.last_error=code
            audit(session,identity,'UPLOAD_REJECTED',doc.id,1,'Bounded binary intake rejected',correlation,{'code':code})
            return {'id':str(doc.id),'state':doc.state,'error':code}
        if upload.state=='UPLOADED':
            # The duplicate stream is an owned, unreferenced object; original never replaced.
            storage.path(identity,key).unlink()
            if upload.sha256 != checksum: raise DomainError(409,'UPLOAD_CONTENT_CONFLICT','Stored upload content is immutable.')
        else:
            upload.storage_key=key;upload.sha256=checksum;upload.byte_size=size;upload.state='UPLOADED';doc.state='UPLOADED'
            audit(session,identity,'ORIGINAL_STORED',doc.id,1,'Original bytes preserved with authoritative SHA-256',correlation,{'sha256':checksum,'bytes':size})
        return {'id':str(doc.id),'upload_id':str(upload.id),'state':doc.state,'sha256':upload.sha256,'byte_size':upload.byte_size}


def enqueue_stage(session, identity, doc, stage, actor, correlation):
    key=digest({'document':str(doc.id),'version':1,'generation':doc.generation,'stage':stage,'version_key':PIPELINE_VERSION})
    found=session.scalar(scope_query(select(DocumentJob),DocumentJob,identity).where(DocumentJob.stage_key==key))
    if found: return found
    job=DocumentJob(**identity.scope(),id=uuid4(),document_id=doc.id,document_version=1,generation=doc.generation,
        stage=stage,stage_version=PIPELINE_VERSION,stage_key=key,actor_id=actor,correlation_id=correlation)
    session.add(job);session.flush();session.add(DocumentOutbox(**identity.scope(),job_id=job.id));session.flush()
    return job


def finalize_upload(session, identity, upload_id, storage, limits, correlation):
    advisory_lock(session,f'upload:{upload_id}')
    upload=get(session,UploadSession,identity,upload_id);doc=get(session,Document,identity,upload.document_id)
    if upload.actor_id != identity.actor_id: raise DomainError(403,'FORBIDDEN','Only the upload actor can finalize.')
    if upload.state in ('FINALIZED','QUARANTINED'): return detail(session,identity,doc.id)
    if upload.state != 'UPLOADED': raise DomainError(409,'UPLOAD_INCOMPLETE','Store document bytes before finalization.')
    if upload.expires_at <= utcnow():
        upload.state='EXPIRED';doc.state='NEEDS_INPUT';doc.last_error='UPLOAD_EXPIRED'
        audit(session,identity,'UPLOAD_EXPIRED',doc.id,1,'Expired upload was not scheduled',correlation)
        return detail(session,identity,doc.id)
    path=storage.path(identity,upload.storage_key)
    checksum=hashlib.sha256();size=0
    with path.open('rb') as stream:
        first=stream.read(512);checksum.update(first);size=len(first)
        while chunk:=stream.read(65536):
            checksum.update(chunk);size+=len(chunk)
            if size > limits.maximum_bytes: break
    failure=None; mime='application/octet-stream'
    if size != upload.byte_size or checksum.hexdigest()!=upload.sha256: failure='ORIGINAL_INTEGRITY_FAILURE'
    else:
        try: mime=sniff(first)
        except DocumentFailure as exc: failure=exc.code
        if not failure and mime!=upload.declared_mime: failure='MIME_MISMATCH'
    session.add(DocumentVersion(**identity.scope(),id=doc.id,version=1,upload_id=upload.id,
        storage_key=upload.storage_key,sha256=upload.sha256,byte_size=upload.byte_size,detected_mime=mime,
        actor_id=identity.actor_id,correlation_id=correlation));session.flush()
    upload.state='QUARANTINED' if failure else 'FINALIZED';doc.state='QUARANTINED' if failure else 'QUEUED';doc.last_error=failure
    if not failure: enqueue_stage(session,identity,doc,'PREPROCESS',identity.actor_id,correlation)
    audit(session,identity,'DOCUMENT_QUARANTINED' if failure else 'UPLOAD_FINALIZED',doc.id,1,
        'Original content checked; preprocessing scheduled' if not failure else 'Original cannot proceed safely',correlation,{'code':failure,'mime':mime})
    return detail(session,identity,doc.id)


def pages(session, identity, document_id):
    return session.scalars(scope_query(select(DocumentPage),DocumentPage,identity).where(DocumentPage.document_id==document_id,DocumentPage.document_version==1).order_by(DocumentPage.page)).all()


def intake_hint(session,identity,doc):
    from app.db.models import AuditEvent
    event=session.scalar(scope_query(select(AuditEvent),AuditEvent,identity).where(AuditEvent.object_id==doc.id,
        AuditEvent.action=='UPLOAD_SESSION_CREATED').order_by(AuditEvent.sequence).limit(1))
    return event.payload.get('intake_hint',doc.source_type) if event else doc.source_type


def confirm_purpose(session,identity,document_id,data,correlation):
    from app.services.finance import scope_lock
    scope_lock(session,identity)
    doc=get(session,Document,identity,document_id)
    if doc.generation!=data['expected_generation']:raise DomainError(409,'DOCUMENT_CHANGED','Refresh the current document before choosing its type.')
    if intake_hint(session,identity,doc)!='AUTO' or doc.source_type!='SUPPORTING_DOCUMENT' or doc.last_error!='DOCUMENT_TYPE_UNCONFIRMED':
        raise DomainError(409,'PURPOSE_ALREADY_SET','This source has already been classified; preserve its extraction and use the source correction workflow.')
    doc.source_type=data['source_type'];doc.generation+=1;doc.state='QUEUED';doc.last_error=None
    enqueue_stage(session,identity,doc,'EXTRACT',identity.actor_id,correlation)
    audit(session,identity,'DOCUMENT_PURPOSE_CONFIRMED',doc.id,1,data['reason'],correlation,{'source_type':doc.source_type,'generation':doc.generation})
    return detail(session,identity,doc.id)


def detail(session, identity, document_id):
    doc=get(session,Document,identity,document_id)
    version=session.scalar(scope_query(select(DocumentVersion),DocumentVersion,identity).where(DocumentVersion.id==doc.id,DocumentVersion.version==1))
    jobs=session.scalars(scope_query(select(DocumentJob),DocumentJob,identity).where(DocumentJob.document_id==doc.id).order_by(DocumentJob.created_at)).all()
    runs=session.scalars(scope_query(select(ExtractionRun),ExtractionRun,identity).where(ExtractionRun.document_id==doc.id).order_by(ExtractionRun.created_at)).all()
    observations=[]
    if runs:
        observations=[projection({'id':r.id,'field_path':r.field_path,'state':r.state,'raw_value':r.raw_value,
            'parsed_candidate':r.parsed_candidate,'source':r.source,'diagnostic':r.diagnostic})
            for r in session.scalars(scope_query(select(Observation),Observation,identity).where(Observation.extraction_run_id==runs[-1].id).order_by(Observation.field_path))]
    draft=session.scalar(scope_query(select(DocumentDraft),DocumentDraft,identity).where(DocumentDraft.document_id==doc.id).order_by(DocumentDraft.created_at.desc()).limit(1))
    return projection({'id':doc.id,'display_name':doc.display_name,'source_type':doc.source_type,'state':doc.state,'generation':doc.generation,'intake_hint':intake_hint(session,identity,doc),
        'last_error':doc.last_error,'last_successful_stage':doc.last_successful_stage,'segmentation_state':doc.segmentation_state,
        'finance_decision':None,'original':None if not version else {'version':version.version,'sha256':version.sha256,
            'byte_size':version.byte_size,'detected_mime':version.detected_mime,'actor_id':version.actor_id,'correlation_id':version.correlation_id,'created_at':version.created_at,'storage_version':version.storage_version},
        'jobs':[{'id':j.id,'stage':j.stage,'state':j.state,'attempts':j.attempts,'last_error':j.last_error,'metadata':j.result_metadata} for j in jobs],
        'pages':[{'page':p.page,'page_sha256':p.page_sha256,'route':p.route,'transform':p.transform,'quality':p.quality,
            'preview_url':f'/api/v1/documents/{doc.id}/pages/{p.page}/preview'} for p in pages(session,identity,doc.id)],
        'extraction_runs':[{'id':r.id,'status':r.status,'adapter':r.adapter,'metadata':r.metadata_json,'started_at':r.started_at,'completed_at':r.completed_at} for r in runs],
        'observations':observations,'draft':None if not draft else {'id':draft.id,'stage':draft.stage,'normalizer_version':draft.normalizer_version,
            'candidate':draft.candidate,'traces':draft.traces,'findings':draft.findings},'manual_source_verification_required':True})
