from pathlib import Path
from uuid import uuid4
import hashlib
from sqlalchemy import select, text
from app.core.config import ROOT
from app.db.document_models import DocumentVersion, DocumentJob, UploadSession
from app.db.session import scope_query


def headers(): return {'Idempotency-Key':str(uuid4())}
def upload(client,name='vendor_native.pdf',content=None,mime='application/pdf'):
    response=client.post('/api/v1/uploads',json={'filename':name,'mime':mime,'source_type':'VENDOR_INVOICE'},headers=headers())
    assert response.status_code==201,response.text
    session=response.json();content=content if content is not None else (ROOT/'data/documents_phase2'/name).read_bytes()
    stored=client.post(session['bytes_url'],content=content,headers={'Content-Type':'application/octet-stream'})
    return session,stored


def test_two_step_original_hash_server_keys_replay_and_cross_tenant(environment):
    db,ctx,other,client,cfg=environment
    s,response=upload(client);assert response.status_code==200
    original=(ROOT/'data/documents_phase2/vendor_native.pdf').read_bytes()
    assert response.json()['sha256']==hashlib.sha256(original).hexdigest()
    key=headers();url=f'/api/v1/uploads/{s["id"]}/finalize'
    first=client.post(url,headers=key);assert first.status_code==202,first.text
    assert first.json()['state']=='QUEUED' and first.json()['finance_decision'] is None
    assert client.post(url,headers=key).json()==first.json()
    assert client.get(f'/api/v1/documents/{s["document_id"]}/original').status_code==409
    with db.session(ctx) as session:
        row=session.scalar(select(DocumentVersion));assert row.version==1 and row.byte_size==len(original)
        assert row.storage_key.endswith(str(__import__('uuid').UUID(row.storage_key.split('/')[-1])))
        assert session.query(DocumentJob).count()==1
    from test_document_pipeline import drain
    drain(environment)
    assert client.get(f'/api/v1/documents/{s["document_id"]}/original').content==original
    for suffix in ('','/original','/pages/1/preview'):
        assert client.get(f'/api/v1/documents/{s["document_id"]}{suffix}',headers={'Authorization':'Bearer test-second'}).status_code==404


def test_content_mismatch_quarantines_and_cannot_download(environment):
    db,ctx,other,client,cfg=environment
    s,response=upload(client,content=(ROOT/'data/documents_phase2/receipt_scan.png').read_bytes())
    r=client.post(f'/api/v1/uploads/{s["id"]}/finalize',headers=headers())
    assert r.json()['state']=='QUARANTINED' and r.json()['last_error']=='MIME_MISMATCH'
    assert client.get(f'/api/v1/documents/{s["document_id"]}/original').status_code==409
    with db.session(ctx) as session:assert session.query(DocumentJob).count()==0


def test_auth_actor_filename_and_immutable_stream(environment):
    db,ctx,other,client,cfg=environment
    assert client.post('/api/v1/uploads',json={'filename':'payload.exe','mime':'application/pdf','source_type':'VENDOR_INVOICE'},headers=headers()).status_code==400
    s,r=upload(client)
    assert client.post(s['bytes_url'],content=b'new bytes').status_code==409
    assert client.post(s['bytes_url'],content=b'evil',headers={'Authorization':'Bearer test-reader'}).status_code==403
    assert client.post(s['bytes_url'],content=b'evil',headers={'Authorization':'Bearer test-second'}).status_code==404


def test_added_tables_force_rls_and_original_immutable(environment):
    import pytest
    from sqlalchemy.exc import DBAPIError
    db,ctx,other,client,cfg=environment
    s,_=upload(client);client.post(f'/api/v1/uploads/{s["id"]}/finalize',headers=headers())
    with db.session(other) as session: assert session.scalar(select(DocumentVersion)) is None
    with pytest.raises(DBAPIError):
        with db.session(ctx) as session:session.execute(text("UPDATE document_versions SET sha256='bad'"))
    with db.engine.connect() as conn:
        assert conn.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace=current_schema()::regnamespace AND relkind='r' AND relrowsecurity AND relforcerowsecurity"))==49
