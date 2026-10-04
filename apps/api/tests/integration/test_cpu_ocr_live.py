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
    response=client.post('/api/v1/uploads',json={'filename':'fictional-cpu-ocr.png','mime':'image/png','source_type':source_type},headers=headers())
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
