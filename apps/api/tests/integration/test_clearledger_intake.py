"""Real scoped database/worker tests of Auto purpose, retained originals and guards."""
import hashlib
from uuid import uuid4
import pytest
from sqlalchemy import select
from app.core.config import ROOT
from app.db.models import AuditEvent
from app.db.document_models import DocumentVersion
from test_document_intake import headers
from test_document_pipeline import drain


def test_authenticated_intake_capabilities_disclose_missing_scanner_without_secret_paths(environment,monkeypatch):
    _,_,_,client,_=environment
    monkeypatch.delenv('AP_MALWARE_SCANNER_EXECUTABLE',raising=False)
    data=client.get('/api/v1/documents/intake-capabilities').json()
    assert data=={'malware_required':False,'malware_scanner':'NOT_CONFIGURED','maximum_bytes':25*1024*1024,'maximum_pages':30}
    assert client.get('/api/v1/documents/intake-capabilities',headers={'Authorization':'Bearer untrusted'}).status_code==401

def uploaded(client,name,mime):
    content=(ROOT/'data/documents_phase2'/name).read_bytes()
    r=client.post('/api/v1/uploads',json={'filename':name,'mime':mime,'source_type':'AUTO'},headers=headers())
    assert r.status_code==201,r.text
    upload=r.json();assert client.post(upload['bytes_url'],content=content).status_code==200
    assert client.post('/api/v1/uploads/'+upload['id']+'/finalize',headers=headers()).status_code==202
    return upload['document_id'],content

@pytest.mark.parametrize('name,kind',[('vendor_native.pdf','VENDOR_INVOICE'),('receipt_native.pdf','EMPLOYEE_RECEIPT')])
def test_auto_native_purpose_only_suggests_branch_not_finance_outcome(environment,name,kind):
    db,ctx,other,client,cfg=environment
    identifier,content=uploaded(client,name,'application/pdf');drain(environment)
    doc=client.get('/api/v1/documents/'+identifier).json()
    assert doc['source_type']==kind and doc['intake_hint']=='AUTO' and doc['state']=='READY',doc
    assert doc['finance_decision'] is None and doc['manual_source_verification_required']
    assert doc['jobs'][0]['metadata']['classification']['state']=='SUGGESTED'
    assert doc['original']['sha256']==hashlib.sha256(content).hexdigest()
    assert client.get('/api/v1/documents/'+identifier,headers={'Authorization':'Bearer test-second'}).status_code==404
    with db.session(ctx) as s:
        assert s.scalar(select(AuditEvent).where(AuditEvent.object_id==identifier,AuditEvent.action=='DOCUMENT_PURPOSE_SUGGESTED'))

def test_unclear_auto_type_stops_before_inference_and_confirmation_is_scoped_idempotent(environment):
    db,ctx,other,client,cfg=environment
    identifier,content=uploaded(client,'receipt_scan.png','image/png');drain(environment)
    path='/api/v1/documents/'+identifier
    doc=client.get(path).json()
    assert doc['state']=='NEEDS_INPUT' and doc['last_error']=='DOCUMENT_TYPE_UNCONFIRMED'
    assert doc['draft'] is None and not doc['extraction_runs'] and len(doc['jobs'])==1
    assert doc['source_type']=='SUPPORTING_DOCUMENT' and doc['generation']==1
    body={'expected_generation':1,'source_type':'EMPLOYEE_RECEIPT','reason':'Inspected the printed merchant receipt type'}
    assert client.post(path+'/purpose',json=body,headers={'Authorization':'Bearer test-second',**headers()}).status_code==404
    assert client.post(path+'/purpose',json=body,headers={'Authorization':'Bearer test-reader',**headers()}).status_code==403
    assert client.post(path+'/purpose',json=body|{'expected_generation':2},headers=headers()).status_code==409
    key=headers();first=client.post(path+'/purpose',json=body,headers=key);assert first.status_code==200,first.text
    assert client.post(path+'/purpose',json=body,headers=key).json()==first.json()
    assert first.json()['generation']==2 and first.json()['source_type']=='EMPLOYEE_RECEIPT'
    drain(environment)
    final=client.get(path).json()
    assert final['state']=='DEPENDENCY_UNAVAILABLE' and final['finance_decision'] is None
    assert final['original']['sha256']==hashlib.sha256(content).hexdigest() and len(final['pages'])==1
    assert client.post(path+'/purpose',json=body,headers=headers()).status_code==409
    with db.session(ctx) as s:
        assert len(s.scalars(select(DocumentVersion).where(DocumentVersion.id==identifier)).all())==1
        assert len(s.scalars(select(AuditEvent).where(AuditEvent.object_id==identifier,AuditEvent.action=='DOCUMENT_PURPOSE_CONFIRMED')).all())==1
