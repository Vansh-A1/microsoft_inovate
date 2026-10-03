"""Durable database worker. Expiring leases, bounded retries, atomic finalization."""
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import select, or_, and_
from app.core.serialization import utcnow
from app.core.identity import Identity
from app.domain.states import ProcessingState
from app.rules.engine import RULESET
from app.db.models import Job, OutboxEvent, Transaction
from app.db.session import scope_query
from app.services.finance import get, finalize, audit, scope_lock


def _claim_once(database,identity,now=None):
    now=now or utcnow()
    with database.session(identity) as session:
        scope_lock(session,identity)
        q=scope_query(select(Job),Job,identity).where(Job.stage=='EVALUATE',Job.stage_version.in_([RULESET,'rules-p3-v1']),or_(and_(Job.state.in_(['QUEUED','RETRYABLE']),Job.available_at<=now),and_(Job.state=='RUNNING',Job.lease_until<=now))).order_by(Job.created_at).with_for_update(skip_locked=True).limit(1)
        job=session.scalar(q)
        if not job:return None
        if job.attempts>=job.maximum_attempts:
            from app.services.operations import mark_failure
            mark_failure(job,'ATTEMPTS_EXHAUSTED',True,now)
            transaction=get(session,Transaction,identity,job.transaction_id)
            if transaction.latest_version==job.transaction_version and transaction.row_version==job.generation:transaction.processing_state=ProcessingState.FAILED_FINAL.value;transaction.eligible=False
            audit(session,identity,'JOB_FAILED',job.id,1,'Maximum execution attempts exhausted',str(job.id));return (None,None,None)
        job.state='RUNNING';job.attempts+=1;job.lease_owner=uuid4();job.lease_until=now+timedelta(seconds=60);job.updated_at=now
        transaction=get(session,Transaction,identity,job.transaction_id)
        if transaction.latest_version==job.transaction_version and transaction.row_version==job.generation:transaction.processing_state=ProcessingState.PROCESSING.value
        for event in session.scalars(scope_query(select(OutboxEvent),OutboxEvent,identity).where(OutboxEvent.job_id==job.id,OutboxEvent.delivered_at.is_(None))):event.delivered_at=now
        audit(session,identity,'JOB_CLAIMED',job.id,1,'Durable execution lease acquired',str(job.id),{'attempt':job.attempts})
        return job.id,job.lease_owner,job.actor_id


def claim(database,identity,now=None):
    from sqlalchemy.exc import DBAPIError
    import time
    for attempt in range(3):
        try:return _claim_once(database,identity,now)
        except DBAPIError as exc:
            if getattr(exc.orig,'sqlstate',None) not in ('40P01','40001'):raise
            if attempt==2:return None
            time.sleep(.05*(2**attempt))
    return None


def run_once(database,identity):
    leased=claim(database,identity)
    if not leased:return False
    job_id,owner,actor=leased
    if job_id is None:return True
    execution_identity=Identity(identity.tenant_id,identity.legal_entity_id,actor,identity.roles,identity.label)
    try:
        with database.session(execution_identity) as session:finalize(session,execution_identity,job_id,owner)
    except Exception as exc:
        # Never persist provider/driver text, SQL, credentials or uploaded values as errors.
        with database.session(execution_identity) as session:
            scope_lock(session,execution_identity)
            job=get(session,Job,execution_identity,job_id)
            if job.state=='RUNNING' and job.lease_owner==owner:
                from app.services.operations import classify_failure,mark_failure
                code,retryable=classify_failure(exc)
                mark_failure(job,code,retryable,utcnow())
                transaction=get(session,Transaction,execution_identity,job.transaction_id)
                if transaction.latest_version==job.transaction_version and transaction.row_version==job.generation:
                    transaction.processing_state=ProcessingState.FAILED_FINAL.value if job.state=='FAILED' else ProcessingState.FAILED_RETRYABLE.value;transaction.eligible=False
                audit(session,execution_identity,'JOB_RETRY_SCHEDULED' if job.state=='RETRYABLE' else 'JOB_FAILED',job.id,1,'Execution rolled back; safe failure recorded',str(job.id))
    return True


def worker_identities(settings):
    from app.core.identity import authenticate
    identities={}
    if not settings.development:
        from app.core.identity import Identity
        from uuid import UUID
        for r in settings.worker_scopes:
            if set(r['roles'])!={'SERVICE_WORKER','FINANCE_REVIEWER'}:raise ValueError('Use only scoped worker capabilities.')
            ctx=Identity(UUID(r['tenant_id']),UUID(r['legal_entity_id']),UUID(r['actor_id']),frozenset(r['roles']),'Scoped enterprise worker')
            identities[(ctx.tenant_id,ctx.legal_entity_id)]=ctx
        if not identities:raise ValueError('Approved worker scopes are required.')
        return identities
    for token in settings.identities:
        identity=authenticate(token,settings)
        if 'FINANCE_REVIEWER' in identity.roles:identities.setdefault((identity.tenant_id,identity.legal_entity_id),identity)
    if not identities:raise ValueError('Configure an explicit scoped finance worker identity.')
    return identities


def main():
    import argparse,time
    from app.core.config import Settings
    from app.core.identity import authenticate
    from app.db.session import Database
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    settings=Settings.load();database=Database(settings.database_url);database.settings=settings
    from app.integrations.blob_storage import configured_storage
    from app.services.document_worker import run_once as run_document_once
    storage=configured_storage(settings)
    identities=worker_identities(settings)
    while True:
        for identity in identities.values():
            run_once(database,identity)
            run_document_once(database,identity,storage,settings)
        if args.once:break
        time.sleep(.5)


if __name__=='__main__':main()
