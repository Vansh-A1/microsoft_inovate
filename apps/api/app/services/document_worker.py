"""Durable bounded document stages with leases, immutable outputs and outbox."""
from dataclasses import replace
from datetime import timedelta
import base64
import hashlib
import time
from uuid import uuid4
from sqlalchemy import select, or_, and_
from app.core.identity import Identity
from app.core.serialization import utcnow, projection
from app.db.document_models import *
from app.db.session import scope_query
from app.services.finance import get, audit, scope_lock
from app.services.documents import enqueue_stage, pages, STAGES, PIPELINE_VERSION
from app.documents.processor import DocumentProcessor, DocumentFailure, PROCESSOR_VERSION
from app.documents.malware import UnconfiguredMalwareAdapter
from app.documents.normalizer import Normalizer, NORMALIZER_VERSION, validate_draft
from app.domain.extraction import DocumentBundle, DocumentPage as BundlePage, DocumentSourceType, SCHEMA_VERSION, to_data
from app.extraction.native import NativeTextExtractionAdapter, reconcile
from app.extraction.ocr import TesseractOCRAdapter, UnconfiguredOCRAdapter
from app.extraction.typellm import TypeLLMExtractionAdapter


def claim(database,identity):
    now=utcnow()
    with database.session(identity) as s:
        scope_lock(s,identity)
        q=scope_query(select(DocumentJob),DocumentJob,identity).where(DocumentJob.stage_version==PIPELINE_VERSION,
            or_(and_(DocumentJob.state.in_(['QUEUED','RETRYABLE']),DocumentJob.available_at<=now),
                and_(DocumentJob.state=='RUNNING',DocumentJob.lease_until<=now))).order_by(DocumentJob.created_at).with_for_update(skip_locked=True).limit(1)
        job=s.scalar(q)
        if not job:return None
        doc=get(s,Document,identity,job.document_id)
        if job.generation!=doc.generation:
            job.state='STALE';job.lease_until=None;return (None,None,None)
        if job.attempts>=job.maximum_attempts:
            job.state='FAILED';job.last_error='ATTEMPTS_EXHAUSTED';doc.state='FAILED_FINAL';doc.last_error=job.last_error
            audit(s,identity,'DOCUMENT_JOB_FAILED',doc.id,1,'Document stage attempts exhausted',job.correlation_id)
            return (None,None,None)
        job.state='RUNNING';job.attempts+=1;job.lease_owner=uuid4();job.lease_until=now+timedelta(seconds=180);job.updated_at=now
        doc.state='PROCESSING'
        for event in s.scalars(scope_query(select(DocumentOutbox),DocumentOutbox,identity).where(DocumentOutbox.job_id==job.id,DocumentOutbox.delivered_at.is_(None))):event.delivered_at=now
        audit(s,identity,'DOCUMENT_STAGE_CLAIMED',doc.id,1,'Durable document stage lease acquired',job.correlation_id,{'stage':job.stage,'attempt':job.attempts})
        return job.id,job.lease_owner,job.actor_id


def bundle_for(doc,identity,page_data):
    return DocumentBundle(doc['id'],1,identity.tenant_id,identity.legal_entity_id,
        DocumentSourceType.EMPLOYEE_RECEIPT if doc['source_type']=='EMPLOYEE_RECEIPT' else DocumentSourceType.VENDOR_INVOICE,
        tuple(BundlePage(p['page'],p['native_text'] or None,artifact_ref=p['preview_key']) for p in page_data),synthetic=False)


