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
from app.documents.malware import UnconfiguredMalwareAdapter,configured_scanner
from app.documents.normalizer import Normalizer, NORMALIZER_VERSION, validate_draft
from app.domain.extraction import DocumentBundle, DocumentPage as BundlePage, DocumentSourceType, SCHEMA_VERSION, to_data
from app.extraction.native import NativeTextExtractionAdapter, reconcile
from app.extraction.ocr import TesseractOCRAdapter, UnconfiguredOCRAdapter
from app.extraction.typellm import TypeLLMExtractionAdapter


def ocr_configured(providers):
    return bool(providers.ocr_executable or providers.ocr_backend=='RAPIDOCR_CPU_EXPERIMENTAL')


def configured_ocr(providers,storage):
    fallback=None
    if providers.ocr_executable:
        try:fallback=TesseractOCRAdapter(providers.ocr_executable,providers.ocr_data_directory or '',providers.ocr_library_directory)
        except DocumentFailure:
            if providers.ocr_backend!='RAPIDOCR_CPU_EXPERIMENTAL':raise
    if providers.ocr_backend=='RAPIDOCR_CPU_EXPERIMENTAL':
        from app.extraction.cpu_ocr import resident,FallbackOCR
        try:return FallbackOCR(resident(providers.ocr_python,storage.root),fallback)
        except DocumentFailure as error:
            if fallback:
                fallback.metadata={'candidate_failure':error.code,'fallback':'TESSERACT'}
                return fallback
            raise
    return fallback or UnconfiguredOCRAdapter()


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
            from app.services.operations import mark_failure
            mark_failure(job,'ATTEMPTS_EXHAUSTED',True,now);doc.state='FAILED_FINAL';doc.last_error=job.last_error
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


def mapping_gaps(observed,source_type,diagnostics=()):
    """Coverage is an extraction-routing gate, never a finance decision."""
    required=('vendor_name','invoice_number','invoice_date','currency','subtotal_amount','tax_amount','total_amount',
        'document_discount_amount','shipping_amount','other_charges_amount','tax_basis') if source_type=='VENDOR_INVOICE' else (
        'merchant_name','receipt_number','expense_date','currency','total_amount','category','local_timezone','receipt_type')
    by={f.field_path:f for f in observed.header_fields}
    gaps=[name for name in required if name not in by or by[name].state.value!='PRESENT']
    if source_type=='VENDOR_INVOICE':
        if not observed.line_items:gaps.append('LINE_ITEMS_NOT_MAPPED')
        elif any(f.state.value!='PRESENT' for row in observed.line_items for f in row.fields):gaps.append('LINE_ITEMS_INCOMPLETE')
    if diagnostics:gaps.extend(diagnostics)
    return list(dict.fromkeys(gaps))


def printed_table_complete(observed,diagnostics=()):
    if diagnostics or not observed.line_items:return False
    for row in observed.line_items:
        fields={f.field_path:f for f in row.fields if f.state.value=='PRESENT'}
        if not {'description','quantity','unit_price'}<=fields.keys() or not {'amount','net_amount','gross_amount'}&fields.keys():return False
    return True


def source_table_reviewable(observed,diagnostics=()):
    """Distinct measured rows with one unread core cell require human input.

    OCR absence is not proof of a blank cell. Do not ask a model to fill it from
    prices/totals, or discard following measured rows. Competing/crossing geometry
    and provider disagreements never satisfy this gate.
    """
    if not observed.line_items or set(diagnostics)-{'TABLE_CELL_UNREAD'}:return False
    for row in observed.line_items:
        fields={f.field_path:f for f in row.fields}
        amount=next((f for f in ('amount','net_amount','gross_amount') if f in fields),None)
        if amount is None:return False
        core=[fields.get(f) for f in ('description','quantity','unit_price',amount)]
        if core[0] is None or core[0].state.value!='PRESENT':return False
        if sum(f is not None and f.state.value=='PRESENT' for f in core)<3:return False
        if any(f is None or f.state.value not in ('PRESENT','MISSING') for f in core):return False
        if any(f.state.value=='PRESENT' and (f.source is None or f.bbox is None) for f in core):return False
    return True


def source_mapping_reviewable(observed,source_type,diagnostics=()):
    if source_type!='VENDOR_INVOICE':return False
    headers={f.field_path:f for f in observed.header_fields}
    core=('vendor_name','invoice_number','invoice_date','currency','subtotal_amount','tax_amount','total_amount')
    return all(f in headers and headers[f].state.value=='PRESENT' for f in core) and source_table_reviewable(observed,diagnostics)


