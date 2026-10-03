from dataclasses import replace
from pathlib import Path
from uuid import UUID
import pytest
from sqlalchemy import select,func
from app.core.config import ROOT
from app.documents.config import ProviderSettings
from app.db.document_models import DocumentJob, DocumentPage, ExtractionRun, Observation, DocumentDraft
from app.integrations.storage import LocalStorage
from app.services.document_worker import run_once,claim,load_work,perform,persist
from app.services.documents import detail
from test_document_intake import upload,headers


def drain(environment,providers=None,scanner=None):
    db,ctx,other,client,cfg=environment
    settings=client.app.state.settings
    # Provider tests must not inherit an operator's optional OCR/remote settings.
    settings=replace(settings,document_providers=providers or ProviderSettings())
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


def test_expired_document_lease_does_not_duplicate_pages_or_stages(environment):
    from datetime import timedelta
    from app.core.serialization import utcnow
    from app.documents.malware import UnconfiguredMalwareAdapter
    db,ctx,other,client,cfg=environment;s,_=upload(client)
    client.post(f'/api/v1/uploads/{s["id"]}/finalize',headers=headers())
    jid,owner,actor=claim(db,ctx);work=load_work(db,ctx,jid);settings=client.app.state.settings;storage=LocalStorage(settings.storage_root)
    output=perform(work,ctx,storage,settings,UnconfiguredMalwareAdapter())
    with db.session(ctx) as session:
        job=session.scalar(select(DocumentJob).where(DocumentJob.id==jid));job.lease_until=utcnow()-timedelta(seconds=1)
    new_id,new_owner,actor=claim(db,ctx);assert new_id==jid and new_owner!=owner
    persist(db,ctx,jid,owner,work,output,utcnow())
    with db.session(ctx) as session:assert session.scalar(select(func.count()).select_from(DocumentPage))==0
    persist(db,ctx,jid,new_owner,work,output,utcnow());drain(environment)
    data=client.get('/api/v1/documents/'+s['document_id']).json()
    assert data['state']=='READY' and len(data['pages'])==1 and len(data['jobs'])==5
    assert data['jobs'][0]['attempts']==2


def test_required_scanner_fails_closed_not_clean(environment):
    db,ctx,other,client,cfg=environment;s,_=upload(client)
    client.post(f'/api/v1/uploads/{s["id"]}/finalize',headers=headers())
    settings=client.app.state.settings;settings=replace(settings,document_limits=replace(settings.document_limits,malware_required=True))
    assert run_once(db,ctx,LocalStorage(settings.storage_root),settings)
    data=client.get('/api/v1/documents/'+s['document_id']).json()
    assert data['state']=='DEPENDENCY_UNAVAILABLE' and data['last_error']=='MALWARE_NOT_CONFIGURED' and not data['pages']