def extract(doc,identity,page_data,storage,providers):
    bundle=bundle_for(doc,identity,page_data);adapter=NativeTextExtractionAdapter(page_data)
    native=adapter.extract(bundle,SCHEMA_VERSION);diagnostics=list(adapter.diagnostics)
    routing={'version':'extraction-routing-v1','paths':[],'ocr_status':'NOT_CONFIGURED','vlm_status':'NOT_CONFIGURED',
        'segmentation':'UNCERTAIN' if 'SEGMENTATION_UNCERTAIN' in diagnostics else 'UNCONFIRMED',
        'fallback':'HUMAN_REVIEW','model_quality':'NOT_MEASURED'}
    visual=[p for p in page_data if p['route']!='NATIVE_TEXT_AVAILABLE']
    if not visual:
        if providers.endpoint:routing['vlm_status']='CONFIGURED_NOT_NEEDED'
        routing['paths']=['NATIVE_TEXT'];return native,diagnostics,routing
    ocr=UnconfiguredOCRAdapter()
    if providers.ocr_executable:
        ocr=TesseractOCRAdapter(providers.ocr_executable,providers.ocr_data_directory or '',providers.ocr_library_directory)
        routing['ocr_status']='CONFIGURED'
    ocr_pages=[];deadline=time.monotonic()+30
    if providers.ocr_executable:
        for p in page_data:
            if p not in visual:ocr_pages.append(p);continue
            if time.monotonic()>=deadline:raise DocumentFailure('OCR_DOCUMENT_TIME_LIMIT')
            ocr.timeout_seconds=max(1,min(15,int(deadline-time.monotonic())))
            recognized=ocr.recognize(storage.path(identity,p['preview_key']),p['transform'])
            ocr_pages.append(p|{'native_text':recognized.text,'spans':list(recognized.spans)})
        ocr_adapter=NativeTextExtractionAdapter(ocr_pages)
        observed=ocr_adapter.extract(bundle_for(doc,identity,ocr_pages),SCHEMA_VERSION)
        observed=replace(observed,metadata=replace(observed.metadata,provider_id='LOCAL_OCR',adapter_id='ocr-label-parser',model_id='tesseract-'+ocr.version))
        native=reconcile(native,observed);native=replace(native,metadata=observed.metadata)
        diagnostics.extend(ocr_adapter.diagnostics);routing['paths'].append('LOCAL_OCR')
        routing['ocr_status']='SUCCEEDED'
    unresolved=[f for f in native.header_fields if f.field_path in ('total_amount','currency','invoice_number' if doc['source_type']=='VENDOR_INVOICE' else 'receipt_number') and f.state.value!='PRESENT']
    if providers.endpoint and (unresolved or not providers.ocr_executable):
        routing['vlm_status']='CONFIGURED'
        enterprise=TypeLLMExtractionAdapter(providers,image_loader=lambda p:'data:image/png;base64,'+base64.b64encode(storage.get(identity,p.artifact_ref)).decode())
        extracted=enterprise.extract(bundle,SCHEMA_VERSION)
        native=reconcile(native,extracted);native=replace(native,metadata=extracted.metadata)
        routing['paths'].append('ENTERPRISE_VLM');routing['vlm_status']='SUCCEEDED'
        routing['enterprise']=enterprise.sidecar
        if enterprise.sidecar['table_coverage']=='UNCERTAIN':diagnostics.append('TABLE_COVERAGE_UNCERTAIN')
    elif providers.endpoint:routing['vlm_status']='CONFIGURED_NOT_NEEDED'
    if not providers.ocr_executable and not providers.endpoint:raise DocumentFailure('VISUAL_PROVIDER_NOT_CONFIGURED')
    return native,diagnostics,routing


def load_work(database,identity,job_id):
    with database.session(identity) as s:
        job=get(s,DocumentJob,identity,job_id);doc=get(s,Document,identity,job.document_id)
        original=s.scalar(scope_query(select(DocumentVersion),DocumentVersion,identity).where(DocumentVersion.id==doc.id,DocumentVersion.version==1))
        page_data=[{'page':p.page,'native_text':p.native_text,'spans':p.spans,'preview_key':p.preview_key,'transform':p.transform,'route':p.route} for p in pages(s,identity,doc.id)]
        run=s.scalar(scope_query(select(ExtractionRun),ExtractionRun,identity).where(ExtractionRun.document_id==doc.id,ExtractionRun.status.in_(['COMPLETED','PARTIAL'])).order_by(ExtractionRun.created_at.desc()).limit(1))
        observations=[] if run is None else [projection({'id':o.id,'field_path':o.field_path,'state':o.state,'raw_value':o.raw_value,'source':o.source}) for o in s.scalars(scope_query(select(Observation),Observation,identity).where(Observation.extraction_run_id==run.id))]
        draft=s.scalar(scope_query(select(DocumentDraft),DocumentDraft,identity).where(DocumentDraft.document_id==doc.id).order_by(DocumentDraft.created_at.desc()).limit(1))
        return {'stage':job.stage,'attempt':job.attempts,'id':doc.id,'source_type':doc.source_type,'original_key':original.storage_key,
            'original_sha':original.sha256,'pages':page_data,'run_id':run.id if run else None,'observations':observations,
            'diagnostics':run.metadata_json.get('diagnostics',[]) if run else [],
            'draft':None if draft is None else {'candidate':draft.candidate,'traces':draft.traces,'findings':draft.findings}}


