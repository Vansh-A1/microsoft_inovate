"""Real PostgreSQL sidecar, governance, leakage, outages and immutable decision tests."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import UUID,uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select,func,text
from sqlalchemy.exc import DBAPIError
from app.core.serialization import utcnow,digest
from app.core.errors import DomainError
from app.core.identity import Identity
from app.db.models import TransactionVersion,Transaction,Evaluation,ReviewCase,AuditEvent,ReferenceRecord
from app.db.risk_models import *
from app.services import intelligence as ml,finance,reviews,operations
from app.integrations.storage import LocalStorage
from test_vertical_slice import payload,headers,evaluate_case
from phase1 import seed

def fresh_seed(client,db,ctx,name):
    row=seed(db,ctx,[name])[0]
    report=evaluate_case(client,db,ctx,row['id'])
    return row|{'latest_evaluation_id':report['evaluation_id'],'decision':report['decision']}

def setup(environment):
    db,ctx,other,client,cfg=environment;author=replace(ctx,roles=ctx.roles|{'ML_ADMIN'})
    gov=Identity(ctx.tenant_id,ctx.legal_entity_id,uuid4(),frozenset({'ML_GOVERNANCE'}),'Separate synthetic ML governor')
    for token,identity in [('test-ml-author',author),('test-ml-gov',gov)]:
        client.app.state.settings.identities[token]={'tenant_id':str(identity.tenant_id),'legal_entity_id':str(identity.legal_entity_id),'actor_id':str(identity.actor_id),'roles':list(identity.roles),'label':identity.label}
    return db,ctx,other,client,cfg,author,gov

def dataset(db,author):
    now=utcnow()
    with db.session(author) as s:return ml.create_dataset(s,author,{'train_end':(now-timedelta(days=60)).isoformat(),
        'validation_end':(now-timedelta(days=30)).isoformat(),'test_end':now.isoformat(),'reason':'Freeze a synthetic development manifest'},'dataset')

def candidate(db,author,gov):
    data=dataset(db,author)
    with db.session(author) as s:built=ml.build_candidate(s,author,UUID(data['id']),'Register transparent statistical baseline','candidate')
    mid=UUID(built['model_id'])
    with db.session(author) as s:ml.transition(s,author,mid,{'expected_version':1,'state':'EVALUATED','reason':'Measure actual pipeline diagnostics'},'evaluate')
    with db.session(gov) as s:ml.transition(s,gov,mid,{'expected_version':2,'state':'APPROVED','reason':'Approve synthetic development shadow observation'},'approve')
    return mid

def deploy(db,gov,mode,model=None,expected=0):
    with db.session(gov) as s:return ml.deploy(s,gov,{'expected_version':expected,'mode':mode,'model_id':str(model) if model else None,
        'threshold':'60.0','reason':'Explicit governed development routing configuration'},'deployment')

def historical(db,ctx,base=None,amount='1000',count=5):
    p=base or payload()
    for i in range(count):
        prior=p|{'invoice_number':'PRIOR-'+uuid4().hex,'total_amount':amount,'invoice_date':'2026-09-01'}
        if p['branch']=='EMPLOYEE_EXPENSE':prior=p|{'claim_number':'PRIOR-'+uuid4().hex,'requested_amount':amount,'expense_date':'2026-09-01'}
        with db.session(ctx) as s:finance.create_transaction(s,ctx,prior,'Submitted synthetic historical fact','history')

def test_rules_only_pins_features_no_score_and_no_future_feedback_leak(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);historical(db,ctx)
    created=fresh_seed(client,db,ctx,'vendor/clean');eid=UUID(created['latest_evaluation_id'])
    response=client.get(f'/api/v1/evaluations/{eid}/intelligence');assert response.status_code==200,response.text
    data=response.json();assert data['intelligence']['status']=='NOT_CONFIGURED' and data['intelligence']['score'] is None
    f=data['features'];assert f['values']['history_count']==5 and f['values']['vendor_amount_ratio']==23.6
    assert str(created['id']) not in [r['object_id'] for r in f['history_manifest']]
    before=digest(f);historical(db,ctx,amount='900000')
    assert digest(client.get(f'/api/v1/evaluations/{eid}/intelligence').json()['features'])==before
    replay=client.post(f'/api/v1/evaluations/{eid}/replay',headers=headers());assert replay.status_code==200 and replay.json()['matches']
    with db.session(other) as s:assert s.scalars(select(FeatureSnapshot)).all()==[]
    assert client.get(f'/api/v1/evaluations/{eid}/intelligence',headers={'Authorization':'Bearer test-second'}).status_code==404

def test_shadow_activation_escalation_rollback_and_replay(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);historical(db,ctx);mid=candidate(db,author,gov)
    with pytest.raises(DomainError) as err:deploy(db,gov,'RULES_PLUS_ANOMALY',mid)
    assert err.value.code=='SHADOW_EVIDENCE_REQUIRED'
    shadow=deploy(db,gov,'SHADOW',mid);created=fresh_seed(client,db,ctx,'vendor/clean');old=client.get('/api/v1/evaluations/'+created['latest_evaluation_id']).json()
    assert old['decision']=='PASS' and old['intelligence']['score']>=60 and old['evaluation_mode']=='SHADOW'
    active=deploy(db,gov,'RULES_PLUS_ANOMALY',mid,1)
    current=client.get('/api/v1/transactions/'+created['id']).json();assert not current['eligible'] and current['eligibility']['eligibility_reason']=='RISK_CONFIGURATION_CHANGED'
    report=evaluate_case(client,db,ctx,created['id']);assert report['decision']=='REVIEW' and report['intelligence']['review_reason']=='ANOMALY_ESCALATION'
    assert all(r['decision_effect']=='NONE' for r in report['rules'])
    assert 'ANOMALY_ESCALATION' in report['reason_codes']
    assert client.post('/api/v1/evaluations/'+report['evaluation_id']+'/replay',headers=headers()).json()['matches']
    with db.session(gov) as s:rolled=ml.rollback(s,gov,{'expected_version':2,'target_id':shadow['id'],'reason':'Return to previous shadow configuration'},'rollback')
    assert rolled['mode']=='SHADOW' and rolled['version']==3
    assert client.get('/api/v1/evaluations/'+old['evaluation_id']).json()['decision']=='PASS'
    assert client.get('/api/v1/evaluations/'+report['evaluation_id']).json()['decision']=='REVIEW'
    deploy(db,gov,'RULES_ONLY',expected=3);final=evaluate_case(client,db,ctx,created['id'])
    assert final['decision']=='PASS' and final['intelligence']['score'] is None and final['model_status']=='NOT_CONFIGURED'

def test_required_model_outage_never_becomes_zero_risk(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);deploy(db,gov,'RULES_PLUS_MODEL')
    created=fresh_seed(client,db,ctx,'vendor/clean');r=client.get('/api/v1/evaluations/'+created['latest_evaluation_id']).json()
    assert r['decision']=='REVIEW' and not r['eligible'] and r['model_status']=='MODEL_UNAVAILABLE'
    assert r['intelligence']['score'] is None and r['intelligence']['review_reason']=='MODEL_UNAVAILABLE'
    assert client.post('/api/v1/evaluations/'+r['evaluation_id']+'/replay',headers=headers()).json()['matches']

def test_missing_active_artifact_is_visible_and_preserves_hold(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);historical(db,ctx);mid=candidate(db,author,gov);deploy(db,gov,'SHADOW',mid)
    passed=fresh_seed(client,db,ctx,'vendor/clean');deploy(db,gov,'RULES_PLUS_ANOMALY',mid,1)
    with db.session(author) as s:model=finance.get(s,ModelVersion,author,mid);path=LocalStorage(client.app.state.settings.storage_root).path(author,model.artifact_key)
    retained=path.read_bytes();path.unlink()
    try:
        assert client.get('/api/v1/intelligence/status').json()['status']=='MODEL_UNAVAILABLE'
        r=evaluate_case(client,db,ctx,passed['id']);assert r['decision']=='REVIEW' and r['intelligence']['score'] is None and r['intelligence']['status']=='MODEL_UNAVAILABLE'
        held=fresh_seed(client,db,ctx,'vendor/paid_duplicate');assert held['decision']=='HOLD'
        assert client.post('/api/v1/evaluations/'+passed['latest_evaluation_id']+'/replay',headers=headers()).status_code==409
    finally:path.write_bytes(retained)

def test_actual_low_anomaly_cannot_clear_mandatory_hold(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);p=payload('vendor/paid_duplicate');historical(db,ctx,p,amount=p['total_amount'])
    mid=candidate(db,author,gov);deploy(db,gov,'SHADOW',mid)
    held=fresh_seed(client,db,ctx,'vendor/paid_duplicate');r=client.get('/api/v1/evaluations/'+held['latest_evaluation_id']).json()
    assert r['intelligence']['status']=='AVAILABLE' and r['intelligence']['score']==0 and r['decision']=='HOLD'
    deploy(db,gov,'RULES_PLUS_ANOMALY',mid,1);r=evaluate_case(client,db,ctx,held['id'])
    assert r['decision']=='HOLD' and r['intelligence']['review_reason'] is None

def test_feedback_pass_sampling_manifest_and_no_online_learning(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);record=fresh_seed(client,db,ctx,'vendor/clean');now=utcnow()
    data={'start':(now-timedelta(days=1)).isoformat(),'end':now.isoformat(),'campaign':'development-audit','rate':'1','reason':'Audit a synthetic PASS without assigning a label'}
    with db.session(author) as s:a=ml.sample_pass(s,author,data,'sample')
    with db.session(author) as s:b=ml.sample_pass(s,author,data,'sample-repeat')
    assert a==b and a['selected']==1
    rid=UUID(a['review_case_ids'][0]);r=client.get('/api/v1/reviews/'+str(rid)).json()
    command={'expected_review_version':r['review_version'],'expected_transaction_version':1,'reason_code':'AUDIT_PASS','comment':'Inspect synthetic retained sources and controls'}
    assigned=client.post('/api/v1/reviews/'+str(rid)+'/assign',json=command|{'action':'CLAIM'},headers=headers());assert assigned.status_code==200,assigned.text
    command['expected_review_version']=assigned.json()['review_version']
    resolved=client.post('/api/v1/reviews/'+str(rid)+'/actions',json=command|{'action':'RESOLVE_EXCEPTION'},headers=headers());assert resolved.status_code==200,resolved.text
    command['expected_review_version']=resolved.json()['review']['review_version']
    ev=client.get('/api/v1/evaluations/'+record['latest_evaluation_id']).json();evidence=ev['rules'][0]['evidence'][0]['id']
    label=client.post('/api/v1/reviews/'+str(rid)+'/feedback',json=command|{'label':'CLEAN_CONFIRMED','evidence_ids':[evidence]},headers=headers());assert label.status_code==201,label.text
    assert label.json()['label']['quality']=='FINAL'
    stale=client.post('/api/v1/reviews/'+str(rid)+'/feedback',json=command|{'label':'POLICY_EXCEPTION','evidence_ids':[evidence]},headers=headers());assert stale.status_code==409
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(ModelVersion))==0
    manifest=dataset(db,author);assert manifest['manifest']['gate']['status']=='SUPERVISED_TRAINING_NOT_JUSTIFIED'
    assert manifest['manifest']['split']['split_counts']=={'TEST':1}
    with db.session(author) as s:deferred=ml.build_candidate(s,author,UUID(manifest['id']),'Do not train on synthetic labels','defer',True)
    assert deferred['state']=='SUPERVISED_DEFERRED' and deferred['model_id'] is None

def test_governance_roles_forged_actor_self_approval_and_conflicts(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);d=dataset(db,author)
    with db.session(author) as s:made=ml.build_candidate(s,author,UUID(d['id']),'Create a synthetic candidate','candidate')
    mid=UUID(made['model_id'])
    assert client.get('/api/v1/intelligence/registry').status_code==403
    assert client.post('/api/v1/intelligence/training-runs',json={'dataset_id':d['id'],'reason':'Unauthorized training candidate'},headers=headers()).status_code==403
    assert client.post('/api/v1/intelligence/deployments',json={'expected_version':0,'mode':'RULES_ONLY','reason':'Unauthorized mode change'},headers=headers()).status_code==403
    response=client.post('/api/v1/intelligence/deployments',json={'expected_version':0,'mode':'RULES_ONLY','reason':'Forged author attempt','actor_id':str(gov.actor_id)},headers=headers()|{'Authorization':'Bearer test-ml-gov'});assert response.status_code==422
    with db.session(author) as s:ml.transition(s,author,mid,{'expected_version':1,'state':'EVALUATED','reason':'Validate actual artifact'},'evaluated')
    selfgov=replace(author,roles=author.roles|{'ML_GOVERNANCE'})
    with pytest.raises(DomainError) as err:
        with db.session(selfgov) as s:ml.transition(s,selfgov,mid,{'expected_version':2,'state':'APPROVED','reason':'Cannot approve own candidate'},'self')
    assert err.value.status==403
    with pytest.raises(DomainError) as err:
        with db.session(gov) as s:ml.transition(s,gov,mid,{'expected_version':1,'state':'APPROVED','reason':'Stale version approval attempt'},'stale')
    assert err.value.status==409
    with pytest.raises(DomainError):
        with db.session(other) as s:finance.get(s,ModelVersion,other,mid)
    with db.session(ctx) as s:
        assert s.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace=current_schema()::regnamespace AND relkind='r' AND relrowsecurity AND relforcerowsecurity"))==61
    with pytest.raises(DBAPIError):
        with db.session(author) as s:s.execute(text('UPDATE risk_models SET version=\'tampered\' WHERE id=:id'),{'id':mid})

def test_history_registration_is_observed_not_backdated_and_idempotent(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment)
    with db.session(author) as s:refs=s.scalars(select(ReferenceRecord).where(ReferenceRecord.kind=='historical_transactions')).all();pins=[{'id':str(r.id),'version':r.version} for r in refs]
    before=utcnow()
    with db.session(author) as s:a=ml.register_history(s,author,pins,'Observe available synthetic reference history','register')
    with db.session(author) as s:b=ml.register_history(s,author,pins,'Idempotent repeated source observation','register-again');sources=s.scalars(select(RiskHistorySource)).all()
    assert a['created']==len(pins) and b['created']==0 and all(r.created_at>=before for r in sources)
    assert all('status' not in r.facts for r in sources)
    assert client.post('/api/v1/intelligence/history',json={'records':pins,'reason':'Attempt to assign future outcome knowledge','known_at':'2020-01-01T00:00:00Z'},headers=headers()|{'Authorization':'Bearer test-ml-author'}).status_code==422

def test_monitoring_is_measured_idempotent_no_auto_retraining(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);historical(db,ctx);fresh_seed(client,db,ctx,'vendor/clean');now=utcnow()
    request={'start':(now-timedelta(days=1)).isoformat(),'end':now.isoformat(),'reason':'Record observed synthetic feature distributions'}
    with db.session(author) as s:a=ml.monitor(s,author,request,'monitor')
    with db.session(author) as s:b=ml.monitor(s,author,request,'monitor-repeat')
    assert a==b and a['content']['count']==1 and a['content']['features']['vendor_amount_ratio']['observed']==1
    assert a['content']['supervised_performance'] is None and a['content']['final_delayed_labels']==0
    with db.session(author) as s:assert s.scalar(select(func.count()).select_from(TrainingRun))==0

def test_cutoff_query_selects_temporal_version_before_currency_and_party_filter(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);historical(db,ctx)
    with db.session(ctx) as s:
        prior=s.scalar(select(TransactionVersion).order_by(TransactionVersion.created_at));t=s.get(Transaction,prior.transaction_id)
        current=finance.create_transaction(s,ctx,payload()|{'invoice_number':'PIT-CURRENT'},'Canonical current submission','current')
    cutoff=utcnow()
    with db.session(ctx) as s:
        t=finance.get(s,Transaction,ctx,prior.transaction_id)
        changed=prior.payload|{'currency':'USD','vendor_id':str(uuid4())}
        finance.revise(s,ctx,t.id,{'expected_version':1,'reason':'Future correction must not change past cohort','transaction':changed},'future')
    with db.session(ctx) as s:
        v=s.scalar(select(TransactionVersion).where(TransactionVersion.transaction_id==UUID(current['id']),TransactionVersion.version==1))
        rows,complete=ml.history(s,ctx,v,cutoff)
    assert complete and any(r['object_id']==str(prior.transaction_id) and r['version']==1 for r in rows)

def test_audit_failure_rolls_back_intelligence_and_evaluation(environment,monkeypatch):
    db,ctx,other,client,cfg,author,gov=setup(environment)
    real=finance.audit
    def fail(s,ctx,action,*args,**kw):
        if action=='INTELLIGENCE_SNAPSHOT_RECORDED':raise DomainError(503,'AUDIT_UNAVAILABLE','Required intelligence audit unavailable')
        return real(s,ctx,action,*args,**kw)
    monkeypatch.setattr(finance,'audit',fail)
    assert seed(db,ctx,['vendor/clean'])[0]['processing_state']=='FAILED_FINAL'
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(FeatureSnapshot))==0
        assert s.scalar(select(func.count()).select_from(RiskScore))==0
        assert s.scalar(select(func.count()).select_from(Evaluation))==0


@pytest.mark.parametrize('case',['employee/clean_taxi','employee/hotel_two_nights'])
def test_actual_employee_anomaly_and_pinned_policy_unit(environment,case):
    db,ctx,other,client,cfg,author,gov=setup(environment);p=payload(case);historical(db,ctx,p,amount='100')
    mid=candidate(db,author,gov);deploy(db,gov,'SHADOW',mid);record=fresh_seed(client,db,ctx,case)
    r=client.get('/api/v1/evaluations/'+record['latest_evaluation_id']).json();assert r['decision']=='PASS' and r['intelligence']['status']=='AVAILABLE'
    f=client.get('/api/v1/evaluations/'+record['latest_evaluation_id']+'/intelligence').json()['features']
    assert f['values']['employee_category_ratio']==float(Decimal(p['requested_amount'])/Decimal('100'))
    # The taxi allowance is EMPLOYEE_LOCAL_DAY; a per-claim denominator would
    # misrepresent the policy. Its unsupported aggregate remains explicitly absent.
    assert f['values']['vendor_amount_ratio'] is None
    if case.endswith('clean_taxi'):
        assert f['values']['policy_limit_ratio'] is None and f['missing']['policy_limit_ratio']
    else:assert f['values']['policy_limit_ratio'] is not None
    deploy(db,gov,'RULES_PLUS_ANOMALY',mid,1);r=evaluate_case(client,db,ctx,record['id'])
    assert r['decision']=='REVIEW' and r['intelligence']['review_reason']=='ANOMALY_ESCALATION'
    assert client.post('/api/v1/evaluations/'+r['evaluation_id']+'/replay',headers=headers()).json()['matches']


def test_cutoff_budget_balance_ignores_future_cancellation_release(environment):
    from test_finance_phase3 import configured,create,trusted_source,approve,drain,report
    from app.services import finance_ledger
    from app.services.reference_imports import active_records
    db,ctx,other,client,cfg=configured(environment);p=trusted_source(db,ctx,payload()|{'invoice_number':'PIT-LEDGER-'+uuid4().hex})
    tid=create(client,p);approve(client,tid);drain(db,ctx);assert report(client,tid)['decision']=='PASS'
    cutoff=utcnow()
    with db.session(ctx) as s:budget=active_records(s,ctx)[p['budget_id']].payload;before=finance_ledger.balance(s,ctx,budget,cutoff=cutoff)
    with db.session(ctx) as s:reviews.cancel(s,ctx,UUID(tid),1,'A future cancellation cannot alter a past feature snapshot','future-cancel')
    with db.session(ctx) as s:
        past=finance_ledger.balance(s,ctx,budget,cutoff=cutoff);current=finance_ledger.balance(s,ctx,budget)
    assert past==before and Decimal(current['available'])>=Decimal(past['available'])
    from app.db.finance_models import AllocationEvent
    with db.session(ctx) as s:assert s.scalar(select(func.count()).select_from(AllocationEvent).where(AllocationEvent.action=='RELEASED'))>0


def test_concurrent_governance_write_has_one_deployment(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment);barrier=Barrier(2)
    def run(mode):
        barrier.wait()
        try:deploy(db,gov,mode);return 201
        except DomainError as error:return error.status
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(run,['RULES_ONLY','RULES_PLUS_MODEL']))
    assert sorted(results)==[201,409]
    with db.session(gov) as s:assert s.scalar(select(func.count()).select_from(RiskDeployment))==1


def test_malformed_risk_controls_return_validation_errors(environment):
    db,ctx,other,client,cfg,author,gov=setup(environment)
    for threshold in ('NaN','Infinity','abc','0','-1','101'):
        r=client.post('/api/v1/intelligence/deployments',json={'expected_version':0,'mode':'RULES_ONLY','threshold':threshold,'reason':'Reject malformed configuration'},headers=headers()|{'Authorization':'Bearer test-ml-gov'});assert r.status_code==422,r.text
    for value in ('no-date','2026-01-01T00:00:00'):
        r=client.post('/api/v1/intelligence/monitoring',json={'start':value,'end':value,'reason':'Reject ambiguous cutoff'},headers=headers()|{'Authorization':'Bearer test-ml-author'});assert r.status_code==422,r.text
    r=client.post('/api/v1/intelligence/pass-samples',json={'start':utcnow().isoformat(),'end':utcnow().isoformat(),'campaign':'safe','rate':'abc','reason':'Reject malformed sampling'},headers=headers()|{'Authorization':'Bearer test-ml-author'});assert r.status_code==422,r.text
