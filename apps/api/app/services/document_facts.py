"""Append source-verified canonical revisions; finance rules remain authoritative."""
from copy import deepcopy
from decimal import Decimal, localcontext
from uuid import UUID, uuid4
from sqlalchemy import select
from app.core.errors import DomainError
from app.core.serialization import projection
from app.db.document_models import Document, DocumentDraft, DocumentPage, TransactionDocument, SourceCorrection
from app.db.models import ReferenceRecord, Transaction, TransactionVersion
from app.db.session import scope_query
from app.documents.normalizer import Normalizer, validate_draft, NORMALIZER_VERSION
from app.extraction.native import HEADER_FIELDS, ROW_FIELDS
from app.schemas.canonical import Canonical
from app.services import finance, documents


def links(session,identity,transaction_id,version):
    return session.scalars(scope_query(select(TransactionDocument),TransactionDocument,identity).where(
        TransactionDocument.transaction_id==transaction_id,TransactionDocument.transaction_version==version)).all()


def copy_links(session,identity,transaction_id,previous,current,exclude=None):
    for link in links(session,identity,transaction_id,previous):
        if link.document_id==exclude:continue
        session.add(TransactionDocument(**identity.scope(),transaction_id=transaction_id,transaction_version=current,
            document_id=link.document_id,document_version=link.document_version,role=link.role,first_page=link.first_page,
            last_page=link.last_page,verification_id=link.verification_id,verification_version=link.verification_version,draft_id=link.draft_id))
    session.flush()


def source_context(session,identity,version,references):
    current=links(session,identity,version.transaction_id,version.version)
    references={k:v for k,v in references.items() if v.get('verification')!='HUMAN_VERIFIED_DOCUMENT'}
    documents_seen=[]
    for link in current:
        if link.verification_id:
            record=session.scalar(scope_query(select(ReferenceRecord),ReferenceRecord,identity).where(ReferenceRecord.id==link.verification_id,ReferenceRecord.version==link.verification_version))
            if record:references[str(link.document_id)]=record.payload|{'_kind':record.kind}
        documents_seen.append({'document_id':str(link.document_id),'document_version':link.document_version,
            'role':link.role,'first_page':link.first_page,'last_page':link.last_page,'draft_id':str(link.draft_id) if link.draft_id else None,
            'verification_id':str(link.verification_id) if link.verification_id else None})
    source_links=[l for l in current if l.role in ('INVOICE','RECEIPT')]
    valid=None
    if source_links:
        ids={str(l.document_id) for l in source_links};p=version.payload
        actual={str(p.get('source_document_id'))} if p['branch']=='VENDOR_INVOICE' else {str(i.get('source_document_id')) for i in p['items']}
        valid=actual<=ids and all(l.verification_id is not None for l in source_links)
        if p['branch']=='VENDOR_INVOICE':
            source=references.get(str(p.get('source_document_id')))
            if source and source.get('verification')=='HUMAN_VERIFIED_DOCUMENT':
                fields=tuple(k for k in ROW_FIELDS if k!='description')+('currency',)
                printed=source['facts'].get('line_items',[])
                valid=bool(valid and len(printed)==len(p['lines']) and all(
                    all(a.get(k)==b.get(k) for k in fields) for a,b in zip(printed,p['lines'])))
                po=references.get(str(p.get('po_id')))
                if source['facts'].get('po_reference'):
                    valid=bool(valid and po and source['facts']['po_reference'].casefold()==str(po.get('display_number','')).casefold())
    return references,documents_seen,valid


