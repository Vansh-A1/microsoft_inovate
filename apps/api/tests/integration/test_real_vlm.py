"""Opt-in real inference through the existing intake/worker/finance architecture."""
import base64
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4
import pytest
from app.core.config import ROOT,Settings
from app.documents.processor import DocumentProcessor
from app.extraction.gateway import GatewayTransport
from app.services.worker import run_once as finance_once
from test_document_intake import headers
from test_document_pipeline import drain
from test_vertical_slice import payload

pytestmark=[pytest.mark.integration_vlm,pytest.mark.skipif(os.environ.get('AP_RUN_REAL_VLM')!='1',reason='Opt-in real GPU/TypeLLM runtime required')]


@pytest.fixture
def providers(monkeypatch):
    settings=Settings.load();p=settings.document_providers
    assert p.transport=='TYPELLM_GATEWAY' and p.model_revision=='66285546d2b821cf421d4f5eb2576359d3770cd3'
    key=ROOT/'runtime/inference/gateway.key'
    assert key.is_file(),'Start the isolated inference gateway first'
    monkeypatch.setenv(p.gateway_token_env,key.read_text().strip())
    assert GatewayTransport(p).health()['status']=='AVAILABLE'
    return replace(p,ocr_executable=None,ocr_data_directory=None,ocr_library_directory=None)


def uploaded(environment,content,name,source_type,providers):
    db,ctx,other,client,cfg=environment
    response=client.post('/api/v1/uploads',json={'filename':name,'mime':'image/png','source_type':source_type},headers=headers())
    assert response.status_code==201,response.text
    upload=response.json();assert client.post(upload['bytes_url'],content=content).status_code==200
    assert client.post('/api/v1/uploads/'+upload['id']+'/finalize',headers=headers()).status_code==202
    drain(environment,providers)
    document=client.get('/api/v1/documents/'+upload['document_id']).json()
    return document


def live_metadata(doc):
    run=next(r for r in doc['extraction_runs'] if r['status'] in ('COMPLETED','PARTIAL'))
    metadata=run['metadata']
    assert run['adapter']=='typellm-sglang-client' and metadata['provider_id']=='ENTERPRISE_VLM'
    versions={v['name']:v['version'] for v in metadata['runtime_versions']}
    assert versions['typellm']=='0.5.1' and versions['model_revision']=='66285546d2b821cf421d4f5eb2576359d3770cd3'
    assert versions['precision']=='BF16' and versions['cache_isolation']=='SERIAL_FLUSH_PER_GENERATE'
    assert 'ENTERPRISE_VLM' in metadata['routing']['paths']
    return run


def test_real_typellm_text_smoke(providers):
    response=GatewayTransport(providers).generate(context='Untrusted receipt text: Total INR 12.50',
        questions={'total_raw':{'type':['string','null'],'thinking':False,'instructions':'Copy the printed total amount as a string. Do not calculate or approve anything.'}},images=None,timeout=30)
    assert response.result['total_raw']=='12.50'


@pytest.mark.parametrize('with_ocr',[False,True])
def test_real_primary_upload_layout_rows_and_critical_uncertainty(environment,providers,with_ocr):
    if with_ocr:
        providers=Settings.load().document_providers
        assert providers.ocr_executable,'The optional live OCR combination needs the configured CPU engine'
    file=Path(os.environ['AP_VLM_PRIMARY_DOCUMENT']);assert file.is_file()
    content=file.read_bytes();doc=uploaded(environment,content,'primary-real-invoice.png','VENDOR_INVOICE',providers)
    run=live_metadata(doc)
    if with_ocr:assert 'LOCAL_OCR' in run['metadata']['routing']['paths']
    assert doc['original']['sha256']==hashlib.sha256(content).hexdigest()
    by={o['field_path']:o for o in doc['observations']}
    assert by['vendor_name']['raw_value']=='East Repair Inc.'
    if with_ocr and by['invoice_number']['raw_value']!='US-001':
        assert by['invoice_number']['state']=='AMBIGUOUS' and 'US-001' in by['invoice_number']['raw_value']
        assert doc['draft']['candidate']['invoice_number'] is None
    else:assert by['invoice_number']['raw_value']=='US-001'
    assert by['total_amount']['raw_value']=='$154.06' and by['currency']['state']=='AMBIGUOUS'
    expected=[('Front and rear brake cables','1','100.00','100.00'),('New set of pedal arms','2','15.00','30.00'),('Labor 3hrs','3','5.00','15.00')]
    assert [[by[f'lines.{i}.{f}']['raw_value'] for f in ('description','quantity','unit_price','amount')] for i in range(3)]==[list(row) for row in expected]
    assert all(by[f'lines.{i}.amount']['source']['page']==1 and by[f'lines.{i}.amount']['source']['bbox'] is None for i in range(3))
    assert doc['state']=='NEEDS_INPUT' and doc['finance_decision'] is None
    assert doc['draft']['candidate']['currency'] is None and doc['draft']['candidate']['invoice_date'] is None
    _,_,_,client,_=environment
    assert client.get('/api/v1/documents/'+doc['id'],headers={'Authorization':'Bearer test-second'}).status_code==404
    # Confirming a page cannot dismiss missing currency, ambiguous date or tax.
    response=client.post('/api/v1/documents/'+doc['id']+'/commit',json={'draft_id':doc['draft']['id'],'transaction':payload(),
        'source_confirmed':True,'reason':'Attempt to bypass critical uncertainty','corrections':[]},headers=headers())
    assert response.status_code==422 and response.json()['error']['code']=='CANONICAL_SOURCE_UNRESOLVED'


