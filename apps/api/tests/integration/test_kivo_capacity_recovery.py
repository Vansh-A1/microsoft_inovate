"""Real 5s lock boundary: atomic rollback, retained source and unchanged replay."""
from decimal import Decimal
import json
import os
import re
from time import perf_counter
from uuid import UUID,uuid4
import pytest
from sqlalchemy import func,select,text
from sqlalchemy.exc import DBAPIError
from app.core.config import ROOT
from app.db.models import AuditEvent,Evaluation,EvidenceObject,IdempotencyRecord,Job,Report,Transaction,TransactionVersion
from app.db.finance_models import FinanceAllocation,AllocationEvent,BudgetEvent
from app.services import finance,finance_ledger
from app.services.worker import claim
from test_finance_phase3 import configured,payload,trusted_source,create,approve


MODELS=(Transaction,TransactionVersion,Evaluation,Report,EvidenceObject,AuditEvent,
        IdempotencyRecord,FinanceAllocation,AllocationEvent,BudgetEvent)


def retained(session):
    return {'counts':[session.scalar(select(func.count()).select_from(model)) for model in MODELS],
        'audit':[(row.sequence,row.event_hash) for row in session.scalars(select(AuditEvent).order_by(AuditEvent.sequence))],
        'versions':[(row.id,row.content_digest) for row in session.scalars(select(TransactionVersion).order_by(TransactionVersion.id))]}


def metric(name,data):
    label=os.getenv('AP_CAPACITY_MEASUREMENT_LABEL')
    if not label:return
    assert re.fullmatch('[a-z0-9-]{1,40}',label)
    path=ROOT/'runtime/kivo-concurrency'/f'{label}-{name}.json';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as file:json.dump(data,file,indent=2);file.write('\n')


def current_lease(db,ctx):
    for _ in range(100):
        lease=claim(db,ctx)
        if not lease:break
        jid,owner,actor=lease
        with db.session(ctx) as s:
            job=finance.get(s,Job,ctx,jid);transaction=finance.get(s,Transaction,ctx,job.transaction_id)
            if job.generation==transaction.row_version:return jid,owner
            finance.finalize(s,ctx,jid,owner)
    raise AssertionError('Expected one real committed current-generation lease')


def test_api_scope_timeout_rolls_back_key_then_same_request_replays(environment):
    db,ctx,other,client,cfg=configured(environment)
    source=trusted_source(db,ctx,payload('vendor/clean'));key=str(uuid4())
    headers={'Idempotency-Key':key}
    with db.session(ctx) as held:
        finance.scope_lock(held,ctx);before=retained(held)
        assert held.scalar(text('SHOW lock_timeout'))=='5s'
        assert held.scalar(text('SHOW statement_timeout'))=='10s'
        started=perf_counter();failed=client.post('/api/v1/transactions',json=source,headers=headers)
        elapsed=round((perf_counter()-started)*1000,3)
        assert failed.status_code==503 and failed.json()['error']['code']=='DATABASE_UNAVAILABLE'
        assert failed.json()['error']['retryable'] is True
        assert retained(held)==before  # Includes no transaction, key or audit from the failed request.
    first=client.post('/api/v1/transactions',json=source,headers=headers)
    assert first.status_code==201,first.text
    with db.session(ctx) as s:after=retained(s)
    replay=client.post('/api/v1/transactions',json=source,headers=headers)
    assert replay.status_code==201 and replay.json()==first.json()
    with db.session(ctx) as s:
        assert retained(s)==after
        transaction=finance.get(s,Transaction,ctx,UUID(first.json()['id']))
        assert transaction.latest_version==1 and transaction.eligible is False and transaction.decision is None
        assert after['counts'][0]==before['counts'][0]+1
        assert after['counts'][1]==before['counts'][1]+1
        assert after['counts'][6]==before['counts'][6]+1
    metric('api-timeout',{'lock_timeout_ms':5000,'actual_failed_request_ms':elapsed,
        'status':503,'retryable':True,'failed_transaction_unchanged':True,'same_key_replay_one_case':True})