def corrected_draft(session,identity,document_id,body):
    doc=finance.get(session,Document,identity,document_id)
    if doc.state in ('AWAITING_UPLOAD','UPLOADED','QUEUED','PROCESSING','QUARANTINED','FAILED_FINAL','FAILED_RETRYABLE'):
        raise DomainError(409,'DOCUMENT_NOT_REVIEWABLE','Wait for safe preprocessing and extraction before verification.')
    draft=finance.get(session,DocumentDraft,identity,UUID(body['draft_id']))
    latest=session.scalar(scope_query(select(DocumentDraft),DocumentDraft,identity).where(DocumentDraft.document_id==doc.id).order_by(DocumentDraft.created_at.desc()).limit(1))
    if draft.document_id!=doc.id or latest.id!=draft.id or draft.stage!='VALIDATE':
        raise DomainError(409,'DRAFT_STALE','Review the latest validated draft.')
    page_numbers={p.page for p in documents.pages(session,identity,doc.id)}
    first=body.get('first_page',1);last=body.get('last_page') or max(page_numbers)
    if first not in page_numbers or last not in page_numbers or first>last:raise DomainError(422,'PAGE_RANGE','Select actual one-based pages.')
    if doc.segmentation_state=='UNCERTAIN':
        raise DomainError(409,'SEGMENTATION_UNCERTAIN','This bundle has conflicting document identities; upload separately confirmed documents. Automatic splitting is unavailable.')
    if not body['source_confirmed']:raise DomainError(422,'SOURCE_CONFIRMATION_REQUIRED','Confirm the source facts before canonical submission.')
    observations=[{'id':t['source_observation_id'],'field_path':t['field_path'],'state':'PRESENT' if t['status']=='NORMALIZED' else t['status'],
        'raw_value':t['raw_value'],'source':t.get('source')} for t in draft.traces]
    by={o['field_path']:o for o in observations};changes=[]
    for correction in body.get('corrections',[]):
        field=correction['field_path'];page=correction['page']
        if field not in by or page not in page_numbers or not first<=page<=last:
            raise DomainError(422,'CORRECTION_SOURCE','Correct an observed field using an actual selected source page.')
        if field not in HEADER_FIELDS and not (field.startswith('lines.') and field.split('.')[-1] in ROW_FIELDS):
            raise DomainError(422,'CORRECTION_FIELD','Unsupported observable field.')
        old=deepcopy(by[field])
        ref={'kind':'DOCUMENT_FIELD','record_id':str(doc.id),'record_version':1,'tenant_id':str(identity.tenant_id),
            'legal_entity_id':str(identity.legal_entity_id),'document_id':str(doc.id),'page':page,'bbox':None,
            'field_path':field,'observed_value':correction['value'],'snapshot_id':None,'import_cell':None}
        by[field]={'id':old['id'],'field_path':field,'state':'PRESENT','raw_value':correction['value'],'source':ref}
        changes.append({'field_path':field,'source_observation_id':old['id'],
            'old_raw_value':old['raw_value'],'old_canonical_candidate':draft.candidate.get(field),'new_raw_value':correction['value'],
            'source':ref,'actor_id':str(identity.actor_id),'reason':correction['reason']})
    candidate,traces,findings=Normalizer().normalize(list(by.values()),date_order=body.get('date_order'))
    # Existing ambiguity/arithmetic must be resolved, not dismissed by source confirmation.
    coverage_codes=tuple(f['code'] for f in draft.findings if f['code'] in ('TABLE_COVERAGE_UNCERTAIN','TABLE_ROW_LIMIT','SEGMENTATION_UNCERTAIN'))
    findings+=validate_draft(candidate,traces,doc.source_type,coverage_codes)
    for trace in traces:
        if trace.get('source') and trace['canonical_candidate'] is not None and trace['source'].get('page') not in range(first,last+1):
            findings.append({'field':trace['field_path'],'code':'SOURCE_OUTSIDE_SELECTED_SEGMENT','state':'NEEDS_INPUT'})
    if findings:raise DomainError(422,'CANONICAL_SOURCE_UNRESOLVED','Critical source facts remain unresolved.',details=findings)
    for change in changes:change['new_canonical_candidate']=candidate[change['field_path']]
    for trace in traces:
        if any(c['field_path']==trace['field_path'] for c in changes):
            trace['value_origin']='HUMAN_CORRECTED'
            trace['actor_id']=str(identity.actor_id)
    return doc,draft,candidate,traces,changes,first,last


