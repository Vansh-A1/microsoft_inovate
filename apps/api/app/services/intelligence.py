"""Governed intelligence sidecar over existing transactions and immutable evaluations."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import UUID,uuid4
from zoneinfo import ZoneInfo
import hashlib
import json
import statistics
import sys
from pathlib import Path
from sqlalchemy import select,func
from app.core.errors import DomainError
from app.core.serialization import projection,digest,utcnow,canonical_json
from app.db.models import (Transaction,TransactionVersion,Evaluation,ReviewCase,ReferenceRecord,
    ReferenceSnapshot,LegalEntity,EvidenceObject)
from app.db.risk_models import (FeatureSchema,RiskHistorySource,FeatureSnapshot,FeedbackLabel,AuditSample,
    DatasetVersion,TrainingRun,ModelVersion,ModelEvent,RiskDeployment,RiskScore,MonitoringSnapshot)
from app.db.session import scope_query
from app.db.workflow_models import ReviewAction
from app.integrations.blob_storage import configured_storage
from app.risk import features,anomaly,datasets
from app.services import finance,reviews

MAX_ROWS=10000
READ_ROLES={'FINANCE_REVIEWER','AUDITOR','ML_ADMIN','ML_GOVERNANCE'}

def require(ctx,roles):
    if not set(roles)&ctx.roles:raise DomainError(403,'FORBIDDEN','Authorized intelligence access is required.')

def query(s,ctx,model):return scope_query(select(model),model,ctx)
def service_code_version():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def feature_schema(s,ctx):
    row=s.scalar(query(s,ctx,FeatureSchema).where(FeatureSchema.version==features.VERSION))
    if row:
        if row.content_digest!=digest(features.schema()):raise DomainError(409,'FEATURE_SCHEMA_CHANGED','Create a new schema version for changed feature definitions.')
        return row
    row=FeatureSchema(**ctx.scope(),version=features.VERSION,content=features.schema(),content_digest=digest(features.schema()))
    s.add(row);s.flush();return row

def deployment(s,ctx):return s.scalar(query(s,ctx,RiskDeployment).order_by(RiskDeployment.version.desc()).limit(1))

def state(s,ctx,model):return s.scalar(query(s,ctx,ModelEvent).where(ModelEvent.model_id==model.id).order_by(ModelEvent.version.desc()).limit(1))

def storage(s):
    settings=s.info.get('settings')
    if not settings:raise DomainError(503,'MODEL_STORAGE_UNAVAILABLE','Private model artifact storage is not configured.')
    return configured_storage(settings)

def register_history(s,ctx,records,reason,correlation):
    require(ctx,{'ML_ADMIN'});finance.scope_lock(s,ctx);created=[]
    for pin in records:
        rid=UUID(pin['id']);version=pin['version']
        prior=s.scalar(query(s,ctx,RiskHistorySource).where(RiskHistorySource.reference_id==rid,RiskHistorySource.reference_version==version))
        if prior:continue
        r=s.scalar(query(s,ctx,ReferenceRecord).where(ReferenceRecord.id==rid,ReferenceRecord.version==version))
        if not r or r.kind!='historical_transactions':raise DomainError(422,'HISTORY_SOURCE_INVALID','Use scoped historical transaction references.')
        if r.payload.get('import_batch_id'):
            from app.db.finance_models import ReferenceActivation
            if not s.scalar(query(s,ctx,ReferenceActivation).where(ReferenceActivation.record_id==rid,ReferenceActivation.record_version==version)):
                raise DomainError(409,'HISTORY_NOT_ACTIVATED','Activate reference data before registering its knowledge time.')
        p=r.payload
        facts={k:p.get(k) for k in ('branch','vendor_id','employee_id','category','invoice_number','claim_number','invoice_date','expense_date','currency','total_amount','requested_amount','claimed_amount')}
        # Availability is observed now. A printed business date is never a knowledge timestamp.
        row=RiskHistorySource(**ctx.scope(),reference_id=rid,reference_version=version,object_id=rid,facts=facts,source_digest=digest(p))
        s.add(row);s.flush();created.append(str(row.id))
    finance.audit(s,ctx,'RISK_HISTORY_REGISTERED',ctx.legal_entity_id,1,reason,correlation,{'source_ids':created,'knowledge_time_policy':'SERVER_OBSERVED_NO_BACKDATING'})
    return {'created':len(created),'source_ids':created,'knowledge_time_policy':'SERVER_OBSERVED_NO_BACKDATING'}

def history(s,ctx,version,cutoff):
    """Pick the latest *known* version first. Never join current lifecycle projections."""
    ranked=scope_query(select(TransactionVersion.id,func.row_number().over(partition_by=TransactionVersion.transaction_id,
        order_by=TransactionVersion.version.desc()).label('rank')),TransactionVersion,ctx).where(
        TransactionVersion.created_at<cutoff,TransactionVersion.transaction_id!=version.transaction_id).subquery()
    p=version.payload;vendor=p['branch']=='VENDOR_INVOICE'
    if not p.get('vendor_id' if vendor else 'employee_id') or not p.get('currency'):return [],False
    q=query(s,ctx,TransactionVersion).join(ranked,ranked.c.id==TransactionVersion.id).where(ranked.c.rank==1,
        TransactionVersion.currency==p.get('currency'),TransactionVersion.party_id==UUID(p['vendor_id' if vendor else 'employee_id']))
    rows=s.scalars(q.order_by(TransactionVersion.created_at,TransactionVersion.id).limit(MAX_ROWS+1)).all()
    result=[{'object_id':str(r.transaction_id),'version':r.version,'known_at':r.created_at.isoformat(),'facts':r.payload,'source_kind':'CANONICAL'} for r in rows]
    refs=s.scalars(query(s,ctx,RiskHistorySource).where(RiskHistorySource.created_at<cutoff).order_by(RiskHistorySource.created_at,RiskHistorySource.id).limit(MAX_ROWS+1)).all()
    result += [{'object_id':str(r.object_id),'version':r.reference_version,'known_at':r.created_at.isoformat(),'facts':r.facts,'source_kind':'OBSERVED_REFERENCE'} for r in refs]
    return result,len(rows)<=MAX_ROWS and len(refs)<=MAX_ROWS

def operands(s,ctx,version,job,context,deterministic):
    """Use only immutable reference facts pinned before the inference cutoff.

    Live ledger, acceptance and duplicate aggregates may change during execution;
    those are explicitly absent until a complete cutoff snapshot proves their basis.
    """
    from app.services.references import pinned
    snap=finance.get(s,ReferenceSnapshot,ctx,job.snapshot_id)
    if snap.created_at>job.evaluated_at:return {}
    refs=pinned(s,ctx,snap.id);p=version.payload;vendor=p['branch']=='VENDOR_INVOICE'
    basis={'known_at':snap.created_at.isoformat(),'currency':p.get('currency'),'lineage':{'snapshot_id':str(snap.id),'reference_manifest_digest':snap.content_digest}}
    if vendor:
        master=refs.get(p.get('vendor_id'))
        if master:
            onboarding=master.get('onboarded_date')
            if onboarding:basis['approved_onboarding_date']=onboarding
            account=master.get('payment_account_token')
            if account and p.get('payment_account_token'):basis['payment_account_changed']=account!=p['payment_account_token']
        expected=Decimal('0');difference=Decimal('0');complete=bool(p.get('lines'))
        for line in p.get('lines',[]):
            master=refs.get(line.get('po_line_id')) or refs.get(line.get('contract_line_id'))
            if not master or master.get('currency',p['currency'])!=p['currency'] or master.get('uom')!=line.get('uom'):
                complete=False;break
            price=features.decimal(master.get('unit_price'));actual=features.decimal(line.get('unit_price'));qty=features.decimal(line.get('quantity'))
            if price is None or actual is None or qty is None:complete=False;break
            expected+=price*qty;difference+=abs(actual-price)*qty
        if complete:basis.update(expected_line_amount=str(expected),price_difference_amount=str(difference))
    else:
        policy=refs.get(p.get('expense_policy_id'))
        if policy and policy.get('currency')==p.get('currency'):
            allowance=policy.get('allowance_amount',policy.get('limit_amount'))
            unit=policy.get('unit');unit_amount=p.get('requested_amount') if unit=='PER_CLAIM' else None
            if unit=='ELIGIBLE_NIGHT' and p.get('items'):
                amounts=[]
                for item in p['items']:
                    nights=features.decimal(item.get('eligible_nights'));claimed=features.decimal(item.get('claimed_amount'))
                    if not nights or nights<=0 or claimed is None or item.get('currency')!=p['currency']:amounts=[];break
                    amounts.append(claimed/nights)
                if amounts:unit_amount=str(max(amounts))
            if features.decimal(allowance) is not None and unit_amount is not None:basis.update(policy_unit=unit,policy_allowance_amount=allowance,policy_unit_amount=unit_amount)
    if context.get('finance_v3'):
        from app.services import finance_ledger
        budget=refs.get(p.get('budget_id'));amount=features.decimal(p.get('total_amount' if vendor else 'requested_amount'))
        if budget and amount is not None and budget.get('currency')==p.get('currency'):
            balance=finance_ledger.balance(s,ctx,budget,exclude=version.transaction_id,po_id=p.get('po_id'),cutoff=job.evaluated_at)
            available=Decimal(balance['available']);allocated=Decimal(balance['allocation'])+Decimal(balance['adjustments'])
            incremental=max(Decimal('0'),amount-Decimal(balance['po_commitment_coverage']))
            basis.update(budget_allocated_amount=str(allocated),budget_post_exposure_amount=str(allocated-available+incremental))
            basis['lineage']['budget_cutoff_ledger_event_ids']=balance['ledger_event_ids']
        # Existing matching arithmetic is reusable only when all of its operands
        # were available at cutoff and no later lifecycle event changed its basis.
        from app.db.finance_models import FinanceAllocation,AllocationEvent
        pins={(r['id'],r['version']) for r in context.get('references',{}).values()}
        known={(r['id'],r['version']) for r in refs.values()}
        live=s.scalars(query(s,ctx,FinanceAllocation).limit(MAX_ROWS+1)).all()
        ids=[a.id for a in live]
        late=any(a.created_at>=job.evaluated_at for a in live) or (bool(ids) and s.scalar(query(s,ctx,AllocationEvent).where(AllocationEvent.allocation_id.in_(ids),AllocationEvent.created_at>=job.evaluated_at).limit(1)) is not None)
        if len(live)<=MAX_ROWS and pins<=known and not late:
            observed={r.rule_id:r.observed for r in deterministic.results}
            po=observed.get('PO-004',{})
            if isinstance(po,dict) and features.decimal(po.get('remaining_value')) is not None:basis['po_remaining_amount']=po['remaining_value']
            grn=observed.get('GRN-001')
            if isinstance(grn,list) and grn and all(features.decimal(r.get('quantity_shortfall')) is not None for r in grn):
                # Aggregate only quantities with a comparable commercial UOM.
                units={refs.get(r.get('commercial_line_id'),{}).get('uom') for r in grn}
                if len(units)==1 and None not in units:basis['receipt_shortfall']=str(sum((Decimal(r['quantity_shortfall']) for r in grn),Decimal('0')))
    from app.db.document_models import TransactionDocument,DocumentDraft,Observation
    documents=s.scalars(query(s,ctx,TransactionDocument).where(TransactionDocument.transaction_id==version.transaction_id,
        TransactionDocument.transaction_version==version.version,TransactionDocument.created_at<job.evaluated_at)).all()
    states=[];observation_ids=[]
    for document in documents:
        draft=s.scalar(query(s,ctx,DocumentDraft).where(DocumentDraft.id==document.draft_id,DocumentDraft.created_at<job.evaluated_at)) if document.draft_id else None
        if not draft:continue
        observations=s.scalars(query(s,ctx,Observation).where(Observation.extraction_run_id==draft.extraction_run_id,Observation.created_at<job.evaluated_at)).all()
        critical={'total_amount','currency','invoice_date','vendor_name'} if vendor else {'total_amount','currency','expense_date','merchant_name'}
        for o in observations:
            if o.field_path in critical:states.append(o.state);observation_ids.append(str(o.id))
    if states:
        basis['quality_and_freshness']=sum(state in ('MISSING','ILLEGIBLE','AMBIGUOUS') for state in states)/len(states)
        basis['lineage']['source_observation_ids']=observation_ids
    from app.db.finance_models import ImageFingerprint
    source_ids={UUID(did) for did in [p.get('source_document_id'),*[i.get('source_document_id') for i in p.get('items',[])]] if did}
    if source_ids:
        own=s.scalars(query(s,ctx,ImageFingerprint).where(ImageFingerprint.document_id.in_(source_ids),ImageFingerprint.created_at<job.evaluated_at).limit(101)).all()
        other=s.scalars(query(s,ctx,ImageFingerprint).where(ImageFingerprint.document_id.not_in(source_ids),ImageFingerprint.created_at<job.evaluated_at).order_by(ImageFingerprint.created_at,ImageFingerprint.id).limit(MAX_ROWS+1)).all()
        if own and other and len(own)<=100 and len(other)<=MAX_ROWS:
            closest=min(((int(a.hash_bits,16)^int(b.hash_bits,16)).bit_count(),str(a.id),str(b.id)) for a in own for b in other)
            basis['min_phash_distance']=closest[0]
            basis['lineage']['phash']={'source_fingerprint_id':closest[1],'candidate_fingerprint_id':closest[2],
                'scope':'PRIOR_SCOPED_DOCUMENT_FINGERPRINTS','definition':'64-bit Hamming distance; fingerprint candidate signal, never proof of duplication'}
    return basis

def prepare(s,ctx,job,version,context,deterministic):
    rows,coverage=history(s,ctx,version,job.evaluated_at)
    t=finance.get(s,Transaction,ctx,version.transaction_id)
    entity=s.scalar(select(LegalEntity).where(LegalEntity.id==ctx.legal_entity_id,LegalEntity.tenant_id==ctx.tenant_id))
    basis=operands(s,ctx,version,job,context,deterministic)
    f=features.build(version.payload,version.transaction_id,version.version,job.evaluated_at,job.snapshot_id,rows,
        operands=basis,submitted_date=t.created_at.astimezone(ZoneInfo(entity.timezone)).date().isoformat(),coverage=coverage)
    f['feature_service_code_version']=service_code_version()
    f['input_availability']='AVAILABLE_AT_CUTOFF' if version.created_at<job.evaluated_at else 'BACKDATED_SYNTHETIC_INPUT'
    if f['input_availability']!='AVAILABLE_AT_CUTOFF':
        # Historical golden fixtures deliberately pin a business evaluation time.
        # They remain valid rules-only tests, but cannot supply historical ML facts.
        f['values']={name:None for name in f['feature_names']}
        f['missing']={name:True for name in f['feature_names']}
        f['missing_reasons']={name:'CURRENT_VERSION_NOT_KNOWN_AT_CUTOFF' for name in f['feature_names']}
        f['cold_start']=True;f['lineage']={}
    configured=deployment(s,ctx);mode=configured.mode if configured else 'RULES_ONLY';model=None
    result={'status':'NOT_CONFIGURED','score':None,'score_kind':None,'factors':[],'explanation_status':'NOT_CONFIGURED','shap_status':'NOT_APPLICABLE'}
    if mode!='RULES_ONLY':
        result={'status':'MODEL_UNAVAILABLE','score':None,'score_kind':None,'factors':[],'explanation_status':'UNAVAILABLE','shap_status':'NOT_APPLICABLE'}
        if configured.model_id:
            model=finance.get(s,ModelVersion,ctx,configured.model_id)
            try:
                artifact=load_artifact(s,ctx,model)
                if mode=='RULES_PLUS_MODEL':raise ValueError('Supervised model not supported by the data gate.')
                result=anomaly.score(f)
                result.update(model_version=model.version,artifact_sha256=model.artifact_sha256,artifact_algorithm=artifact['algorithm'])
            except (OSError,ValueError,DomainError):result['diagnostic']='PINNED_ARTIFACT_OR_SCHEMA_UNAVAILABLE'
    threshold=configured.threshold if configured else anomaly.DEFAULT_THRESHOLD
    combined,reason=anomaly.combine(deterministic.decision,mode,result,threshold)
    intelligence=projection(result|{'mode':mode,'model_id':model.id if model else None,'deployment_id':configured.id if configured else None,
        'deployment_version':configured.version if configured else None,'feature_schema':features.VERSION,'feature_digest':digest(f),
        'threshold':threshold,'deterministic_decision':deterministic.decision,'combined_decision':combined,'review_reason':reason,
        'data_scope':'SYNTHETIC_DEVELOPMENT','supervised_status':'DEFERRED_REPRESENTATIVE_ADJUDICATED_LABELS_REQUIRED'})
    return replace(deterministic,decision=combined,eligible=deterministic.eligible and combined=='PASS'),f,intelligence,configured,model

def persist(s,ctx,evaluation,f,intelligence,configured,model):
    schema=feature_schema(s,ctx)
    snapshot=FeatureSnapshot(**ctx.scope(),evaluation_id=evaluation.id,schema_id=schema.id,content=f,content_digest=digest(f))
    s.add(snapshot);s.flush()
    row=RiskScore(**ctx.scope(),evaluation_id=evaluation.id,feature_snapshot_id=snapshot.id,
        deployment_id=configured.id if configured else None,model_id=model.id if model else None,content=intelligence,content_digest=digest(intelligence))
    s.add(row);s.flush()
    finance.audit(s,ctx,'INTELLIGENCE_SNAPSHOT_RECORDED',evaluation.transaction_id,evaluation.transaction_version,
        'Pinned cutoff-safe business features and separate intelligence result',str(evaluation.id),
        {'evaluation_id':str(evaluation.id),'feature_snapshot_id':str(snapshot.id),'risk_score_id':str(row.id),'mode':intelligence['mode'],'status':intelligence['status']})

def inspect(s,ctx,evaluation_id):
    require(ctx,READ_ROLES);finance.get(s,Evaluation,ctx,evaluation_id)
    row=s.scalar(query(s,ctx,RiskScore).where(RiskScore.evaluation_id==evaluation_id))
    labels=s.scalars(query(s,ctx,FeedbackLabel).where(FeedbackLabel.evaluation_id==evaluation_id).order_by(FeedbackLabel.created_at)).all()
    f=finance.get(s,FeatureSnapshot,ctx,row.feature_snapshot_id) if row else None
    return {'intelligence':row.content if row else {'mode':'RULES_ONLY','status':'NOT_CONFIGURED','score':None},
        'features':f.content if f else None,'labels':[label_view(r) for r in labels]}

def label_view(r):return projection({'id':r.id,'label':r.label,'quality':r.quality,'taxonomy':r.taxonomy,
    'actor_id':r.actor_id,'created_at':r.created_at,'reason':r.reason,'evidence':r.evidence,'supersedes_id':r.supersedes_id})

def feedback(s,ctx,review_id,data,correlation):
    row,t=reviews.guard(s,ctx,review_id,data)
    if row.owner_id!=ctx.actor_id:raise DomainError(403,'CASE_NOT_OWNED','Claim this case before recording adjudication.')
    if data['label'] not in datasets.LABELS:raise DomainError(422,'LABEL_INVALID','Use the versioned adjudication taxonomy.')
    prior=s.scalar(query(s,ctx,FeedbackLabel).where(FeedbackLabel.evaluation_id==row.evaluation_id).order_by(FeedbackLabel.created_at.desc(),FeedbackLabel.id.desc()).limit(1))
    if (str(prior.id) if prior else None)!=data.get('expected_label_id'):raise DomainError(409,'LABEL_VERSION_CONFLICT','Refresh the latest adjudication before superseding it.')
    if not data.get('evidence_ids'):raise DomainError(422,'LABEL_EVIDENCE_REQUIRED','Cite retained evidence for adjudication.')
    for eid in data['evidence_ids']:
        e=finance.get(s,EvidenceObject,ctx,UUID(eid))
        if e.evaluation_id!=row.evaluation_id:raise DomainError(409,'LABEL_EVIDENCE_STALE','Use evidence from this pinned evaluation.')
    quality='FINAL' if row.state in ('RESOLVED','CANCELLED') else 'PROVISIONAL'
    reviews.record(s,ctx,row,t,'ADJUDICATE',data,correlation,{'label':data['label'],'quality':quality,'taxonomy':datasets.TAXONOMY})
    action=s.scalar(query(s,ctx,ReviewAction).where(ReviewAction.review_case_id==row.id,ReviewAction.review_version==row.row_version))
    label=FeedbackLabel(**ctx.scope(),evaluation_id=row.evaluation_id,review_case_id=row.id,review_action_id=action.id,
        actor_id=ctx.actor_id,taxonomy=datasets.TAXONOMY,label=data['label'],quality=quality,reason=data['comment'],evidence=data['evidence_ids'],supersedes_id=prior.id if prior else None)
    s.add(label);s.flush();finance.audit(s,ctx,'FEEDBACK_LABEL_CREATED',t.id,t.latest_version,data['comment'],correlation,{'label_id':str(label.id),'taxonomy':label.taxonomy,'quality':quality,'evaluation_id':str(row.evaluation_id)})
    return {'label':label_view(label),'review':reviews.view(s,ctx,row)}

def sample_pass(s,ctx,data,correlation):
    require(ctx,{'ML_ADMIN'});finance.scope_lock(s,ctx)
    start,end=features.instant(data['start']),features.instant(data['end'])
    if start>=end:raise DomainError(422,'SAMPLING_WINDOW_INVALID','Use an increasing bounded sampling period.')
    rows=s.scalars(query(s,ctx,Evaluation).where(Evaluation.decision=='PASS',Evaluation.evaluated_at>=start,Evaluation.evaluated_at<end)
        .order_by(Evaluation.evaluated_at,Evaluation.id).limit(MAX_ROWS+1)).all()
    if len(rows)>MAX_ROWS:raise DomainError(422,'SAMPLING_WINDOW_TOO_LARGE','Narrow the frozen period to at most 10000 evaluations.')
    selected=[]
    for e in rows:
        if not datasets.sampled(e.id,data['campaign'],data['rate']):continue
        prior=s.scalar(query(s,ctx,AuditSample).where(AuditSample.evaluation_id==e.id))
        if prior:selected.append(str(prior.review_case_id));continue
        t=finance.get(s,Transaction,ctx,e.transaction_id)
        # Audit the retained evaluation without changing historical/current eligibility.
        review=ReviewCase(**ctx.scope(),transaction_id=t.id,evaluation_id=e.id,decision='PASS',branch=t.branch,
            state='OPEN' if t.latest_version==e.transaction_version else 'SUPERSEDED',reasons=['PASS_AUDIT'])
        s.add(review);s.flush();s.add(AuditSample(**ctx.scope(),evaluation_id=e.id,review_case_id=review.id,campaign=data['campaign'],rate=data['rate'],actor_id=ctx.actor_id))
        selected.append(str(review.id));finance.audit(s,ctx,'PASS_AUDIT_SAMPLED',t.id,e.transaction_version,data['reason'],correlation,{'evaluation_id':str(e.id),'review_case_id':str(review.id),'campaign':data['campaign'],'rate':data['rate']})
    return {'eligible_evaluations':len(rows),'selected':len(selected),'review_case_ids':selected,'method':'SHA256_CAMPAIGN_AND_EVALUATION','pass_is_not_a_label':True}

def create_dataset(s,ctx,data,correlation):
    require(ctx,{'ML_ADMIN'});finance.scope_lock(s,ctx);schema=feature_schema(s,ctx);frozen=utcnow()
    labels=s.scalars(query(s,ctx,FeedbackLabel).where(FeedbackLabel.created_at<=frozen).order_by(FeedbackLabel.created_at,FeedbackLabel.id).limit(MAX_ROWS+1)).all()
    if len(labels)>MAX_ROWS:raise DomainError(422,'DATASET_SCOPE_TOO_LARGE','Narrow dataset scope before creating a manifest.')
    latest={r.evaluation_id:r for r in labels};rows=[];excluded=[]
    from app.db.document_models import TransactionDocument,DocumentVersion
    from app.db.finance_models import DuplicateComparison
    for eid,label in latest.items():
        e=finance.get(s,Evaluation,ctx,eid);v=s.scalar(query(s,ctx,TransactionVersion).where(TransactionVersion.transaction_id==e.transaction_id,TransactionVersion.version==e.transaction_version))
        f=s.scalar(query(s,ctx,FeatureSnapshot).where(FeatureSnapshot.evaluation_id==eid,FeatureSnapshot.schema_id==schema.id))
        if not f:excluded.append({'evaluation_id':str(eid),'reason':'FEATURE_SNAPSHOT_UNAVAILABLE'});continue
        docs=s.scalars(query(s,ctx,TransactionDocument).where(TransactionDocument.transaction_id==e.transaction_id,TransactionDocument.transaction_version==e.transaction_version)).all()
        groups=['document:'+str(d.document_id) for d in docs]
        groups+=['source:'+str(value) for value in [v.payload.get('source_document_id'),*[i.get('source_document_id') for i in v.payload.get('items',[])]] if value]
        for d in docs:
            dv=s.scalar(query(s,ctx,DocumentVersion).where(DocumentVersion.id==d.document_id,DocumentVersion.version==d.document_version))
            if dv:groups.append('original:'+dv.sha256)
        comparisons=s.scalars(query(s,ctx,DuplicateComparison).where(DuplicateComparison.transaction_id==e.transaction_id)).all()
        peers=[]
        for comparison in comparisons:
            peer=str(comparison.candidate_id) if comparison.candidate_type=='TRANSACTION' else None
            if peer:peers.append(peer)
        p=v.payload;vendor=p['branch']=='VENDOR_INVOICE'
        rows.append({'transaction_id':str(e.transaction_id),'transaction_version':e.transaction_version,'evaluation_id':str(eid),
            'label_id':str(label.id),'label':label.label,'quality':label.quality,'taxonomy':label.taxonomy,'cutoff':e.evaluated_at.isoformat(),
            'branch':p['branch'],'party_id':p.get('vendor_id' if vendor else 'employee_id'),'group_keys':groups,'related_transaction_ids':peers,
            'feature_snapshot_id':str(f.id),'feature_digest':f.content_digest,'data_origin':'SYNTHETIC_DEVELOPMENT',
            'document_quality':'SOURCE_UNKNOWN' if f.content['values']['quality_and_freshness'] is None else 'MEASURED'})
    try:split=datasets.temporal_split(rows,data['train_end'],data['validation_end'],data['test_end'],data.get('heldout_parties',[]))
    except ValueError as error:raise DomainError(422,'DATASET_SPLIT_INVALID',str(error)) from None
    if features.instant(data['test_end'])>frozen:raise DomainError(422,'DATASET_FUTURE_FREEZE','Final test boundary must already be frozen.')
    manifest={'schema_version':'dataset-p5-v1','taxonomy':datasets.TAXONOMY,'feature_schema':features.VERSION,'feature_schema_digest':schema.content_digest,
        'cutoff_rule':'Each immutable feature snapshot uses only facts known strictly before its evaluation cutoff.',
        'split':split,'unavailable_features':excluded,'gate':datasets.supervised_gate(split['included']),
        'source_data_version':digest(rows),'data_origin':'SYNTHETIC_DEVELOPMENT','target':datasets.supervised_gate(split['included'])['target'],
        'filters':{'scope':'SERVER_AUTHORIZED_TENANT_ENTITY','maximum_rows':MAX_ROWS},'reason':data['reason']}
    hashed=digest(manifest);prior=s.scalar(query(s,ctx,DatasetVersion).where(DatasetVersion.content_digest==hashed))
    if prior:return dataset_view(prior)
    row=DatasetVersion(**ctx.scope(),schema_id=schema.id,manifest=manifest,content_digest=hashed,actor_id=ctx.actor_id)
    s.add(row);s.flush();finance.audit(s,ctx,'DATASET_VERSION_CREATED',row.id,1,data['reason'],correlation,{'dataset_digest':hashed,'gate':manifest['gate']['status'],'included':len(split['included'])})
    return dataset_view(row)

def dataset_view(row):return projection({'id':row.id,'created_at':row.created_at,'digest':row.content_digest,'manifest':row.manifest})

def build_candidate(s,ctx,dataset_id,reason,correlation,supervised=False):
    require(ctx,{'ML_ADMIN'});finance.scope_lock(s,ctx);dataset=finance.get(s,DatasetVersion,ctx,dataset_id)
    metadata={'dataset_digest':dataset.content_digest,'feature_schema':features.VERSION,'feature_code_version':features.code_version(),
        'training_code_version':service_code_version(),'random_seed':0,
        'dependencies':{'python':sys.version.split()[0],'statistics':'PYTHON_STDLIB'},'configuration':{'minimum_cohort':features.MINIMUM_COHORT,'algorithm':anomaly.ALGORITHM},
        'gate':dataset.manifest['gate'],'metrics':None,'metric_status':'NO_SUPERVISED_MODEL_OR_GENERALIZATION_METRICS'}
    if supervised:
        run=TrainingRun(**ctx.scope(),dataset_id=dataset.id,schema_id=dataset.schema_id,actor_id=ctx.actor_id,state='SUPERVISED_DEFERRED',metadata_record=metadata)
        s.add(run);s.flush();finance.audit(s,ctx,'SUPERVISED_TRAINING_DEFERRED',run.id,1,reason,correlation,{'dataset_id':str(dataset.id),'gate':dataset.manifest['gate']['status']})
        return {'training_run_id':str(run.id),'state':run.state,'gate':dataset.manifest['gate'],'model_id':None}
    run=TrainingRun(**ctx.scope(),dataset_id=dataset.id,schema_id=dataset.schema_id,actor_id=ctx.actor_id,state='BASELINE_BUILT',metadata_record=metadata)
    s.add(run);s.flush();artifact={'schema':'statistical-artifact-p5-v1','algorithm':anomaly.ALGORITHM,'version':anomaly.VERSION,
        'feature_schema':features.VERSION,'feature_schema_digest':features.schema() and digest(features.schema()),'feature_code_version':features.code_version(),
        'feature_service_code_version':service_code_version(),
        'anomaly_code_version':hashlib.sha256(__import__('pathlib').Path(anomaly.__file__).read_bytes()).hexdigest(),
        'training_run_id':str(run.id),'dataset_id':str(dataset.id),'training_configuration':metadata['configuration'],
        'model_card':'Transparent development statistical policy; no fitted classifier, probability, calibration, SHAP or production validation.'}
    key,sha=storage(s).put(ctx,canonical_json(artifact).encode())
    model=ModelVersion(**ctx.scope(),algorithm=anomaly.ALGORITHM,version=anomaly.VERSION+'-'+uuid4().hex[:12],schema_id=dataset.schema_id,
        dataset_id=dataset.id,training_run_id=run.id,actor_id=ctx.actor_id,artifact_key=key,artifact_sha256=sha,metadata_record=metadata|{'model_card':artifact['model_card']})
    s.add(model);s.flush();s.add(ModelEvent(**ctx.scope(),model_id=model.id,version=1,state='CANDIDATE',actor_id=ctx.actor_id,reason=reason,details={'training_run_id':str(run.id)}))
    finance.audit(s,ctx,'ANOMALY_CANDIDATE_REGISTERED',model.id,1,reason,correlation,{'artifact_sha256':sha,'dataset_id':str(dataset.id),'training_run_id':str(run.id),'state':'CANDIDATE'})
    return {'model_id':str(model.id),'model_version':model.version,'state':'CANDIDATE','training_run_id':str(run.id),'metrics':None}

def load_artifact(s,ctx,model):
    data=storage(s).get(ctx,model.artifact_key)
    if len(data)>2*1024*1024 or hashlib.sha256(data).hexdigest()!=model.artifact_sha256:raise ValueError('Artifact integrity failed.')
    result=json.loads(data)
    if result.get('schema')!='statistical-artifact-p5-v1' or result.get('algorithm')!=anomaly.ALGORITHM or result.get('version')!=anomaly.VERSION:
        raise ValueError('Unsupported artifact.')
    schema=finance.get(s,FeatureSchema,ctx,model.schema_id)
    if schema.version!=features.VERSION or schema.content_digest!=digest(features.schema()) or result.get('feature_schema_digest')!=schema.content_digest or result.get('feature_code_version')!=features.code_version():raise ValueError('Feature schema/code mismatch.')
    if result.get('feature_service_code_version')!=service_code_version():raise ValueError('Pinned feature service code is unavailable.')
    if result.get('anomaly_code_version')!=hashlib.sha256(__import__('pathlib').Path(anomaly.__file__).read_bytes()).hexdigest():raise ValueError('Pinned scoring code is unavailable.')
    return result

def transition(s,ctx,model_id,data,correlation):
    target=data['state'];require(ctx,{'ML_ADMIN'} if target=='EVALUATED' else {'ML_GOVERNANCE'});finance.scope_lock(s,ctx)
    model=finance.get(s,ModelVersion,ctx,model_id);prior=state(s,ctx,model)
    if prior.version!=data['expected_version']:raise DomainError(409,'MODEL_VERSION_CONFLICT','Refresh the registry before recording this action.')
    if target in ('SHADOW','ACTIVE'):raise DomainError(422,'DEPLOYMENT_REQUIRED','Use an explicit governed deployment to enter shadow or active mode.')
    allowed={'CANDIDATE':{'EVALUATED','REJECTED'},'EVALUATED':{'APPROVED','REJECTED'},'APPROVED':{'RETIRED','REJECTED'},'SHADOW':{'RETIRED'},'ACTIVE':{'RETIRED'}}
    if target not in allowed.get(prior.state,set()):raise DomainError(409,'MODEL_STATE_INVALID','This registry transition is not permitted.')
    if target=='APPROVED' and ctx.actor_id==model.actor_id:raise DomainError(403,'MODEL_SELF_APPROVAL','The candidate author cannot approve their own candidate.')
    if target in ('APPROVED','EVALUATED'):
        try:load_artifact(s,ctx,model)
        except (ValueError,OSError):raise DomainError(409,'MODEL_ARTIFACT_UNAVAILABLE','The private artifact or compatible schema failed verification.') from None
    details={}
    if target=='EVALUATED':
        dataset=finance.get(s,DatasetVersion,ctx,model.dataset_id);count=0;available=0;scores=[]
        for item in dataset.manifest['split']['included']:
            f=finance.get(s,FeatureSnapshot,ctx,UUID(item['feature_snapshot_id']));result=anomaly.score(f.content);count+=1
            if result['score'] is not None:available+=1;scores.append(result['score'])
        details={'dataset_id':str(dataset.id),'data_origin':dataset.manifest['data_origin'],'scored_rows':count,'available_scores':available,
            'score_min':min(scores) if scores else None,'score_max':max(scores) if scores else None,'metrics_kind':'PIPELINE_DIAGNOSTICS_ONLY','generalization_metrics':None}
    current=deployment(s,ctx)
    if target in ('RETIRED','REJECTED') and current and current.model_id==model.id and current.mode!='RULES_ONLY':raise DomainError(409,'MODEL_IN_USE','Rollback or disable the active deployment before retiring its model.')
    event=ModelEvent(**ctx.scope(),model_id=model.id,version=prior.version+1,state=target,actor_id=ctx.actor_id,reason=data['reason'],details=details)
    s.add(event);s.flush();finance.audit(s,ctx,'MODEL_'+target,model.id,event.version,data['reason'],correlation,details)
    return projection({'model_id':model.id,'version':event.version,'state':target,'diagnostics':details})

def deploy(s,ctx,data,correlation):
    require(ctx,{'ML_GOVERNANCE'});finance.scope_lock(s,ctx);prior=deployment(s,ctx)
    if (prior.version if prior else 0)!=data['expected_version']:raise DomainError(409,'DEPLOYMENT_VERSION_CONFLICT','Refresh the deployment before changing it.')
    mode=data['mode'];model=None
    if data.get('model_id'):
        model=finance.get(s,ModelVersion,ctx,UUID(data['model_id']));event=state(s,ctx,model)
        if event.state not in ('APPROVED','SHADOW','ACTIVE'):raise DomainError(409,'MODEL_NOT_APPROVED','An explicitly approved candidate is required.')
        if model.actor_id==ctx.actor_id:raise DomainError(403,'MODEL_SELF_ACTIVATION','The candidate author cannot activate their own candidate.')
        try:load_artifact(s,ctx,model)
        except (ValueError,OSError):raise DomainError(409,'MODEL_ARTIFACT_UNAVAILABLE','Verify the private artifact before deployment.') from None
        if mode=='RULES_PLUS_MODEL':raise DomainError(409,'SUPERVISED_MODEL_DEFERRED','Representative adjudicated labels are required before supervised activation.')
        if mode=='RULES_PLUS_ANOMALY':
            shadows=s.scalars(query(s,ctx,RiskScore).where(RiskScore.model_id==model.id)).all()
            if not any(r.content['mode']=='SHADOW' and r.content['status']=='AVAILABLE' for r in shadows):raise DomainError(409,'SHADOW_EVIDENCE_REQUIRED','Collect an actual available shadow score before activation.')
        if mode!='RULES_ONLY':
            target='SHADOW' if mode=='SHADOW' else 'ACTIVE'
            s.add(ModelEvent(**ctx.scope(),model_id=model.id,version=event.version+1,state=target,actor_id=ctx.actor_id,reason=data['reason'],details={'mode':mode,'development_only':True}))
    if mode in ('SHADOW','RULES_PLUS_ANOMALY') and not model:raise DomainError(422,'MODEL_REQUIRED','Choose an approved statistical artifact.')
    if mode=='RULES_ONLY' and model:raise DomainError(422,'MODE_MODEL_MISMATCH','RULES_ONLY has no configured score.')
    # RULES_PLUS_MODEL without an artifact deliberately represents a required unavailable dependency.
    row=RiskDeployment(**ctx.scope(),version=(prior.version if prior else 0)+1,mode=mode,model_id=model.id if model else None,
        previous_id=prior.id if prior else None,actor_id=ctx.actor_id,threshold=data['threshold'],reason=data['reason'])
    s.add(row);s.flush();finance.audit(s,ctx,'RISK_DEPLOYMENT_CREATED',row.id,row.version,data['reason'],correlation,
        {'mode':mode,'model_id':str(model.id) if model else None,'previous_id':str(prior.id) if prior else None,'requires_reevaluation':True})
    return deployment_view(row)

def deployment_view(row):return projection({'id':row.id,'version':row.version,'mode':row.mode,'model_id':row.model_id,'threshold':row.threshold,'previous_id':row.previous_id,'created_at':row.created_at})

def rollback(s,ctx,data,correlation):
    require(ctx,{'ML_GOVERNANCE'});finance.scope_lock(s,ctx);current=deployment(s,ctx)
    if not current or current.version!=data['expected_version']:raise DomainError(409,'DEPLOYMENT_VERSION_CONFLICT','Refresh before rollback.')
    target=finance.get(s,RiskDeployment,ctx,UUID(data['target_id']))
    if target.version>=current.version:raise DomainError(409,'ROLLBACK_TARGET_INVALID','Choose an earlier retained deployment.')
    result=deploy(s,ctx,{'expected_version':current.version,'mode':target.mode,'model_id':str(target.model_id) if target.model_id else None,
        'threshold':target.threshold,'reason':data['reason']},correlation)
    finance.audit(s,ctx,'RISK_DEPLOYMENT_ROLLED_BACK',UUID(result['id']),result['version'],data['reason'],correlation,{'rollback_target_id':str(target.id)})
    return result

def registry(s,ctx):
    require(ctx,{'ML_ADMIN','ML_GOVERNANCE','AUDITOR'});current=deployment(s,ctx)
    models=s.scalars(query(s,ctx,ModelVersion).order_by(ModelVersion.created_at.desc()).limit(100)).all()
    return {'deployment':deployment_view(current) if current else {'version':0,'mode':'RULES_ONLY','model_id':None},
        'models':[projection({'id':m.id,'version':m.version,'algorithm':m.algorithm,'artifact_sha256':m.artifact_sha256,
            'state':state(s,ctx,m).state,'registry_version':state(s,ctx,m).version,'dataset_id':m.dataset_id,
            'feature_schema':features.VERSION,'metadata':m.metadata_record}) for m in models],
        'datasets':[dataset_view(r) for r in s.scalars(query(s,ctx,DatasetVersion).order_by(DatasetVersion.created_at.desc()).limit(50))],
        'deployments':[deployment_view(r) for r in s.scalars(query(s,ctx,RiskDeployment).order_by(RiskDeployment.version.desc()).limit(50))],
        'supervised_status':'DEFERRED_REPRESENTATIVE_ADJUDICATED_LABELS_REQUIRED','online_learning':False}

def monitor(s,ctx,data,correlation):
    require(ctx,{'ML_ADMIN','ML_GOVERNANCE'});finance.scope_lock(s,ctx);start,end=features.instant(data['start']),features.instant(data['end'])
    if start>=end or end>utcnow():raise DomainError(422,'MONITORING_WINDOW_INVALID','Use an increasing frozen observation period.')
    rows=s.scalars(query(s,ctx,FeatureSnapshot).join(Evaluation,Evaluation.id==FeatureSnapshot.evaluation_id).where(Evaluation.evaluated_at>=start,Evaluation.evaluated_at<end)
        .order_by(FeatureSnapshot.created_at,FeatureSnapshot.id).limit(MAX_ROWS+1)).all()
    if len(rows)>MAX_ROWS:raise DomainError(422,'MONITORING_WINDOW_TOO_LARGE','Narrow this monitoring period.')
    scores=[];parties={'vendor':set(),'employee':set()};categories={};currency_amounts={};overrides=0;labels=0
    for f in rows:
        risk=s.scalar(query(s,ctx,RiskScore).where(RiskScore.evaluation_id==f.evaluation_id))
        if risk and risk.content.get('score') is not None:scores.append(risk.content['score'])
        e=finance.get(s,Evaluation,ctx,f.evaluation_id);v=s.scalar(query(s,ctx,TransactionVersion).where(TransactionVersion.transaction_id==e.transaction_id,TransactionVersion.version==e.transaction_version));p=v.payload;vendor=p['branch']=='VENDOR_INVOICE'
        parties['vendor' if vendor else 'employee'].add(p.get('vendor_id' if vendor else 'employee_id'))
        category=p.get('category','VENDOR');categories[category]=categories.get(category,0)+1
        amount=features.decimal(p.get('total_amount' if vendor else 'requested_amount'))
        if amount is not None:currency_amounts.setdefault(p['currency'],[]).append(amount)
        feedback=s.scalar(query(s,ctx,FeedbackLabel).where(FeedbackLabel.evaluation_id==e.id,FeedbackLabel.quality=='FINAL',FeedbackLabel.created_at<=end).order_by(FeedbackLabel.created_at.desc()).limit(1))
        if feedback:
            labels+=1
            if risk and risk.content.get('review_reason')=='ANOMALY_ESCALATION' and feedback.label in ('CLEAN_CONFIRMED','DISTINCT_CONFIRMED'):overrides+=1
    distributions={}
    for name in features.schema()['order']:
        vals=[r.content['values'][name] for r in rows if r.content['values'][name] is not None]
        numeric=[float(v) for v in vals]
        distributions[name]={'observed':len(vals),'missing':len(rows)-len(vals),'missing_rate':(len(rows)-len(vals))/len(rows) if rows else None,
            'minimum':min(numeric) if numeric else None,'median':statistics.median(numeric) if numeric else None,'maximum':max(numeric) if numeric else None}
    baseline=None;drift=[]
    if data.get('dataset_id'):
        baseline=finance.get(s,DatasetVersion,ctx,UUID(data['dataset_id']))
        baseline_rows=[finance.get(s,FeatureSnapshot,ctx,UUID(i['feature_snapshot_id'])) for i in baseline.manifest['split']['included'] if i['split']=='TRAIN']
        if baseline_rows:
            for name in features.schema()['order']:
                old=sum(r.content['missing'][name] for r in baseline_rows)/len(baseline_rows);new=distributions[name]['missing_rate']
                if new is not None and abs(new-old)>=0.2:drift.append({'feature':name,'kind':'MISSINGNESS_CHANGE','baseline':old,'current':new,'absolute_difference':abs(new-old)})
    content=projection({'schema_version':'monitoring-p5-v1','window':{'start':start,'end':end},'feature_schema':features.VERSION,
        'snapshot_manifest':[{'id':r.id,'digest':r.content_digest} for r in rows],'count':len(rows),'features':distributions,
        'amount_by_currency':{c:{'count':len(a),'minimum':str(min(a)),'median':str(statistics.median(a)),'maximum':str(max(a))} for c,a in currency_amounts.items()},
        'party_mix':{k:len(v) for k,v in parties.items()},'category_mix':categories,'score_distribution':{'count':len(scores),'min':min(scores) if scores else None,'median':statistics.median(scores) if scores else None,'max':max(scores) if scores else None},
        'cold_start_rate':sum(r.content['cold_start'] for r in rows)/len(rows) if rows else None,'final_delayed_labels':labels,
        'clean_adjudicated_anomaly_escalations':overrides,'adjudication_coverage':labels/len(rows) if rows else None,'supervised_performance':None,
        'drift':drift,'action':'EVALUATION_REQUESTED' if drift else 'NO_AUTOMATIC_ACTION','threshold_policy':'Development diagnostic: absolute missingness shift >= 0.20; no automatic retraining.',
        'baseline_dataset_id':baseline.id if baseline else None,'baseline_status':'AVAILABLE' if baseline and baseline_rows else 'NOT_CONFIGURED_OR_EMPTY'})
    hashed=digest(content);prior=s.scalar(query(s,ctx,MonitoringSnapshot).where(MonitoringSnapshot.content_digest==hashed))
    if prior:return {'id':str(prior.id),'content':prior.content}
    row=MonitoringSnapshot(**ctx.scope(),dataset_id=baseline.id if baseline else None,actor_id=ctx.actor_id,content=content,content_digest=hashed)
    s.add(row);s.flush();finance.audit(s,ctx,'RISK_MONITORING_RECORDED',row.id,1,data['reason'],correlation,{'count':len(rows),'drift_signals':len(drift)})
    return {'id':str(row.id),'content':content}

def replay(s,ctx,evaluation,deterministic):
    row=s.scalar(query(s,ctx,RiskScore).where(RiskScore.evaluation_id==evaluation.id))
    if not row:return deterministic
    f=finance.get(s,FeatureSnapshot,ctx,row.feature_snapshot_id)
    if digest(f.content)!=f.content_digest or digest(row.content)!=row.content_digest or row.content['feature_digest']!=f.content_digest:
        raise DomainError(409,'REPLAY_INTELLIGENCE_INTEGRITY','Retained features or intelligence digest failed verification.')
    result=row.content
    if result['mode']!='RULES_ONLY' and result.get('status') not in ('MODEL_UNAVAILABLE',):
        if not row.model_id:raise DomainError(409,'REPLAY_MODEL_UNAVAILABLE','The retained model is unavailable.')
        model=finance.get(s,ModelVersion,ctx,row.model_id)
        try:load_artifact(s,ctx,model)
        except (ValueError,OSError):raise DomainError(409,'REPLAY_MODEL_UNAVAILABLE','The retained compatible artifact is unavailable.') from None
        computed=anomaly.score(f.content)
        if computed['status']!=result['status'] or computed['score']!=result['score']:raise DomainError(409,'REPLAY_SCORE_MISMATCH','The retained scoring output was not reproduced.')
    combined,reason=anomaly.combine(deterministic.decision,result['mode'],result,result['threshold'])
    if reason!=result['review_reason']:raise DomainError(409,'REPLAY_COMBINER_MISMATCH','The retained intelligence disposition was not reproduced.')
    return replace(deterministic,decision=combined,eligible=deterministic.eligible and combined=='PASS')
