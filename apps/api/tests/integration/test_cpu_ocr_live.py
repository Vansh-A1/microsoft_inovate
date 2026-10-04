"""Opt-in actual pinned CPU OCR through uploads, durable stages and source gate."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import pytest
from app.core.config import ROOT,Settings
from app.documents.processor import DocumentFailure
from app.extraction.cpu_ocr import CPUOCR
from test_document_intake import headers
from test_document_pipeline import drain
from test_vertical_slice import payload

pytestmark=pytest.mark.skipif(os.environ.get('AP_RUN_CPU_OCR')!='1',reason='Opt-in isolated pinned CPU OCR assets required')


def providers():
    python=ROOT/'runtime/ocr-rapid/.venv/bin/python'
    assert python.is_file()
    return replace(Settings.load().document_providers,ocr_backend='RAPIDOCR_CPU_EXPERIMENTAL',ocr_python=str(python),endpoint=None,model=None)


def upload(environment,file,source_type,settings):
    _,_,_,client,_=environment
    content=file.read_bytes()
    response=client.post('/api/v1/uploads',json={'filename':'fictional-cpu-ocr'+file.suffix,'mime':'application/pdf' if file.suffix=='.pdf' else 'image/png','source_type':source_type},headers=headers())
    assert response.status_code==201,response.text
    u=response.json();assert client.post(u['bytes_url'],content=content).status_code==200
    assert client.post('/api/v1/uploads/'+u['id']+'/finalize',headers=headers()).status_code==202
    drain(environment,settings)
    doc=client.get('/api/v1/documents/'+u['document_id']).json()
    assert doc['original']['sha256']==hashlib.sha256(content).hexdigest()
    return doc


def test_actual_cpu_scan_maps_measured_facts_without_vlm_or_finance_clearance(environment):
    doc=upload(environment,ROOT/'data/clearledger_challenge/t04.png','VENDOR_INVOICE',providers())
    assert doc['state']=='NEEDS_INPUT' and doc['finance_decision'] is None
    run=doc['extraction_runs'][0];metadata=run['metadata'];routing=metadata['routing']
    assert metadata['provider_id']=='LOCAL_OCR' and 'RAPIDOCR_CPU' in metadata['model_id']
    assert routing['paths']==['LOCAL_OCR'] and 'ENTERPRISE_VLM' not in routing['paths']
    engine=routing['ocr_provenance'][0]['runtime']
    assert engine['packages']=={'rapidocr':'3.9.2','onnxruntime':'1.23.2'}
    assert all(p==['CPUExecutionProvider'] for p in engine['providers'].values())
    candidate=doc['draft']['candidate']
    assert candidate['invoice_number']=='CL-FICTION-4' and candidate['currency']=='INR' and candidate['total_amount']=='236.00'
    assert [candidate[f'lines.{i}.amount'] for i in range(2)]==['150.00','50.00']
    assert candidate.get('lines.0.tax_amount') is None and candidate.get('lines.0.discount_amount') is None
    by={o['field_path']:o for o in doc['observations']}
    assert by['lines.0.tax_amount']['state']=='MISSING' and by['lines.0.tax_amount']['raw_value'] is None
    assert by['lines.0.tax_amount']['source'] is None
    assert by['lines.1.amount']['source']['page']==1 and by['lines.1.amount']['source']['bbox'] is not None
    _,_,_,client,_=environment
    assert client.get('/api/v1/documents/'+doc['id'],headers={'Authorization':'Bearer test-second'}).status_code==404
    response=client.post('/api/v1/documents/'+doc['id']+'/commit',json={'draft_id':doc['draft']['id'],'transaction':payload(),
        'source_confirmed':True,'reason':'Missing accounting facts cannot be bypassed','corrections':[]},headers=headers())
    assert response.status_code==422 and response.json()['error']['code']=='CANONICAL_SOURCE_UNRESOLVED'


def test_missing_cpu_runtime_uses_real_tesseract_and_records_failure(environment):
    settings=replace(providers(),ocr_python='/tmp/clearledger-unavailable-ocr-python')
    assert settings.ocr_executable
    doc=upload(environment,ROOT/'data/documents_phase2/receipt_scan.png','EMPLOYEE_RECEIPT',settings)
    assert doc['state']=='READY' and doc['finance_decision'] is None
    source=doc['extraction_runs'][0]['metadata']['routing']['ocr_provenance'][0]
    assert source['provider']=='TESSERACT' and source['runtime']['candidate_failure']=='OCR_NOT_CONFIGURED'
    assert doc['draft']['candidate']['total_amount']=='500.00'


def test_actual_wrapped_scan_recovers_missed_glyph_with_measured_crop_without_vlm(environment):
    doc=upload(environment,ROOT/'data/clearledger_challenge/h04.png','VENDOR_INVOICE',providers())
    assert doc['state']=='NEEDS_INPUT' and doc['finance_decision'] is None
    routing=doc['extraction_runs'][0]['metadata']['routing']
    assert routing['paths']==['LOCAL_OCR']
    retry=routing['ocr_provenance'][0]['runtime']['row_retries']
    assert len(retry)==1 and retry[0]['field']=='quantity' and retry[0]['status']=='MEASURED_CELL_READ'
    assert retry[0]['scale']==2 and len(retry[0]['crop_extents_pixels'])==4
    candidate=doc['draft']['candidate']
    assert candidate['lines.0.description']=='Notebook cases recycled paper'
    assert [candidate[f'lines.{i}.quantity'] for i in range(2)]==['2','1']
    by={o['field_path']:o for o in doc['observations']}
    assert by['lines.1.quantity']['state']=='PRESENT'
    source=by['lines.1.quantity']['source'];box=source['bbox']
    assert source['page']==1 and source['observed_value']=='1'
    assert .48<box['x1']<box['x2']<.55 and .44<box['y1']<box['y2']<.49
    assert box['x2']-box['x1']<.03  # actual detected glyph region, not full row crop
    assert by['lines.1.tax_amount']['state']=='MISSING' and candidate.get('lines.1.tax_amount') is None


def test_actual_unread_quantity_keeps_distinct_source_rows_and_precise_human_question(environment):
    configured=Settings.load().document_providers
    settings=replace(providers(),endpoint=configured.endpoint,model=configured.model)
    doc=upload(environment,ROOT/'data/clearledger_reserved/r07.png','VENDOR_INVOICE',settings)
    assert doc['state']=='NEEDS_INPUT' and doc['finance_decision'] is None
    routing=doc['extraction_runs'][0]['metadata']['routing']
    assert routing['paths']==['LOCAL_OCR'] and routing['vlm_status']=='CONFIGURED_NOT_NEEDED'
    assert routing['sufficiency']=='SOURCE_CELL_CONFIRMATION_REQUIRED'
    assert len(routing['source_rows'])==3 and len({r['identity'] for r in routing['source_rows']})==3
    candidate=doc['draft']['candidate']
    assert [candidate[f'lines.{i}.description'] for i in range(3)]==['Felt document sleeves','Desk index tabs','Binder spines']
    assert candidate['lines.1.quantity'] is None and candidate['lines.1.unit_price']=='19.25' and candidate['lines.1.amount']=='19.25'
    by={o['field_path']:o for o in doc['observations']};quantity=by['lines.1.quantity']
    assert quantity['state']=='MISSING' and quantity['raw_value'] is None and quantity['source']['page']==1 and quantity['source']['bbox'] is None
    question=next(f['message'] for f in doc['draft']['findings'] if f['field']=='lines.1.quantity')
    assert 'line 2 (Desk index tabs) on page 1' in question and 'do not calculate' in question
    _,_,_,client,_=environment
    response=client.post('/api/v1/documents/'+doc['id']+'/commit',json={'draft_id':doc['draft']['id'],'transaction':payload(),
        'source_confirmed':True,'reason':'An unread quantity cannot be supplied by a demo template','corrections':[]},headers=headers())
    assert response.status_code==422 and response.json()['error']['code']=='CANONICAL_SOURCE_UNRESOLVED'


@pytest.mark.parametrize('filename',['q03.png','q04.pdf'])
def test_actual_legitimate_identical_printed_items_keep_distinct_positions_and_pages(environment,filename):
    doc=upload(environment,ROOT/'data/clearledger_row_identity'/filename,'VENDOR_INVOICE',providers())
    assert doc['state']=='NEEDS_INPUT' and doc['finance_decision'] is None
    candidate=doc['draft']['candidate']
    assert [candidate[f'lines.{i}.quantity'] for i in range(3)]==['2','2','2']
    assert len({candidate[f'lines.{i}.description'] for i in range(3)})==1
    rows=doc['extraction_runs'][0]['metadata']['routing']['source_rows']
    assert len(rows)==3 and len({r['identity'] for r in rows})==3
    assert [r['page'] for r in rows]==([1,2,3] if filename.endswith('.pdf') else [1,1,1])


def test_cpu_source_scope_and_owned_child_restart_preserve_actual_reading(tmp_path):
    original=ROOT/'data/clearledger_challenge/t04.png';file=tmp_path/'derived.png';file.write_bytes(original.read_bytes())
    from PIL import Image
    with Image.open(file) as image:dimensions=list(image.size)
    transform={'derived_dimensions':dimensions,'exif_orientation':1}
    engine=CPUOCR(ROOT/'runtime/ocr-rapid/.venv/bin/python',tmp_path)
    try:
        with pytest.raises(DocumentFailure,match='OCR_SOURCE_SCOPE_INVALID'):engine.recognize(original,transform)
        first=engine.recognize(file,transform);pid=engine.process.pid
        engine.process.terminate();engine.process.wait(timeout=5)
        second=engine.recognize(file,transform)
        assert engine.process.pid!=pid and first.text==second.text and '236.00' in second.text
        assert first.provider==second.provider=='RAPIDOCR_CPU'
    finally:engine.close()


def test_actual_rotated_scan_preserves_original_hash_boxes_and_derivative_attestation(environment):
    doc=upload(environment,ROOT/'data/clearledger_rotation/d03.png','VENDOR_INVOICE',providers())
    assert doc['state']=='NEEDS_INPUT' and doc['finance_decision'] is None
    routing=doc['extraction_runs'][0]['metadata']['routing'];engine=routing['ocr_provenance'][0]['runtime']
    assert routing['paths']==['LOCAL_OCR'] and engine['layout_alignment']['clockwise_degrees']==90
    derivative=engine['aligned_pixel_read']
    assert derivative['image_bytes_transformed'] is True and len(derivative['derived_sha256'])==64
    assert derivative['source_to_layout']['source_dimensions']==[992,1440]
    candidate=doc['draft']['candidate']
    assert [candidate[f'lines.{i}.amount'] for i in range(3)]==['42.75','20.00','19.50']
    by={o['field_path']:o for o in doc['observations']}
    # Measured source coordinates locate the original rotated scan, not the
    # upright OCR derivative. The first-row amount is near its original top.
    box=by['lines.0.amount']['source']['bbox']
    assert .23<box['x1']<box['x2']<.28 and .04<box['y1']<box['y2']<.11
    assert candidate['tax_basis'] is None and candidate.get('lines.0.tax_amount') is None


def test_actual_two_blank_cells_keep_partial_rows_and_block_canonical_commit(environment):
    configured=Settings.load().document_providers
    doc=upload(environment,ROOT/'data/clearledger_row_identity/q06.pdf','VENDOR_INVOICE',
        replace(providers(),endpoint=configured.endpoint,model=configured.model))
    assert doc['state']=='NEEDS_INPUT' and doc['finance_decision'] is None
    routing=doc['extraction_runs'][0]['metadata']['routing']
    assert routing['paths']==['NATIVE_TEXT'] and 'ENTERPRISE_VLM' not in routing['paths']
    candidate=doc['draft']['candidate'];by={o['field_path']:o for o in doc['observations']}
    assert [candidate[f'lines.{i}.description'] for i in range(3)]==['Canvas file pouches','Blue record labels','Canvas file pouches']
    assert candidate['lines.1.amount']=='37.50'
    for field in ('quantity','unit_price'):
        path='lines.1.'+field
        assert candidate[path] is None and by[path]['state']=='MISSING' and by[path]['raw_value'] is None
        question=next(f['message'] for f in doc['draft']['findings'] if f['field']==path and f.get('code')=='SOURCE_CELL_UNREAD')
        assert 'line 2 (Blue record labels)' in question and 'do not calculate' in question
    _,_,_,client,_=environment
    response=client.post('/api/v1/documents/'+doc['id']+'/commit',json={'draft_id':doc['draft']['id'],'transaction':payload(),
        'source_confirmed':True,'reason':'Two absent cells must remain unknown','corrections':[]},headers=headers())
    assert response.status_code==422 and response.json()['error']['code']=='CANONICAL_SOURCE_UNRESOLVED'


def test_actual_deskew_border_padding_is_excluded_without_losing_valid_source_regions(tmp_path):
    import base64,json
    from app.documents.processor import DocumentProcessor
    from app.extraction.layout import printed_layout
    manifest=json.loads((ROOT/'data/clearledger_public/manifest.json').read_text())
    reference=next(c['source'] for c in manifest['cases'] if c['id']=='p02')
    source=ROOT/'runtime/clearledger/public-research'/reference['local_path']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==reference['sha256']
    page=DocumentProcessor().process(source)['pages'][0]
    preview=tmp_path/'preview.png';content=base64.b64decode(page['preview_base64']);preview.write_bytes(content)
    engine=CPUOCR(ROOT/'runtime/ocr-rapid/.venv/bin/python',tmp_path)
    try:
        actual=engine.recognize(preview,page['transform'])
        assert actual.provider=='RAPIDOCR_CPU' and preview.read_bytes()==content
        excluded=engine.metadata['aligned_pixel_read']['excluded_source_regions']
        assert len(excluded)==1 and excluded[0]['reason']=='DETECTOR_REGION_OUTSIDE_ORIGINAL_CANVAS'
        assert excluded[0]['mapped_pixels']['y1']<0
        assert all(0<=v<=1 for s in actual.spans for v in s['bbox'].values())
        assert excluded[0]['text'] not in [s['text'] for s in actual.spans]
        h,rows,_=printed_layout({'spans':actual.spans})
        assert dict((f,v) for f,v,_ in h)['tax_amount']=='AED 3.00' and len(rows)==1
    finally:engine.close()