def commit(session,identity,document_id,body,correlation):
    finance.scope_lock(session,identity)
    if body.get('transaction_id'):finance.review_guard(session,identity,finance.get(session,Transaction,identity,UUID(body['transaction_id'])),body)
    doc,draft,candidate,traces,changes,first,last=corrected_draft(session,identity,document_id,body)
    payload=deepcopy(body['transaction']);vendor=payload['branch']=='VENDOR_INVOICE'
    if vendor != (doc.source_type=='VENDOR_INVOICE'):
        raise DomainError(422,'DOCUMENT_BRANCH','Source type must match the finance branch.')
    if vendor:
        fields=('invoice_number','invoice_date','currency','subtotal_amount','tax_amount','total_amount',
            'document_discount_amount','shipping_amount','other_charges_amount','tax_basis','payment_account_token')
        payload.update({k:candidate.get(k) for k in fields});payload['source_document_id']=str(doc.id)
        indexes=sorted({int(k.split('.')[1]) for k in candidate if k.startswith('lines.')})
        if len(payload['lines'])!=len(indexes):raise DomainError(422,'LINE_MAPPING','Map each observed line to a canonical line; row count must agree.')
        for i in indexes:
            for k in ROW_FIELDS:
                if k!='description':payload['lines'][i][k]=candidate.get(f'lines.{i}.{k}')
            payload['lines'][i]['currency']=candidate['currency']
    else:
        if not payload['items']:raise DomainError(422,'RECEIPT_MAPPING','Supply an expense item for the receipt.')
        matching=[i for i in payload['items'] if i.get('source_document_id')==str(doc.id)]
        if not matching and len(payload['items'])==1:matching=payload['items'];matching[0]['source_document_id']=str(doc.id)
        if len(matching)!=1:raise DomainError(422,'RECEIPT_MAPPING','Link this receipt to exactly one expense item.')
        item=matching[0]
        item.update(currency=candidate['currency'],category=candidate['category'],expense_date=candidate['expense_date'],
            local_timezone=candidate['local_timezone'],receipt_total_amount=candidate['total_amount'])
        # Claim amount is a human request, validated by existing finance rules, never inferred reimbursable.
        payload.update(currency=candidate['currency'],category=candidate['category'],expense_date=candidate['expense_date'],local_timezone=candidate['local_timezone'])
    payload=Canonical.model_validate(payload).model_dump(mode='json')
    transaction_id=body.get('transaction_id')
    previous=None
    if transaction_id:
        transaction_id=UUID(transaction_id);previous=finance.get(session,Transaction,identity,transaction_id).latest_version
        created=finance.revise(session,identity,transaction_id,{'expected_version':body['expected_version'],'reason':body['reason'],'transaction':payload},correlation,
            normalizer_version=NORMALIZER_VERSION,copy_document_links=False)
        copy_links(session,identity,transaction_id,previous,created['version'],exclude=doc.id)
    else:
        created=finance.create_transaction(session,identity,payload,body['reason'],correlation,normalizer_version=NORMALIZER_VERSION)
        transaction_id=UUID(created['id'])
    facts={k:v for k,v in candidate.items() if not k.startswith('lines.')}
    if vendor:
        facts['line_items']=[{k:candidate.get(f'lines.{i}.{k}') for k in ROW_FIELDS if k!='description'}|{'currency':candidate['currency']} for i in indexes]
    if not vendor:facts.update(receipt_total_amount=candidate['total_amount'],readable=True)
    fields={f'facts.{t["field_path"]}':t['source'] for t in traces if t.get('source')}
    verification_id=uuid4()
    correction_id=uuid4()
    for trace in traces:
        if trace.get('value_origin')=='HUMAN_CORRECTED':trace['source_correction_id']=str(correction_id)
    verified={'id':str(verification_id),'version':1,'tenant_id':str(identity.tenant_id),'legal_entity_id':str(identity.legal_entity_id),
        'source_type':doc.source_type,'verification':'HUMAN_VERIFIED_DOCUMENT','representation':'ACTUAL_DOCUMENT_SOURCE',
        'facts':facts,'_document_id':str(doc.id),'_document_version':1,'_field_sources':fields,
        'source_verification':{'actor_id':str(identity.actor_id),'reason':body['reason'],'draft_id':str(draft.id),
            'normalizer_version':NORMALIZER_VERSION,'transaction_id':str(transaction_id),'transaction_version':created['version'],
            'first_page':first,'last_page':last,'traces':traces}}
    session.add(ReferenceRecord(**identity.scope(),id=verification_id,version=1,kind='documents',label=doc.display_name,payload=verified));session.flush()
    session.add(TransactionDocument(**identity.scope(),transaction_id=transaction_id,transaction_version=created['version'],document_id=doc.id,
        document_version=1,role='INVOICE' if vendor else 'RECEIPT',first_page=first,last_page=last,verification_id=verification_id,verification_version=1,draft_id=draft.id))
    session.add(SourceCorrection(**identity.scope(),id=correction_id,transaction_id=transaction_id,transaction_version=created['version'],document_id=doc.id,
        document_version=1,actor_id=identity.actor_id,reason=body['reason'],changes=changes));session.flush()
    finance.audit(session,identity,'SOURCE_FACTS_VERIFIED',transaction_id,created['version'],body['reason'],correlation,{'document_id':str(doc.id),'draft_id':str(draft.id),'correction_count':len(changes)})
    job=finance.enqueue(session,identity,transaction_id,created['version'],'Evaluate source-verified canonical revision',correlation,f'document:{draft.id}:{created["version"]}')
    return created|job|{'document_id':str(doc.id),'source_verification_id':str(verification_id)}