def perform(work,identity,storage,settings,scanner):
    if work['stage']=='PREPROCESS':
        content=storage.get(identity,work['original_key'])
        if hashlib.sha256(content).hexdigest()!=work['original_sha']:raise DocumentFailure('ORIGINAL_INTEGRITY_FAILURE')
        scan=scanner.scan(storage.path(identity,work['original_key']))
        if scan.status=='INFECTED':raise DocumentFailure('MALWARE_DETECTED')
        if scan.status=='ERROR':raise DocumentFailure('MALWARE_SCAN_UNAVAILABLE',retryable=True)
        if scan.status=='NOT_CONFIGURED' and settings.document_limits.malware_required:raise DocumentFailure('MALWARE_NOT_CONFIGURED')
        data=DocumentProcessor(settings.document_limits).process(storage.path(identity,work['original_key']))
        data['scan']={'status':scan.status,'adapter':scan.adapter,'version':scan.version}
        for p in data['pages']:
            image=base64.b64decode(p.pop('preview_base64'));p['preview_key'],sha=storage.put(identity,image,maximum=settings.document_limits.maximum_derived_bytes)
            if sha!=p['page_sha256']:raise DocumentFailure('DERIVED_INTEGRITY_FAILURE')
        return data
    if work['stage']=='EXTRACT':
        observed,diagnostics,routing=extract(work,identity,work['pages'],storage,settings.document_providers)
        return {'result':to_data(observed),'diagnostics':diagnostics,'routing':routing}
    if work['stage']=='NORMALIZE':
        candidate,traces,findings=Normalizer().normalize(work['observations'])
        return {'candidate':candidate,'traces':traces,'findings':findings}
    if work['stage']=='VALIDATE':
        draft=work['draft'];findings=draft['findings']+validate_draft(draft['candidate'],draft['traces'],work['source_type'],work['diagnostics'])
        return draft|{'findings':findings}
    return {'state':'NEEDS_INPUT' if work['draft']['findings'] else 'READY'}


def persist(database,identity,job_id,owner,work,output,started):
    with database.session(identity) as s:
        scope_lock(s,identity)
        job=s.scalar(scope_query(select(DocumentJob),DocumentJob,identity).where(DocumentJob.id==job_id).with_for_update());doc=get(s,Document,identity,job.document_id)
        if job.state!='RUNNING' or job.lease_owner!=owner or job.lease_until<=utcnow() or job.generation!=doc.generation:return
        if job.stage=='PREPROCESS':
            for p in output['pages']:
                s.add(DocumentPage(**identity.scope(),document_id=doc.id,document_version=1,processor_version=PROCESSOR_VERSION,**p))
            job.result_metadata={'scan':output['scan'],'processor_version':PROCESSOR_VERSION,'page_count':len(output['pages'])}
        elif job.stage=='EXTRACT':
            r=output['result'];run=ExtractionRun(**identity.scope(),id=__import__('uuid').UUID(r['run_id']),document_id=doc.id,document_version=1,
                job_id=job.id,attempt=job.attempts,status=r['status'],adapter=r['metadata']['adapter_id'],
                metadata_json=r['metadata']|{'routing':output['routing'],'diagnostics':output['diagnostics'],'schema_version':r['schema_version']},
                result=r,started_at=started,completed_at=utcnow())
            s.add(run);s.flush()
            items=[(o['field_path'],o) for o in r['header_fields']]+[(f'lines.{row["row_index"]-1}.{o["field_path"]}',o) for row in r['line_items'] for o in row['fields']]
            for field,o in items:s.add(Observation(**identity.scope(),extraction_run_id=run.id,field_path=field,state=o['state'],
                raw_value=o['raw_value'],parsed_candidate=o['parsed_candidate'],source=o['source'],diagnostic=o['diagnostic_note']))
            if 'SEGMENTATION_UNCERTAIN' in output['diagnostics']:doc.segmentation_state='UNCERTAIN'
            job.result_metadata=output['routing']
        elif job.stage in ('NORMALIZE','VALIDATE'):
            s.add(DocumentDraft(**identity.scope(),document_id=doc.id,document_version=1,extraction_run_id=work['run_id'],
                normalizer_version=NORMALIZER_VERSION,stage=job.stage,**output))
        elif job.stage=='FINALIZE':doc.state=output['state']
        job.state='SUCCEEDED';job.lease_until=None;job.updated_at=utcnow();doc.last_successful_stage=job.stage;doc.last_error=None
        s.flush()
        if job.stage!='FINALIZE':enqueue_stage(s,identity,doc,STAGES[STAGES.index(job.stage)+1],job.actor_id,job.correlation_id);doc.state='QUEUED'
        audit(s,identity,'DOCUMENT_STAGE_COMPLETED',doc.id,1,'Document stage output committed once',job.correlation_id,{'stage':job.stage})


