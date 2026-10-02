"""Durable database worker. Expiring leases, bounded retries, atomic finalization."""
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import select, or_, and_
from app.core.serialization import utcnow
from app.core.identity import Identity
from app.db.models import Job, OutboxEvent, Transaction
from app.db.session import scope_query
from app.services.finance import get, finalize, audit


def claim(database,identity,now=None):
    now=now or utcnow()
    with database.session(identity) as session:
        q=scope_query(select(Job),Job,identity).where(or_(and_(Job.state.in_(['QUEUED','RETRYABLE']),Job.available_at<=now),and_(Job.state=='RUNNING',Job.lease_until<=now))).order_by(Job.created_at).with_for_update(skip_locked=True).limit(1)
        job=session.scalar(q)
        if not job:return None
        if job.attempts>=job.maximum_attempts:
            job.state='FAILED';job.last_error='ATTEMPTS_EXHAUSTED';job.lease_until=None;job.updated_at=now
            transaction=get(session,Transaction,identity,job.transaction_id)
            if transaction.latest_version==job.transaction_version and transaction.processing_state=='QUEUED':transaction.processing_state='FAILED';transaction.eligible=False
            audit(session,identity,'JOB_FAILED',job.id,1,'Maximum execution attempts exhausted',str(job.id));return None
        job.state='RUNNING';job.attempts+=1;job.lease_owner=uuid4();job.lease_until=now+timedelta(seconds=60);job.updated_at=now
        for event in session.scalars(scope_query(select(OutboxEvent),OutboxEvent,identity).where(OutboxEvent.job_id==job.id,OutboxEvent.delivered_at.is_(None))):event.delivered_at=now
        audit(session,identity,'JOB_CLAIMED',job.id,1,'Durable execution lease acquired',str(job.id),{'attempt':job.attempts})
        return job.id,job.lease_owner,job.actor_id


def run_once(database,identity):
    leased=claim(database,identity)
    if not leased:return False
    job_id,owner,actor=leased
    execution_identity=Identity(identity.tenant_id,identity.legal_entity_id,actor,identity.roles,identity.label)
    try:
        with database.session(execution_identity) as session:finalize(session,execution_identity,job_id,owner)
    except Exception:
        # Never persist provider/driver text, SQL, credentials or uploaded values as errors.
        with database.session(execution_identity) as session:
            job=get(session,Job,execution_identity,job_id)
            if job.state=='RUNNING' and job.lease_owner==owner:
                job.state='FAILED' if job.attempts>=job.maximum_attempts else 'RETRYABLE';job.last_error='EXECUTION_FAILED';job.lease_until=None;job.available_at=utcnow()+timedelta(seconds=2**job.attempts);job.updated_at=utcnow()
                transaction=get(session,Transaction,execution_identity,job.transaction_id)
                if job.state=='FAILED' and transaction.latest_version==job.transaction_version:transaction.processing_state='FAILED';transaction.eligible=False
                audit(session,execution_identity,'JOB_RETRY_SCHEDULED' if job.state=='RETRYABLE' else 'JOB_FAILED',job.id,1,'Execution rolled back; safe failure recorded',str(job.id))
    return True


def main():
    import argparse,time
    from app.core.config import Settings
    from app.core.identity import authenticate
    from app.db.session import Database
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    settings=Settings.load();database=Database(settings.database_url)
    identities={}
    for token in settings.identities:
        identity=authenticate(token,settings);identities[(identity.tenant_id,identity.legal_entity_id)]=identity
    while True:
        for identity in identities.values():run_once(database,identity)
        if args.once:break
        time.sleep(.5)


if __name__=='__main__':main()
