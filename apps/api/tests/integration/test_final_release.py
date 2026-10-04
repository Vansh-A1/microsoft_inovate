import json
from dataclasses import replace
from datetime import timedelta
from uuid import UUID,uuid4
import pytest
from app.core.serialization import utcnow
from app.db.models import AuditEvent
from app.db.document_models import Document,DocumentVersion,UploadSession,DocumentJob,ExtractionRun
from app.services import finance
from app.services.release_measurements import summary
from phase1 import seed


def test_walkthrough_decisions_are_retained_scoped_facts(environment,tmp_path,monkeypatch):
    from app import demo_routes
    db,ctx,other,client,cfg=environment
    result=seed(db,ctx,['vendor/clean'])[0]
    path=tmp_path/'scenarios.json';path.write_text(json.dumps({'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'complete':True,
        'scenarios':[{'key':'actual-pass','label':'Synthetic computed case','evaluation_id':result['latest_evaluation_id'],'decision':'HOLD'}]}));path.chmod(0o600)
    monkeypatch.setattr(demo_routes,'MANIFEST',path)
    response=client.get('/api/v1/development/scenarios');assert response.status_code==200,response.text
    data=response.json();assert data['ready'] and data['items'][0]['decision']=='PASS'  # ignores manifest's forged result
    assert client.get('/api/v1/development/scenarios',headers={'Authorization':'Bearer test-second'}).json()['items']==[]
    client.app.state.settings.identities['employee']={**client.app.state.settings.identities['test-reviewer'],'roles':['EMPLOYEE']}
    assert client.get('/api/v1/development/scenarios',headers={'Authorization':'Bearer employee'}).status_code==403
    templates=tmp_path/'templates';templates.mkdir();(templates/'vendor.json').write_text(json.dumps({'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'transaction':{'invoice_number':'SYNTHETIC-SCOPED-TEMPLATE'}}));(templates/'vendor.json').chmod(0o600)
    monkeypatch.setattr(demo_routes,'TEMPLATES',templates)
    assert client.get('/api/v1/development/templates/vendor').json()['invoice_number']=='SYNTHETIC-SCOPED-TEMPLATE'
    assert client.get('/api/v1/development/templates/vendor',headers={'Authorization':'Bearer test-second'}).json()['invoice_number']!='SYNTHETIC-SCOPED-TEMPLATE'
    from fastapi.testclient import TestClient
    from app import main
    # No Azure service is contacted for a route-disabled test. Storage is unused
    # because the development gate must reject before authentication/read work.
    monkeypatch.setattr(main,'configured_storage',lambda settings:object())
    with TestClient(main.create_app(replace(client.app.state.settings,development=False),db)) as enterprise:
        assert enterprise.get('/api/v1/development/scenarios',headers={'Authorization':'Bearer test-reviewer'}).status_code==404


def test_measurements_are_scoped_bounded_observations_not_guesses(environment):
    db,ctx,other,client,cfg=environment
    assert summary([])=={'samples':0,'median_ms':None,'maximum_ms':None}
    assert summary([10,30,20])=={'samples':3,'median_ms':20,'maximum_ms':30}
    before=client.get('/api/v1/operations/measurements');assert before.status_code==200,before.text
    assert before.json()['extraction']=={} and before.json()['audit_failures']['count'] is None
    now=utcnow();document=uuid4();upload=uuid4();job=uuid4()
    with db.session(ctx) as s:
        s.add(Document(**ctx.scope(),id=document,source_type='VENDOR_INVOICE',display_name='Synthetic measurement',state='NEEDS_INPUT'));s.flush()
        s.add(UploadSession(**ctx.scope(),id=upload,document_id=document,actor_id=ctx.actor_id,correlation_id='measurement',declared_mime='image/png',state='FINALIZED',expires_at=now+timedelta(hours=1)));s.flush()
        s.add(DocumentVersion(**ctx.scope(),id=document,version=1,upload_id=upload,storage_key='a'*64,sha256='b'*64,byte_size=1,detected_mime='image/png',actor_id=ctx.actor_id,correlation_id='measurement'));s.flush()
        s.add(DocumentJob(**ctx.scope(),id=job,document_id=document,document_version=1,generation=1,stage='EXTRACT',stage_version='document-pipeline-v1',stage_key='c'*64,state='SUCCEEDED',actor_id=ctx.actor_id,correlation_id='measurement'));s.flush()
        s.add(ExtractionRun(**ctx.scope(),document_id=document,document_version=1,job_id=job,attempt=1,status='PARTIAL',adapter='typellm',result={},metadata_json={'provider_id':'ENTERPRISE_VLM','raw_secret':'do-not-export','routing':{'enterprise':{'header_seconds':2,'line_seconds':3,'row_inventory_seconds':1,'unexpected':'do-not-export'}}},started_at=now-timedelta(seconds=10),completed_at=now))
        finance.audit(s,ctx,'DOCUMENT_STAGE_CLAIMED',document,1,'Synthetic stage claim','measurement',{'stage':'EXTRACT'})
        finance.audit(s,ctx,'DOCUMENT_STAGE_COMPLETED',document,1,'Synthetic stage completion','measurement',{'stage':'EXTRACT'})
    data=client.get('/api/v1/operations/measurements').json()
    assert data['extraction']['ENTERPRISE_VLM']['median_ms']==10000
    assert data['provider_calls']['header']['median_ms']==2000 and data['provider_calls']['rows']['median_ms']==3000
    assert data['document_stage_commit_elapsed']['EXTRACT']['samples']==1
    assert 'do-not-export' not in json.dumps(data)
    assert client.get('/api/v1/operations/measurements',headers={'Authorization':'Bearer test-second'}).json()['extraction']=={}
    client.app.state.settings.identities['employee']={**client.app.state.settings.identities['test-reviewer'],'roles':['EMPLOYEE']}
    assert client.get('/api/v1/operations/measurements',headers={'Authorization':'Bearer employee'}).status_code==403


def test_audit_failure_signal_preserves_rollback_and_redacts_exception(environment,monkeypatch):
    from app.core import observability
    db,ctx,other,client,cfg=environment;messages=[]
    monkeypatch.setattr(observability.log,'error',messages.append)
    with pytest.raises(RuntimeError,match='private-exception'):
        with db.session(ctx) as s:
            original=s.flush
            def fail_audit(*args,**kwargs):
                if any(isinstance(row,AuditEvent) for row in s.new):raise RuntimeError('private-exception-token')
                return original(*args,**kwargs)
            monkeypatch.setattr(s,'flush',fail_audit)
            finance.audit(s,ctx,'REVIEW_ASSIGNMENT',uuid4(),1,'Synthetic rollback test','private-correlation',{'secret':'never-log'})
    assert messages==['{"event":"audit_write_failed"}']
    with db.session(ctx) as s:assert not s.query(AuditEvent).filter(AuditEvent.action=='REVIEW_ASSIGNMENT').first()