def record_failure(database,identity,job_id,owner,work,exc,started):
    with database.session(identity) as s:
        scope_lock(s,identity)
        job=s.scalar(scope_query(select(DocumentJob),DocumentJob,identity).where(DocumentJob.id==job_id).with_for_update());doc=get(s,Document,identity,job.document_id)
        if job.state!='RUNNING' or job.lease_owner!=owner or job.generation!=doc.generation:return
        retry=exc.retryable and job.attempts<job.maximum_attempts
        job.state='RETRYABLE' if retry else 'FAILED';job.last_error=exc.code;job.lease_until=None;job.updated_at=utcnow();job.available_at=utcnow()+timedelta(seconds=2**job.attempts)
        quarantined=job.stage=='PREPROCESS' and exc.code not in ('MALWARE_NOT_CONFIGURED','MALWARE_SCAN_UNAVAILABLE','PARSER_TIMEOUT','PARSER_RESOURCE_FAILURE')
        unavailable='NOT_CONFIGURED' in exc.code or exc.code in ('TOKENIZER_NOT_PROVISIONED','TYPELLM_CLIENT_NOT_INSTALLED','TYPELLM_CLIENT_VERSION_UNSUPPORTED')
        doc.state='FAILED_RETRYABLE' if retry else ('QUARANTINED' if quarantined else ('DEPENDENCY_UNAVAILABLE' if unavailable else 'NEEDS_INPUT'))
        doc.last_error=exc.code
        if job.stage=='EXTRACT':s.add(ExtractionRun(**identity.scope(),document_id=doc.id,document_version=1,job_id=job.id,attempt=job.attempts,
            status='FAILED',adapter='document-router',metadata_json={'schema_version':SCHEMA_VERSION,'failure_code':exc.code},result={},started_at=started,completed_at=utcnow()))
        audit(s,identity,'DOCUMENT_RETRY_SCHEDULED' if retry else 'DOCUMENT_STAGE_FAILED',doc.id,1,'Safe document stage failure recorded',job.correlation_id,{'stage':job.stage,'code':exc.code})


def run_once(database,identity,storage,settings,scanner=None):
    leased=claim(database,identity)
    if not leased:return False
    job_id,owner,actor=leased
    if job_id is None:return True
    execution=Identity(identity.tenant_id,identity.legal_entity_id,actor,identity.roles,identity.label)
    started=utcnow();work=load_work(database,execution,job_id)
    try:
        output=perform(work,execution,storage,settings,scanner or UnconfiguredMalwareAdapter())
        persist(database,execution,job_id,owner,work,output,started)
    except DocumentFailure as exc:record_failure(database,execution,job_id,owner,work,exc,started)
    except Exception:record_failure(database,execution,job_id,owner,work,DocumentFailure('DOCUMENT_EXECUTION_FAILED',retryable=True),started)
    return True
