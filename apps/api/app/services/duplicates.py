"""Bounded indexed union of candidate searches; no fuzzy confirmation authority."""
from datetime import timedelta
from decimal import Decimal
import re, unicodedata
from uuid import UUID
from sqlalchemy import select, or_, and_, func
from rapidfuzz.fuzz import ratio
from app.core.errors import DomainError
from app.core.serialization import digest, projection
from app.db.models import ReferenceRecord, Transaction, TransactionVersion
from app.db.document_models import TransactionDocument, DocumentVersion, DocumentPage
from app.db.finance_models import DuplicateComparison, DuplicateResolution, ImageFingerprint, FingerprintBand
from app.db.session import scope_query

MAX_CANDIDATES=500
NORMALIZER='duplicate-keys-v1'
PHASH_VERSION='opencv-dct-phash-v1'


def aggressive(value):return re.sub(r'[^\w]','',unicodedata.normalize('NFKC',value or '').casefold(),flags=re.UNICODE)

def fingerprint(raw):
    import cv2,numpy as np
    from PIL import Image
    from io import BytesIO
    with Image.open(BytesIO(raw)) as im:
        im.load();width,height=im.size
        gray=np.array(im.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=np.float32)
    dct=cv2.dct(gray)[:8,:8];median=float(np.median(dct.flatten()[1:]));bits=dct>median
    number=0
    for bit in bits.flatten():number=(number<<1)|int(bit)
    return f'{number:016x}',{'algorithm':'pHash-DCT','library':'OpenCV','library_version':cv2.__version__,'hash_size':64,'preprocessing_version':PHASH_VERSION,'original_dimensions':[width,height],'derived_dimensions':[32,32],'crop':None,'low_information':float(np.std(gray))<2,'hash_bits':f'{number:016x}'}


def bands(bits):
    number=int(bits,16);offset=0;result=[]
    for i,width in enumerate((10,9,9,9,9,9,9)):
        result.append((i,f'{(number>>offset)&((1<<width)-1):03x}'));offset+=width
    return result


def ensure_fingerprints(session,identity,document_id,storage):
    originals=session.scalars(scope_query(select(DocumentPage),DocumentPage,identity).where(DocumentPage.document_id==document_id)).all()
    for page in originals:
        old=session.scalar(scope_query(select(ImageFingerprint),ImageFingerprint,identity).where(ImageFingerprint.document_id==document_id,ImageFingerprint.document_version==page.document_version,ImageFingerprint.page==page.page))
        if old:continue
        bits,metadata=fingerprint(storage.get(identity,page.preview_key));metadata.update(page=page.page,document_version=page.document_version)
        row=ImageFingerprint(**identity.scope(),document_id=document_id,document_version=page.document_version,page=page.page,hash_bits=bits,metadata_json=metadata)
        session.add(row);session.flush()
        if not metadata['low_information']:
            for band,value in bands(bits):session.add(FingerprintBand(**identity.scope(),fingerprint_id=row.id,band=band,bits=value))
    session.flush()


def image_candidates(session,identity,document_ids,maximum_distance):
    images=session.scalars(scope_query(select(ImageFingerprint),ImageFingerprint,identity).where(ImageFingerprint.document_id.in_(document_ids))).all() if document_ids else []
    matched={}
    for image in images:
        if image.metadata_json['low_information']:continue
        for band,value in bands(image.hash_bits):
            q=scope_query(select(ImageFingerprint).join(FingerprintBand,FingerprintBand.fingerprint_id==ImageFingerprint.id),ImageFingerprint,identity).where(FingerprintBand.band==band,FingerprintBand.bits==value,ImageFingerprint.document_id.not_in(document_ids)).limit(MAX_CANDIDATES+1)
            rows=session.scalars(q).all()
            if len(rows)>MAX_CANDIDATES:raise DomainError(503,'DUPLICATE_COVERAGE_LIMIT','Image candidate bucket exceeds the bounded retrieval limit.')
            for candidate in rows:
                distance=(int(image.hash_bits,16)^int(candidate.hash_bits,16)).bit_count()
                if distance<=maximum_distance:
                    key=str(candidate.document_id);prior=matched.get(key)
                    signal={'distance':distance,'hash_size':64,'source_page':image.page,'candidate_page':candidate.page,'source_hash':image.hash_bits,'candidate_hash':candidate.hash_bits,'algorithm':PHASH_VERSION}
                    if prior is None or distance<prior['distance']:matched[key]=signal
    return matched