def printed_mapping_complete(observed,source_type,diagnostics=()):
    """Sufficient *printed* coverage to stop inference, never financial clearance.

    Missing tax treatment/charges/UOM stay missing and require source confirmation.
    A VLM is not asked to fabricate fields that have no printed label/column.
    """
    if diagnostics:return False
    required=('vendor_name','invoice_number','invoice_date','currency','subtotal_amount','tax_amount','total_amount') if source_type=='VENDOR_INVOICE' else (
        'merchant_name','expense_date','currency','total_amount')
    by={f.field_path:f for f in observed.header_fields}
    if any(name not in by or by[name].state.value!='PRESENT' for name in required):return False
    if source_type!='VENDOR_INVOICE':return True
    return printed_table_complete(observed,diagnostics)


def extract(doc,identity,page_data,storage,providers):
    bundle=bundle_for(doc,identity,page_data);adapter=NativeTextExtractionAdapter(page_data)
    native=adapter.extract(bundle,SCHEMA_VERSION);diagnostics=list(adapter.diagnostics)
    from app.extraction.row_grounding import source_rows
    routing={'version':'extraction-routing-v2','paths':['NATIVE_TEXT'] if any(p['native_text'] for p in page_data) else [],'ocr_status':'NOT_CONFIGURED','vlm_status':'NOT_CONFIGURED',
        'segmentation':'UNCERTAIN' if 'SEGMENTATION_UNCERTAIN' in diagnostics else 'UNCONFIRMED',
        'fallback':'HUMAN_REVIEW','model_quality':'NOT_MEASURED'}
    visual=[p for p in page_data if p['route']!='NATIVE_TEXT_AVAILABLE']
    gaps=mapping_gaps(native,doc['source_type'],diagnostics)
    routing['cheap_mapping_gaps']=gaps
    if 'SEGMENTATION_UNCERTAIN' in diagnostics:
        # A model cannot choose which of two printed invoice identities owns a
        # bundle. Preserve both and request confirmed segmentation.
        routing['vlm_status']='CONFIGURED_NOT_NEEDED' if providers.endpoint else 'NOT_CONFIGURED'
        routing['sufficiency']='HUMAN_SEGMENTATION_REQUIRED'
        return native,diagnostics,routing
    if not visual and (not gaps or printed_mapping_complete(native,doc['source_type'],diagnostics) or source_mapping_reviewable(native,doc['source_type'],diagnostics)):
        if providers.endpoint:routing['vlm_status']='CONFIGURED_NOT_NEEDED'
        if gaps:routing['sufficiency']='SOURCE_CELL_CONFIRMATION_REQUIRED' if 'TABLE_CELL_UNREAD' in diagnostics else 'PRINTED_FACTS_MAPPED_REVIEW_REQUIRED'
        routing['source_rows']=source_rows(native)
        routing['paths']=['NATIVE_TEXT'];return native,diagnostics,routing
    ocr=UnconfiguredOCRAdapter()
    if ocr_configured(providers):
        ocr=configured_ocr(providers,storage)
        routing['ocr_status']='CONFIGURED'
    ocr_pages=page_data;deadline=time.monotonic()+30
    if ocr_configured(providers) and visual:
        ocr_pages=[]
        routing['ocr_provenance']=[]
        for p in page_data:
            if p not in visual:ocr_pages.append(p);continue
            if time.monotonic()>=deadline:raise DocumentFailure('OCR_DOCUMENT_TIME_LIMIT')
            ocr.timeout_seconds=max(1,min(15,int(deadline-time.monotonic())))
            recognized=ocr.recognize(storage.path(identity,p['preview_key']),p['transform'])
            routing['ocr_provenance'].append({'page':p['page'],'provider':recognized.provider,'version':recognized.version,
                'runtime':getattr(ocr,'metadata',{})})
            ocr_pages.append(p|{'native_text':recognized.text,'spans':list(recognized.spans)})
        ocr_adapter=NativeTextExtractionAdapter(ocr_pages)
        observed=ocr_adapter.extract(bundle_for(doc,identity,ocr_pages),SCHEMA_VERSION)
        engines='+'.join(sorted({p['provider']+'-'+p['version'] for p in routing['ocr_provenance']}))
        observed=replace(observed,metadata=replace(observed.metadata,provider_id='LOCAL_OCR',adapter_id='ocr-label-parser',model_id=engines))
        native=reconcile(native,observed);native=replace(native,metadata=observed.metadata)
        diagnostics.extend(ocr_adapter.diagnostics);routing['paths'].append('LOCAL_OCR')
        routing['ocr_status']='SUCCEEDED'
    gaps=mapping_gaps(native,doc['source_type'],diagnostics)
    routing['cheap_mapping_gaps']=gaps
    if providers.endpoint and gaps and not (printed_mapping_complete(native,doc['source_type'],diagnostics) or source_mapping_reviewable(native,doc['source_type'],diagnostics)):
        routing['vlm_status']='CONFIGURED'
        from app.extraction.grid import row_crops
        crop_cache={}
        def row_image(page,ordinal,count):
            if page.page not in crop_cache:crop_cache[page.page]=row_crops(storage.get(identity,page.artifact_ref),providers.maximum_rows)
            crops=crop_cache[page.page]
            if len(crops)!=count:return None
            content,trace=crops[ordinal-1]
            key,sha=storage.put(identity,content,maximum=4*1024*1024)
            if sha!=trace['sha256']:raise DocumentFailure('DERIVED_INTEGRITY_FAILURE')
            trace=trace|{'preview_key':page.artifact_ref,'storage_key':key,
                'page_transform':next(p['transform'] for p in page_data if p['page']==page.page)}
            return 'data:image/png;base64,'+base64.b64encode(content).decode(),trace
        mapped_headers={};printed_columns={};mapped_rows={}
        from app.extraction.layout import table_columns
        for p in ocr_pages:
            page_adapter=NativeTextExtractionAdapter([p])
            per_page=page_adapter.extract(bundle_for(doc,identity,[p]),SCHEMA_VERSION)
            mapped_headers[p['page']]=per_page.header_fields
            printed_columns[p['page']]=table_columns(p)
            if printed_table_complete(per_page,page_adapter.diagnostics) or source_table_reviewable(per_page,page_adapter.diagnostics):mapped_rows[p['page']]=per_page.line_items
        enterprise=TypeLLMExtractionAdapter(providers,
            image_loader=lambda p:'data:image/png;base64,'+base64.b64encode(storage.get(identity,p.artifact_ref)).decode(),row_image_loader=row_image,
            header_observations=mapped_headers,printed_columns=printed_columns,row_observations=mapped_rows)
        extracted=enterprise.extract(bundle_for(doc,identity,ocr_pages),SCHEMA_VERSION)
        # A model can read amounts but cannot establish accounting tax treatment
        # from their arithmetic or a sales-tax summary. Preserve the unsupported
        # candidate for review; only independently labeled text can corroborate it.
        basis=next((f for f in native.header_fields if f.field_path=='tax_basis'),None)
        if basis is None or basis.state.value!='PRESENT':
            from app.domain.extraction import ExtractionObservationState as ObservationState
            extracted=replace(extracted,header_fields=tuple(replace(f,state=ObservationState.AMBIGUOUS,
                diagnostic_note='Model-only tax treatment is unconfirmed; inspect an explicit source statement or apply an authorized policy.')
                if f.field_path=='tax_basis' and f.state.value=='PRESENT' else f for f in extracted.header_fields))
        from app.domain.extraction import ExtractionObservationState as ObservationState
        accounting=frozenset(('discount_amount','net_amount','tax_rate','tax_amount','gross_amount'))
        grounded_rows=[]
        for index,row in enumerate(extracted.line_items):
            independently_read={f.field_path:f for f in native.line_items[index].fields} if len(native.line_items)==len(extracted.line_items) else {}
            fields=tuple(replace(f,state=ObservationState.AMBIGUOUS,
                diagnostic_note='Model-only row accounting semantics are unconfirmed; inspect an explicit item column. Document totals and arithmetic do not establish row facts.')
                if f.field_path in accounting and f.state is ObservationState.PRESENT and
                    (f.field_path not in independently_read or independently_read[f.field_path].state is not ObservationState.PRESENT)
                else f for f in row.fields)
            grounded_rows.append(replace(row,fields=fields))
        extracted=replace(extracted,line_items=tuple(grounded_rows))
        enterprise.sidecar['accounting_grounding_version']='independent-item-column-v1'
        if native.line_items and extracted.line_items and len(native.line_items)!=len(extracted.line_items):
            from app.domain.extraction import to_data
            routing['row_count_disagreement']={'version':'provider-candidates-v1',
                'primary':to_data(native),'visual':to_data(extracted)}
        native=reconcile(native,extracted)
        if enterprise.sidecar.get('calls',0):
            native=replace(native,metadata=extracted.metadata)
            routing['paths'].append('ENTERPRISE_VLM');routing['vlm_status']='SUCCEEDED'
        else:
            # Per-page complete observations may leave only a document-level
            # conflict. Reuse does not constitute a model invocation/provenance.
            routing['vlm_status']='CONFIGURED_NOT_NEEDED'
        routing['enterprise']=enterprise.sidecar
        if enterprise.sidecar['table_coverage']=='UNCERTAIN':diagnostics.append('TABLE_COVERAGE_UNCERTAIN')
    elif providers.endpoint:
        routing['vlm_status']='CONFIGURED_NOT_NEEDED'
        if gaps:routing['sufficiency']='SOURCE_CELL_CONFIRMATION_REQUIRED' if 'TABLE_CELL_UNREAD' in diagnostics else 'PRINTED_FACTS_MAPPED_REVIEW_REQUIRED'
    if visual and not ocr_configured(providers) and not providers.endpoint:raise DocumentFailure('VISUAL_PROVIDER_NOT_CONFIGURED')
    routing['source_rows']=source_rows(native)
    return native,diagnostics,routing


