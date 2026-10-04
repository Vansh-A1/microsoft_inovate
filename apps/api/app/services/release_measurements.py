"""Bounded, scoped observations of retained work; no SLA or inferred success."""
from datetime import timedelta
from statistics import median
from sqlalchemy import select,func
from app.core.serialization import utcnow,projection
from app.db.session import scope_query
from app.db.document_models import ExtractionRun,DocumentJob
from app.db.models import Job,AuditEvent,RuleResultRow
from app.services.operations import read_permission

LIMIT=500

def summary(values):
    ordered=sorted(values)
    return {'samples':len(ordered),'median_ms':round(median(ordered),3) if ordered else None,
        'maximum_ms':round(max(ordered),3) if ordered else None}

def measurements(session,identity):
    read_permission(identity);now=utcnow();cutoff=now-timedelta(days=7)
    runs=session.scalars(scope_query(select(ExtractionRun),ExtractionRun,identity).where(ExtractionRun.started_at>=cutoff).order_by(ExtractionRun.started_at.desc()).limit(LIMIT)).all()
    extraction={};provider_calls={}
    for run in runs:
        provider=run.metadata_json.get('provider_id','UNKNOWN')
        if provider not in ('ENTERPRISE_VLM','NATIVE_TEXT','LOCAL_OCR','FIXTURE'):provider='UNKNOWN'
        extraction.setdefault(provider,[]).append(max(0,(run.completed_at-run.started_at).total_seconds()*1000))
        # Only typed timing numbers are exposed. Source text, identifiers, provider
        # output and error messages never enter this operational projection.
        side=run.metadata_json.get('routing',{}).get('enterprise',{})
        for kind,key in [('header','header_seconds'),('rows','line_seconds'),('inventory','row_inventory_seconds')]:
            elapsed=side.get(key)
            if isinstance(elapsed,(int,float)) and 0<=elapsed<=180:
                provider_calls.setdefault(kind,[]).append(elapsed*1000)
    events=session.scalars(scope_query(select(AuditEvent),AuditEvent,identity).where(AuditEvent.created_at>=cutoff,AuditEvent.action.in_(['DOCUMENT_STAGE_CLAIMED','DOCUMENT_STAGE_COMPLETED'])).order_by(AuditEvent.sequence.desc()).limit(LIMIT*4)).all()
    claims={};stages={}
    for event in reversed(events):
        stage=event.payload.get('stage');key=(event.object_id,stage)
        if stage not in ('PREPROCESS','EXTRACT','NORMALIZE','VALIDATE','FINALIZE'):continue
        if event.action=='DOCUMENT_STAGE_CLAIMED':claims[key]=event.created_at
        elif key in claims:
            elapsed=(event.created_at-claims.pop(key)).total_seconds()*1000
            if elapsed>=0:stages.setdefault(stage,[]).append(elapsed)
    queues={}
    for model,label in [(Job,'finance'),(DocumentJob,'document')]:
        oldest=session.scalar(scope_query(select(func.min(model.created_at)),model,identity).where(model.state.in_(['QUEUED','RETRYABLE'])))
        queues[label]={'oldest_wait_seconds':max(0,(now-oldest).total_seconds()) if oldest else None,
            'states':dict(session.execute(scope_query(select(model.state,func.count()).group_by(model.state),model,identity)).all())}
    findings=dict(session.execute(scope_query(select(RuleResultRow.rule_id,func.count()).group_by(RuleResultRow.rule_id),RuleResultRow,identity).where(RuleResultRow.created_at>=cutoff,RuleResultRow.status.in_(['ERROR','UNKNOWN','FAIL']),RuleResultRow.rule_id.in_(['REF-001','BUD-001','GRN-001','EXP-005','SYS-001']))).all())
    return projection({'measured_at':now,'window_start':cutoff,'maximum_run_samples':LIMIT,
        'extraction':{k:summary(v) for k,v in extraction.items()},'provider_calls':{k:summary(v) for k,v in provider_calls.items()},
        'document_stage_commit_elapsed':{k:summary(v) for k,v in stages.items()},'queues':queues,
        'findings_requiring_attention':findings,'audit_failures':{'count':None,'signal':'audit_write_failed structured log; failed writes roll back, so no retained DB count'},
        'interpretation':'Recent retained samples; stage timings include commit overhead. Development observations, not production SLA.'})