def test_finalization_scope_timeout_preserves_lease_source_audit_then_replays(environment):
    db,ctx,other,client,cfg=configured(environment)
    source=trusted_source(db,ctx,payload('vendor/clean'));tid=create(client,source);approve(client,tid)
    jid,owner=current_lease(db,ctx)
    with db.session(ctx) as held:
        finance.scope_lock(held,ctx);before=retained(held)
        job=finance.get(held,Job,ctx,jid);lease_until=job.lease_until
        assert job.state=='RUNNING' and job.attempts==1 and job.lease_owner==owner
        started=perf_counter()
        with pytest.raises(DBAPIError) as failure:
            with db.session(ctx) as s:finance.finalize(s,ctx,jid,owner)
        elapsed=round((perf_counter()-started)*1000,3)
        assert failure.value.orig.sqlstate=='55P03'
        assert retained(held)==before
        held.refresh(job)
        assert job.state=='RUNNING' and job.attempts==1 and job.lease_owner==owner and job.lease_until==lease_until
    with db.session(ctx) as s:eid=finance.finalize(s,ctx,jid,owner)
    with db.session(ctx) as s:
        after=retained(s);transaction=finance.get(s,Transaction,ctx,UUID(tid));job=finance.get(s,Job,ctx,jid)
        assert transaction.decision=='PASS' and transaction.eligible is True and transaction.latest_evaluation_id==eid
        assert job.state=='SUCCEEDED' and job.attempts==1 and job.result_evaluation_id==eid
        assert after['counts'][2]==before['counts'][2]+1 and after['counts'][3]==before['counts'][3]+1
        assert after['versions']==before['versions']
        assert sum((allocation.quantity for allocation,state in finance_ledger.active(s,ctx)
                    if allocation.kind=='GRN_LINE'),Decimal(0))==Decimal('20')
    with db.session(ctx) as s:assert finance.finalize(s,ctx,jid,owner)==eid
    with db.session(ctx) as s:assert retained(s)==after
    metric('finalization-timeout',{'lock_timeout_ms':5000,'actual_failed_finalization_ms':elapsed,
        'sqlstate':'55P03','failed_effects_and_lease_unchanged':True,'same_lease_one_evaluation_report_allocation_set':True,
        'canonical_version_unchanged':True,'replay_no_additional_effects':True})


def test_preclaimed_worker_timeout_records_retry_then_real_reclaim(environment,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import sleep
    from app.core.serialization import utcnow
    from app.services import worker
    db,ctx,other,client,cfg=configured(environment)
    source=trusted_source(db,ctx,payload('vendor/clean'));tid=create(client,source);approve(client,tid)
    jid,owner=current_lease(db,ctx);failed=Event();released=Event();measurements={}
    original=worker.finalize
    def observed(session,identity,job,lease):
        started=perf_counter()
        try:return original(session,identity,job,lease)
        except DBAPIError as error:
            measurements.update(sqlstate=error.orig.sqlstate,failed_finalization_ms=round((perf_counter()-started)*1000,3))
            failed.set();assert released.wait(20),'Release disposable blocker after actual failure'
            raise
    # Feed the real committed lease at the worker's claim/finalization boundary.
    # Only this stage handshake is instrumented; timeout, rollback, classification,
    # failure audit, scheduler backoff and subsequent reclaim use real code/SQL.
    with monkeypatch.context() as stage:
        stage.setattr(worker,'claim',lambda *args:(jid,owner,ctx.actor_id))
        stage.setattr(worker,'finalize',observed)
        with ThreadPoolExecutor(1) as pool:
            with db.session(ctx) as held:
                finance.scope_lock(held,ctx);before=retained(held)
                pending=pool.submit(worker.run_once,db,ctx)
                assert failed.wait(15),'Expected existing 5s PostgreSQL lock timeout'
                assert measurements['sqlstate']=='55P03' and retained(held)==before
            released.set();assert pending.result(timeout=20) is True
    with db.session(ctx) as s:
        job=finance.get(s,Job,ctx,jid);transaction=finance.get(s,Transaction,ctx,UUID(tid))
        assert job.state=='RETRYABLE' and job.attempts==1 and job.lease_until is None
        assert job.last_error=='DATABASE_UNAVAILABLE' and job.failure_retryable is True
        assert transaction.processing_state=='FAILED_RETRYABLE' and transaction.eligible is False
        recorded=retained(s)
        assert recorded['versions']==before['versions']
        assert all(recorded['counts'][index]==before['counts'][index] for index in (2,3,4,7,8,9))
        events=s.scalars(select(AuditEvent).where(AuditEvent.object_id==jid,AuditEvent.action=='JOB_RETRY_SCHEDULED')).all()
        assert len(events)==1
        remaining=max(0,(job.available_at-utcnow()).total_seconds())
        assert remaining<=3  # Existing attempt-one 2s + <1s jitter, no clock override.
    started=perf_counter();sleep(remaining+.05)
    assert worker.run_once(db,ctx) is True
    elapsed=round((perf_counter()-started)*1000,3)
    with db.session(ctx) as s:
        after=retained(s);job=finance.get(s,Job,ctx,jid);transaction=finance.get(s,Transaction,ctx,UUID(tid))
        assert job.state=='SUCCEEDED' and job.attempts==2 and transaction.decision=='PASS' and transaction.eligible is True
        assert after['counts'][2]==before['counts'][2]+1 and after['counts'][3]==before['counts'][3]+1
        assert after['versions']==before['versions'] and after['audit'][:len(before['audit'])]==before['audit']
    assert worker.run_once(db,ctx) is False
    with db.session(ctx) as s:assert retained(s)==after
    metric('worker-timeout',measurements|{'retry_state':'RETRYABLE','attempts_after_recovery':2,
        'actual_wait_and_reclaim_ms':elapsed,'one_failure_audit':True,'one_evaluation_report_allocation_set':True,
        'canonical_version_unchanged':True,'real_scheduler_backoff':True,
        'harness':'Actual committed lease fed at claim/finalization boundary; real DB timeout and worker retry/reclaim.'})
