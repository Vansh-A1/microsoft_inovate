from dataclasses import replace
from pathlib import Path
from uuid import UUID
import pytest
from sqlalchemy import select,func
from app.core.config import ROOT
from app.documents.config import ProviderSettings
from app.db.document_models import DocumentJob, DocumentPage, ExtractionRun, Observation, DocumentDraft
from app.integrations.storage import LocalStorage
from app.services.document_worker import run_once
from app.services.documents import detail
from test_document_intake import upload,headers


def drain(environment,providers=None,scanner=None):
    db,ctx,other,client,cfg=environment
    settings=client.app.state.settings
    if providers:settings=replace(settings,document_providers=providers)
    for _ in range(10):
        if not run_once(db,ctx,LocalStorage(settings.storage_root),settings,scanner):break


def test_real_pdf_stages_observations_draft_replay(environment):
    db,ctx,other,client,cfg=environment;s,_=upload(client)
    client.post(f'/api/v1/uploads/{s["id"]}/finalize',headers=headers());drain(environment)
    data=client.get(f'/api/v1/documents/{s["document_id"]}').json()
    assert data['state']=='READY',data
    assert [j['stage'] for j in data['jobs']]==['PREPROCESS','EXTRACT','NORMALIZE','VALIDATE','FINALIZE']
    assert all(j['state']=='SUCCEEDED' for j in data['jobs'])
    assert data['jobs'][0]['metadata']['scan']['status']=='NOT_CONFIGURED'
    assert data['draft']['candidate']['total_amount']=='23600.00' and data['draft']['traces']
    assert data['finance_decision'] is None and data['manual_source_verification_required']
    assert client.get(data['pages'][0]['preview_url']).headers['content-type']=='image/png'
    drain(environment)
    with db.session(ctx) as session:
        assert session.scalar(select(func.count()).select_from(DocumentPage))==1
        assert session.scalar(select(func.count()).select_from(ExtractionRun))==1
        assert session.scalar(select(func.count()).select_from(DocumentJob))==5
        assert session.scalar(select(func.count()).select_from(DocumentDraft))==2


@pytest.mark.parametrize('name,expected',[('ambiguous_date.pdf','NEEDS_INPUT'),('conflicting_total.pdf','NEEDS_INPUT'),('password_protected.pdf','QUARANTINED'),('corrupt.pdf','QUARANTINED'),('uncertain_bundle.pdf','NEEDS_INPUT')])
def test_uncertainty_and_permanent_failure(environment,name,expected):
    db,ctx,other,client,cfg=environment;s,_=upload(client,name)
    client.post(f'/api/v1/uploads/{s["id"]}/finalize',headers=headers());drain(environment)
    data=client.get(f'/api/v1/documents/{s["document_id"]}').json()
    assert data['state']==expected,data
    assert data['finance_decision'] is None
    if expected=='QUARANTINED':assert data['jobs'][0]['attempts']==1 and len(data['jobs'])==1


def test_visual_without_provider_retains_page_and_dependency_state(environment):
    db,ctx,other,client,cfg=environment;s,_=upload(client,'receipt_scan.png',mime='image/png')
    client.post(f'/api/v1/uploads/{s["id"]}/finalize',headers=headers());drain(environment)
    data=client.get(f'/api/v1/documents/{s["document_id"]}').json()
    assert data['state']=='DEPENDENCY_UNAVAILABLE' and data['last_successful_stage']=='PREPROCESS'
    assert data['last_error']=='VISUAL_PROVIDER_NOT_CONFIGURED' and len(data['pages'])==1
    assert data['extraction_runs'][0]['status']=='FAILED'


def test_real_cpu_ocr_photo_actual_strings_and_original_boxes(environment):
    db,ctx,other,client,cfg=environment
    r=client.post('/api/v1/uploads',json={'filename':'receipt_photo.jpg','mime':'image/jpeg','source_type':'EMPLOYEE_RECEIPT'},headers=headers())
    s=r.json();client.post(s['bytes_url'],content=(ROOT/'data/documents_phase2/receipt_photo.jpg').read_bytes())
    client.post(f'/api/v1/uploads/{s["id"]}/finalize',headers=headers())
    providers=ProviderSettings(ocr_executable=str(ROOT/'runtime/tools/ocr/usr/bin/tesseract'),ocr_data_directory=str(ROOT/'runtime/tools/ocr/usr/share/tesseract-ocr/5/tessdata'),ocr_library_directory=str(ROOT/'runtime/tools/ocr/usr/lib/x86_64-linux-gnu'))
    drain(environment,providers)
    data=client.get(f'/api/v1/documents/{s["document_id"]}').json()
    assert data['state']=='READY',data
    assert data['draft']['candidate']['total_amount']=='500.00'
    assert data['extraction_runs'][0]['metadata']['provider_id']=='LOCAL_OCR'
    source=next(o for o in data['observations'] if o['field_path']=='total_amount')['source']
    assert source['page']==1 and source['bbox'] is not None