def test_real_scan_to_normalization_source_correction_and_finance(environment,providers):
    from test_finance_phase3 import configured,approve,drain as drain_finance,report as finance_report
    environment=configured(environment)
    source=ROOT/'data/documents_phase2/vendor_native.pdf'
    rendered=DocumentProcessor().process(source)['pages'][0]
    doc=uploaded(environment,base64.b64decode(rendered['preview_base64']),'real-vlm-synthetic-invoice.png','VENDOR_INVOICE',providers)
    run=live_metadata(doc);candidate=doc['draft']['candidate']
    assert candidate['invoice_number']=='P2-INV-00128' and candidate['currency']=='INR' and candidate['total_amount']=='23600.00'
    assert all(isinstance(candidate[k],str) for k in ('total_amount','subtotal_amount','tax_amount'))
    # Independent post-inference source inspection. The small model currently
    # confuses NET/GROSS in this compact pipe table; retained raw observations
    # and arithmetic block automatic acceptance. Corrections are explicit,
    # source-linked and audited, never given to the model as answers.
    printed={'description':'Widgets','quantity':'20','unit_price':'1000.00','discount_amount':'0.00','net_amount':'20000.00',
        'tax_rate':'0.18','tax_amount':'3600.00','gross_amount':'23600.00','uom':'EA'}
    corrections=[{'field_path':'lines.0.'+k,'value':value,'page':1,'reason':'Integration source reviewer verified the literal printed row'}
        for k,value in printed.items() if candidate.get('lines.0.'+k)!=value]
    if candidate.get('tax_basis')!='EXCLUSIVE':
        corrections.append({'field_path':'tax_basis','value':'EXCLUSIVE','page':1,
            'reason':'Independent source review of the printed Tax basis: EXCLUSIVE label; model interpretation has no accounting authority'})
    db,ctx,other,client,cfg=environment
    response=client.post('/api/v1/documents/'+doc['id']+'/commit',json={'draft_id':doc['draft']['id'],'transaction':payload(),
        'source_confirmed':True,'reason':'Integration source reviewer checked the actual synthetic invoice and selected existing references',
        'corrections':corrections},headers=headers())
    assert response.status_code==201,response.text
    created=response.json();assert finance_once(db,ctx)
    job=client.get('/api/v1/jobs/'+created['job_id']).json();assert job['state']=='SUCCEEDED',job
    report=client.get('/api/v1/evaluations/'+job['evaluation_id']).json()
    assert report['extraction_mode']=='DOCUMENT_DERIVED' and report['transaction']['total_amount']=='23600.00'
    assert report['decision']=='HOLD' and next(r for r in report['rules'] if r['rule_id']=='DOC-001')['status']=='PASS'
    assert next(r for r in report['rules'] if r['rule_id']=='APR-001')['status']!='PASS'
    retained=client.get('/api/v1/documents/'+doc['id']).json()
    assert retained['extraction_runs'][0]==run and retained['observations']==doc['observations']
    sources=client.get('/api/v1/transactions/'+created['id']+'/sources').json()
    assert sources['documents'][0]['verified'] and len(sources['corrections'][0]['changes'])==len(corrections)
    old_id=report['evaluation_id']
    approve(client,created['id']);drain_finance(db,ctx)
    approved=finance_report(client,created['id'])
    assert approved['decision']=='PASS' and len(approved['rules'])==28
    assert approved['extraction_mode']=='DOCUMENT_DERIVED' and approved['normalizer_version']=='document-normalizer-v2'
    assert next(r for r in approved['rules'] if r['rule_id']=='GRN-001')['status']=='PASS'
    assert client.get('/api/v1/evaluations/'+old_id).json()['decision']=='HOLD'


def test_actual_connection_outage_is_retryable_and_cannot_be_empty_success(environment,providers):
    source=ROOT/'data/documents_phase2/receipt_scan.png'
    unavailable=replace(providers,endpoint='http://127.0.0.1:30009')
    doc=uploaded(environment,source.read_bytes(),'dependency-outage-receipt.png','EMPLOYEE_RECEIPT',unavailable)
    assert doc['state']=='FAILED_RETRYABLE' and doc['last_successful_stage']=='PREPROCESS'
    assert doc['last_error']=='PROVIDER_UNAVAILABLE' and doc['finance_decision'] is None
    assert doc['extraction_runs'][0]['status']=='FAILED' and not doc['observations'] and doc['draft'] is None


def test_configured_real_model_is_not_used_for_complete_native_pdf(environment,providers):
    db,ctx,other,client,cfg=environment
    response=client.post('/api/v1/uploads',json={'filename':'cheap-native.pdf','mime':'application/pdf','source_type':'VENDOR_INVOICE'},headers=headers())
    u=response.json();client.post(u['bytes_url'],content=(ROOT/'data/documents_phase2/vendor_native.pdf').read_bytes())
    client.post('/api/v1/uploads/'+u['id']+'/finalize',headers=headers());drain(environment,providers)
    doc=client.get('/api/v1/documents/'+u['document_id']).json();assert doc['state']=='READY'
    metadata=doc['extraction_runs'][0]['metadata']
    assert metadata['provider_id']=='NATIVE_TEXT' and metadata['routing']['vlm_status']=='CONFIGURED_NOT_NEEDED'