def load_work(database,identity,job_id):
    with database.session(identity) as s:
        job=get(s,DocumentJob,identity,job_id);doc=get(s,Document,identity,job.document_id)
        original=s.scalar(scope_query(select(DocumentVersion),DocumentVersion,identity).where(DocumentVersion.id==doc.id,DocumentVersion.version==1))
        page_data=[{'page':p.page,'native_text':p.native_text,'spans':p.spans,'preview_key':p.preview_key,'transform':p.transform,'route':p.route} for p in pages(s,identity,doc.id)]
        run=s.scalar(scope_query(select(ExtractionRun),ExtractionRun,identity).where(ExtractionRun.document_id==doc.id,ExtractionRun.status.in_(['COMPLETED','PARTIAL'])).order_by(ExtractionRun.created_at.desc()).limit(1))
        observations=[] if run is None else [projection({'id':o.id,'field_path':o.field_path,'state':o.state,'raw_value':o.raw_value,'source':o.source,'diagnostic':o.diagnostic}) for o in s.scalars(scope_query(select(Observation),Observation,identity).where(Observation.extraction_run_id==run.id))]
        draft=s.scalar(scope_query(select(DocumentDraft),DocumentDraft,identity).where(DocumentDraft.document_id==doc.id).order_by(DocumentDraft.created_at.desc()).limit(1))
        from app.services.documents import intake_hint
        return {'stage':job.stage,'attempt':job.attempts,'id':doc.id,'source_type':doc.source_type,'intake_hint':intake_hint(s,identity,doc),'original_key':original.storage_key,
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
        if work.get('intake_hint')=='AUTO':
            from app.documents.classification import classify
            classification_pages=[]
            deadline=time.monotonic()+30
            providers=settings.document_providers
            for p in data['pages']:
                candidate=p
                if not p['native_text'].strip() and ocr_configured(providers):
                    remaining=int(deadline-time.monotonic())
                    if remaining<=0:raise DocumentFailure('OCR_DOCUMENT_TIME_LIMIT')
                    ocr=configured_ocr(providers,storage);ocr.timeout_seconds=min(15,remaining)
                    text=ocr.recognize(storage.path(identity,p['preview_key']),p['transform'])
                    candidate=p|{'native_text':text.text,'spans':text.spans}
                classification_pages.append(candidate)
            data['classification']=classify(bundle_for(work,identity,classification_pages),classification_pages)
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
            if 'classification' in output:
                job.result_metadata['classification']=output['classification']
                if output['classification']['source_type']:
                    doc.source_type=output['classification']['source_type']
                    audit(s,identity,'DOCUMENT_PURPOSE_SUGGESTED',doc.id,1,'Printed document labels suggest a purpose; source verification still required',job.correlation_id,output['classification'])
                else:
                    job.state='SUCCEEDED';job.lease_until=None;job.updated_at=utcnow();doc.last_successful_stage='PREPROCESS'
                    doc.state='NEEDS_INPUT';doc.last_error='DOCUMENT_TYPE_UNCONFIRMED'
                    audit(s,identity,'DOCUMENT_PURPOSE_REQUIRED',doc.id,1,'Confirm document type before extraction',job.correlation_id,output['classification'])
                    return
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
        from app.services.operations import mark_failure
        mark_failure(job,exc.code,exc.retryable,utcnow())
        quarantined=not exc.retryable and job.stage=='PREPROCESS' and exc.code not in ('MALWARE_NOT_CONFIGURED','MALWARE_SCAN_UNAVAILABLE','PARSER_TIMEOUT','PARSER_RESOURCE_FAILURE')
        unavailable='NOT_CONFIGURED' in exc.code or exc.code in ('TOKENIZER_NOT_PROVISIONED','TYPELLM_CLIENT_NOT_INSTALLED','TYPELLM_CLIENT_VERSION_UNSUPPORTED')
        doc.state='FAILED_RETRYABLE' if retry else ('FAILED_FINAL' if exc.retryable else ('QUARANTINED' if quarantined else ('DEPENDENCY_UNAVAILABLE' if unavailable else 'NEEDS_INPUT')))
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
        output=perform(work,execution,storage,settings,scanner or configured_scanner())
        persist(database,execution,job_id,owner,work,output,started)
    except DocumentFailure as exc:record_failure(database,execution,job_id,owner,work,exc,started)
    except Exception as exc:
        from app.services.operations import classify_failure
        code,retryable=classify_failure(exc)
        record_failure(database,execution,job_id,owner,work,DocumentFailure(code,retryable=retryable),started)
    return True