def search(session,identity,version,profile):
    p=version.payload;vendor=p['branch']=='VENDOR_INVOICE';number=p.get('invoice_number' if vendor else 'receipt_number') or p.get('claim_number');day=version.business_date;amount=version.total_amount;party=version.party_id
    documents={UUID(s) for s in [p.get('source_document_id')]+[i.get('source_document_id') for i in p.get('items',[])] if s}
    documents.update(session.scalars(scope_query(select(TransactionDocument.document_id),TransactionDocument,identity).where(TransactionDocument.transaction_id==version.transaction_id,TransactionDocument.transaction_version==version.version)))
    originals=session.scalars(scope_query(select(DocumentVersion),DocumentVersion,identity).where(DocumentVersion.id.in_(documents))).all() if documents else []
    sha={r.sha256 for r in originals};same_docs=set()
    if sha:same_docs.update(session.scalars(scope_query(select(DocumentVersion.id),DocumentVersion,identity).where(DocumentVersion.sha256.in_(sha),DocumentVersion.id.not_in(documents))))
    visual=image_candidates(session,identity,list(documents),profile['phash_distance'])
    candidate_documents=documents|same_docs|{UUID(k) for k in visual}
    linked=set(session.scalars(scope_query(select(TransactionDocument.transaction_id),TransactionDocument,identity).where(TransactionDocument.document_id.in_(candidate_documents)))) if candidate_documents else set()
    predicates=[]
    if party and number:predicates.append(and_(TransactionVersion.party_id==party,func.regexp_replace(TransactionVersion.number_key,'[^a-zA-Z0-9]','','g')==aggressive(number)))
    if party and amount is not None and day:
        delta=Decimal(profile['near_amount_absolute']);window=timedelta(days=profile['duplicate_window_days'])
        predicates.append(and_(TransactionVersion.party_id==party,TransactionVersion.currency==version.currency,TransactionVersion.total_amount.between(amount-delta,amount+delta),TransactionVersion.business_date.between(day-window,day+window)))
    if linked:predicates.append(TransactionVersion.transaction_id.in_(linked))
    if candidate_documents:
        predicates.append(TransactionVersion.payload['source_document_id'].as_string().in_([str(i) for i in candidate_documents]))
    if p.get('po_id'):predicates.append(and_(TransactionVersion.party_id==party,TransactionVersion.payload['po_id'].as_string()==p['po_id'],TransactionVersion.business_date==day))
    if p.get('contract_id'):predicates.append(and_(TransactionVersion.party_id==party,TransactionVersion.payload['contract_id'].as_string()==p['contract_id'],TransactionVersion.payload['service_from'].as_string()==p.get('service_from')))
    if p.get('merchant') and day:
        predicates.append(and_(TransactionVersion.payload['merchant'].as_string()==p['merchant'],TransactionVersion.currency==version.currency,TransactionVersion.business_date.between(day-timedelta(days=profile['duplicate_window_days']),day+timedelta(days=profile['duplicate_window_days']))))
    candidates=[]
    if predicates:
        q=scope_query(select(TransactionVersion,Transaction).join(Transaction,Transaction.id==TransactionVersion.transaction_id),TransactionVersion,identity).where(TransactionVersion.version==Transaction.latest_version,TransactionVersion.transaction_id!=version.transaction_id,or_(*predicates)).order_by(TransactionVersion.created_at,TransactionVersion.id).limit(MAX_CANDIDATES+1)
        rows=session.execute(q).all()
        if len(rows)>MAX_CANDIDATES:raise DomainError(503,'DUPLICATE_COVERAGE_LIMIT','Narrow candidate criteria; complete retrieval is required.')
        candidates=[(str(r.transaction_id),r.version,'TRANSACTION',r.payload,t.eligible and t.processing_state=='COMPLETED',t.processing_state) for r,t in rows]
    history_predicates=[]
    if party and number:history_predicates.append(and_(ReferenceRecord.party_id==party,func.regexp_replace(ReferenceRecord.number_key,'[^a-zA-Z0-9]','','g')==aggressive(number)))
    if party and amount is not None and day:history_predicates.append(and_(ReferenceRecord.party_id==party,ReferenceRecord.currency==version.currency,ReferenceRecord.amount.between(amount-Decimal(profile['near_amount_absolute']),amount+Decimal(profile['near_amount_absolute'])),ReferenceRecord.business_date.between(day-timedelta(days=profile['duplicate_window_days']),day+timedelta(days=profile['duplicate_window_days']))))
    if history_predicates:
        rows=session.scalars(scope_query(select(ReferenceRecord),ReferenceRecord,identity).where(ReferenceRecord.kind=='historical_transactions',or_(*history_predicates)).limit(MAX_CANDIDATES+1)).all()
        if len(rows)>MAX_CANDIDATES:raise DomainError(503,'DUPLICATE_COVERAGE_LIMIT','Historical candidate coverage exceeds its bound.')
        candidates += [(str(r.id),r.version,'REFERENCE',r.payload,r.payload.get('lifecycle') not in ('CANCELLED','REVERSED','REJECTED') and (r.payload.get('capacity_state') in ('CONSUMED','RESERVED') or r.payload.get('lifecycle') in ('PAID','APPROVED','POSTED')),r.payload.get('lifecycle')) for r in rows]
    results=[]
    for cid,cversion,ctype,other,active,lifecycle in candidates:
        other_number=other.get('invoice_number' if vendor else 'receipt_number') or other.get('claim_number');other_amount=other.get('total_amount' if vendor else 'requested_amount',other.get('claimed_amount'));other_day=other.get('invoice_date' if vendor else 'expense_date');other_party=other.get('vendor_id' if vendor else 'employee_id');other_docs={s for s in [other.get('source_document_id')]+[i.get('source_document_id') for i in other.get('items',[])] if s}
        linked_docs=session.scalars(scope_query(select(TransactionDocument.document_id),TransactionDocument,identity).where(TransactionDocument.transaction_id==UUID(cid),TransactionDocument.transaction_version==cversion)).all() if ctype=='TRANSACTION' else []
        other_docs.update(str(s) for s in linked_docs)
        same_currency=p.get('currency')==other.get('currency');difference=abs(amount-Decimal(other_amount)) if same_currency and amount is not None and other_amount is not None else None
        raw_same=bool(number and other_number and number.strip().casefold()==other_number.strip().casefold());key_same=bool(number and other_number and aggressive(number)==aggressive(other_number))
        image=min((visual[did] for did in other_docs if did in visual),key=lambda x:x['distance'],default=None)
        shared_source=bool(other_docs&{str(d) for d in documents});exact_file=shared_source or bool(other_docs&{str(d) for d in same_docs})
        strong=bool(vendor and party and str(party)==other_party and raw_same and difference==0 and day and str(day)==other_day and same_currency)
        receipt_strong=bool(not vendor and p.get('receipt_number') and p['receipt_number']==other.get('receipt_number') and p.get('merchant') and p['merchant']==other.get('merchant') and difference==0 and str(day)==other_day)
        classification='STRONG_BUSINESS_MATCH' if strong or receipt_strong else 'EXACT_BYTES' if exact_file else 'POSSIBLE_DUPLICATE'
        signals=projection({'normalizer_version':NORMALIZER,'invoice_number_raw_same':raw_same,'aggressive_key_same':key_same,'source_number':number,'candidate_number':other_number,'number_similarity':ratio(number or '',other_number or ''),'party_same':str(party)==other_party,'amount_difference':difference,'currency_same':same_currency,'date_distance_days':abs((day-__import__('datetime').date.fromisoformat(other_day)).days) if day and other_day else None,'po_same':bool(p.get('po_id') and p.get('po_id')==other.get('po_id')),'contract_same':bool(p.get('contract_id') and p.get('contract_id')==other.get('contract_id')),'line_items_same':p.get('lines')==other.get('lines') if vendor else None,'exact_file':exact_file,'phash':image,'source_document_ids':sorted(str(d) for d in documents),'candidate_document_ids':sorted(other_docs),'candidate_lifecycle':lifecycle,'active_obligation':bool(active),'source_facts':safe_facts(p),'candidate_facts':safe_facts(other)})
        if not active and lifecycle in ('CANCELLED','REVERSED','REJECTED'):classification='DISTINCT'
        # Nearby unrelated numbers are retained only with a supported number/receipt/image signal.
        if not (strong or receipt_strong or key_same or exact_file or image or signals['number_similarity']>=profile['fuzzy_number_cutoff'] or p.get('contract_id') and p.get('contract_id')==other.get('contract_id')):continue
        key=digest({'transaction':str(version.transaction_id),'version':version.version,'candidate':cid,'candidate_version':cversion,'signals':signals,'algorithm':'duplicate-v1'})
        row=session.scalar(scope_query(select(DuplicateComparison),DuplicateComparison,identity).where(DuplicateComparison.comparison_key==key))
        if not row:
            row=DuplicateComparison(**identity.scope(),transaction_id=version.transaction_id,transaction_version=version.version,candidate_id=UUID(cid),candidate_version=cversion,candidate_type=ctype,classification=classification,signals=signals,comparison_key=key);session.add(row);session.flush()
        resolution=session.scalar(scope_query(select(DuplicateResolution),DuplicateResolution,identity).where(DuplicateResolution.comparison_id.in_(scope_query(select(DuplicateComparison.id),DuplicateComparison,identity).where(DuplicateComparison.transaction_id==version.transaction_id,DuplicateComparison.transaction_version==version.version,DuplicateComparison.candidate_id==UUID(cid),DuplicateComparison.candidate_version==cversion,DuplicateComparison.candidate_type==ctype))).order_by(DuplicateResolution.created_at.desc()).limit(1))
        # Bind disposition to both live versions; candidate revision invalidates it.
        results.append({'id':str(row.id),'version':1,'candidate_id':cid,'candidate_version':cversion,'candidate_type':ctype,'classification':classification,'signals':signals,'disposition':resolution.disposition if resolution else None,'resolution_id':str(resolution.id) if resolution else None})
    return results,{'status':'COMPLETE','candidate_count':len(results),'bounds':MAX_CANDIDATES,'algorithm':'duplicate-v1','image_search':'INDEXED_BANDS','same_file_search':bool(sha),'fuzzy_date_window_days':profile['duplicate_window_days']}


def safe_facts(p):
    return {k:v for k,v in p.items() if k not in ('payment_account_token','approvals','attendees')}
