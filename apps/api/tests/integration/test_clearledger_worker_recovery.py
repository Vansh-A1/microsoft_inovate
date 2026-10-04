"""An actual PostgreSQL lock timeout rolls back a claim; later work is idempotent."""
import json
from uuid import UUID,uuid4
from app.core.config import ROOT,Settings
from app.core.observability import log
from app.db.models import Job
from app.integrations.storage import LocalStorage
from app.schemas.canonical import fixture_canonical
from app.services.finance import get,scope_lock
from app.services.worker import run_scoped_cycle


def test_lock_timeout_preserves_queued_attempt_then_recovers(environment,tmp_path,monkeypatch):
    database,identity,other,client,cfg=environment
    events=[];monkeypatch.setattr(log,'warning',lambda message:events.append(json.loads(message)))
    payload=fixture_canonical(json.loads((ROOT/'data/golden_cases/vendor/clean.json').read_text())['transaction'])
    created=client.post('/api/v1/transactions',json=payload,headers={'Idempotency-Key':str(uuid4())})
    assert created.status_code==201
    record_id=created.json()['id']
    queued=client.post(f'/api/v1/transactions/{record_id}/evaluate',json={'expected_version':1,'reason':'Verify worker lock recovery'},headers={'Idempotency-Key':str(uuid4())})
    assert queued.status_code==202
    job_id=UUID(queued.json()['job_id']);storage=LocalStorage(tmp_path/'private')
    with database.session(identity) as held:
        scope_lock(held,identity)
        assert run_scoped_cycle(database,identity,storage,Settings.load()) is False
        job=get(held,Job,identity,job_id)
        assert job.state=='QUEUED' and job.attempts==0 and job.lease_owner is None
    assert events==[{'event':'worker_backoff','stage':'FINANCE','reason':'DATABASE_CONTENTION'}]
    assert run_scoped_cycle(database,identity,storage,Settings.load()) is True
    job=client.get('/api/v1/jobs/'+str(job_id)).json()
    assert job['state']=='SUCCEEDED' and job['attempts']==1
    case=client.get('/api/v1/transactions/'+record_id).json()
    assert case['decision']=='HOLD' and case['eligible'] is False
    assert run_scoped_cycle(database,identity,storage,Settings.load()) is True
    unchanged=client.get('/api/v1/jobs/'+str(job_id)).json()
    assert unchanged['attempts']==1 and unchanged['evaluation_id']==job['evaluation_id']