def attach(session,identity,transaction_id,body,correlation):
    finance.scope_lock(session,identity);transaction=finance.get(session,Transaction,identity,transaction_id)
    finance.require_active(transaction);finance.review_guard(session,identity,transaction,body)
    if transaction.latest_version!=body['expected_version']:raise DomainError(409,'STALE_VERSION','Refresh the current transaction.')
    doc=finance.get(session,Document,identity,UUID(body['document_id']))
    if doc.state not in ('READY','NEEDS_INPUT','DEPENDENCY_UNAVAILABLE') or not documents.pages(session,identity,doc.id):
        raise DomainError(409,'DOCUMENT_NOT_REVIEWABLE','Attach a safely preprocessed document.')
    if any(l.document_id==doc.id for l in links(session,identity,transaction.id,transaction.latest_version)):
        raise DomainError(409,'DOCUMENT_ALREADY_LINKED','This document is already attached to the current version.')
    version=session.scalar(scope_query(select(TransactionVersion),TransactionVersion,identity).where(TransactionVersion.transaction_id==transaction.id,TransactionVersion.version==transaction.latest_version))
    payload=deepcopy(version.payload)
    if body['role']=='RECEIPT':
        if transaction.branch!='EMPLOYEE_EXPENSE' or body.get('item_index') is None or not 0<=body['item_index']<len(payload['items']):
            raise DomainError(422,'RECEIPT_MAPPING','Choose an actual employee expense item.')
        payload['items'][body['item_index']]['source_document_id']=str(doc.id)
    created=finance.revise(session,identity,transaction.id,{'expected_version':body['expected_version'],'reason':body['reason'],'transaction':payload},correlation)
    count=len(documents.pages(session,identity,doc.id));first=body.get('first_page',1);last=body.get('last_page') or count
    if not 1<=first<=last<=count:raise DomainError(422,'PAGE_RANGE','Choose actual one-based pages.')
    session.add(TransactionDocument(**identity.scope(),transaction_id=transaction.id,transaction_version=created['version'],document_id=doc.id,
        document_version=1,role=body['role'],first_page=first,last_page=last));session.flush()
    finance.audit(session,identity,'DOCUMENT_ATTACHED',transaction.id,created['version'],body['reason'],correlation,{'document_id':str(doc.id),'role':body['role']})
    return created


def sources(session,identity,transaction_id):
    transaction=finance.get(session,Transaction,identity,transaction_id)
    current=links(session,identity,transaction_id,transaction.latest_version)
    corrections=session.scalars(scope_query(select(SourceCorrection),SourceCorrection,identity).where(SourceCorrection.transaction_id==transaction_id).order_by(SourceCorrection.created_at)).all()
    return projection({'transaction_id':transaction_id,'transaction_version':transaction.latest_version,
        'documents':[{'role':l.role,'first_page':l.first_page,'last_page':l.last_page,'verified':l.verification_id is not None,
            'document':documents.detail(session,identity,l.document_id)} for l in current],
        'corrections':[{'version':c.transaction_version,'actor_id':c.actor_id,'reason':c.reason,'changes':c.changes,'created_at':c.created_at} for c in corrections]})
