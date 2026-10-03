"""Immutable-manifest planning, temporal/group splits and a fail-closed data gate."""
from collections import Counter
from decimal import Decimal
import hashlib
from app.risk.features import instant

TAXONOMY='adjudication-p5-v1'
LABELS=('CLEAN_CONFIRMED','DUPLICATE_CONFIRMED','POLICY_EXCEPTION',
        'DOCUMENT_CORRECTION_ONLY','DISTINCT_CONFIRMED','INSUFFICIENT_INFORMATION')
TARGET={'CLEAN_CONFIRMED':0,'DISTINCT_CONFIRMED':0,'DUPLICATE_CONFIRMED':1,'POLICY_EXCEPTION':1}
GATE_VERSION='representative-label-gate-v1'


def sampled(evaluation_id,seed,rate):
    rate=Decimal(rate)
    if not rate.is_finite() or not 0<rate<=1:raise ValueError('Audit sampling rate must be in (0,1].')
    value=int.from_bytes(hashlib.sha256((seed+':'+str(evaluation_id)).encode()).digest(),'big')
    return Decimal(value)/Decimal(2**256)<rate


def temporal_split(rows,train_end,validation_end,test_end,heldout_parties=()):
    bounds=[instant(t) for t in (train_end,validation_end,test_end)]
    if not bounds[0]<bounds[1]<bounds[2]:raise ValueError('Frozen split boundaries must be strictly chronological.')
    parent={r['transaction_id']:r['transaction_id'] for r in rows}
    def root(key):
        parent.setdefault(key,key)
        if parent[key]!=key:parent[key]=root(parent[key])
        return parent[key]
    def join(a,b):
        a=root(a);b=root(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    owners={}
    for row in rows:
        for key in row.get('group_keys',[]):
            if key in owners:join(row['transaction_id'],owners[key])
            else:owners[key]=row['transaction_id']
        for peer in row.get('related_transaction_ids',[]):
            if peer in parent:join(row['transaction_id'],peer)
    folds={}
    for row in rows:
        at=instant(row['cutoff'])
        fold=next((name for name,bound in zip(('TRAIN','VALIDATION','TEST'),bounds) if at<bound),'OUTSIDE_FREEZE')
        folds.setdefault(root(row['transaction_id']),set()).add(fold)
    included=[];excluded=[];heldout=set(heldout_parties)
    for row in rows:
        group=root(row['transaction_id']);places=folds[group]
        reason=None;fold=next(iter(places))
        if len(places)>1:reason='GROUP_SPANS_TEMPORAL_SPLITS'
        elif fold=='OUTSIDE_FREEZE':reason='OUTSIDE_FREEZE'
        elif row.get('quality')!='FINAL':reason='PROVISIONAL_ADJUDICATION'
        elif row['label'] not in TARGET:reason='NON_BINARY_TAXONOMY'
        elif row.get('party_id') in heldout:
            if fold!='TEST':reason='HELD_OUT_PARTY_EARLIER_PERIOD'
            else:fold='UNSEEN_VENDOR' if row['branch']=='VENDOR_INVOICE' else 'UNSEEN_EMPLOYEE'
        item=row|{'group_id':hashlib.sha256(group.encode()).hexdigest(),'split':fold,
                  'target':TARGET.get(row['label'])}
        if reason:excluded.append(item|{'exclusion':reason})
        else:included.append(item)
    return {'included':included,'excluded':excluded,'boundaries':{
        'train_end':bounds[0].isoformat(),'validation_end':bounds[1].isoformat(),'test_end':bounds[2].isoformat()},
        'split_counts':dict(Counter(r['split'] for r in included)),
        'exclusion_counts':dict(Counter(r['exclusion'] for r in excluded))}


def supervised_gate(rows):
    """Development gate defaults, not sponsor policy or proof of generalization."""
    valid=[r for r in rows if r.get('quality')=='FINAL' and r.get('label') in TARGET]
    real=[r for r in valid if r.get('data_origin')=='AUTHORIZED_REPRESENTATIVE']
    positive=sum(TARGET[r['label']]==1 for r in real);negative=len(real)-positive
    dates=[instant(r['cutoff']) for r in real]
    span=(max(dates)-min(dates)).days if dates else 0
    vendors={r['party_id'] for r in real if r['branch']=='VENDOR_INVOICE'}
    employees={r['party_id'] for r in real if r['branch']=='EMPLOYEE_EXPENSE'}
    reasons=[]
    if not real:reasons.append('REPRESENTATIVE_AUTHORIZED_ADJUDICATIONS_REQUIRED')
    if len(real)<500:reasons.append('FEWER_THAN_500_REPRESENTATIVE_FINAL_LABELS')
    if positive<50 or negative<100:reasons.append('MATERIAL_EXCEPTION_CLASS_COVERAGE_INADEQUATE')
    if len(vendors)<10 or len(employees)<10:reasons.append('BOTH_BRANCH_PARTY_DIVERSITY_INADEQUATE')
    if span<90:reasons.append('FEWER_THAN_90_DAYS')
    if len({r.get('document_quality','UNKNOWN') for r in real})<2:reasons.append('DOCUMENT_QUALITY_DIVERSITY_UNPROVEN')
    for fold in ('TRAIN','VALIDATION','TEST'):
        subset=[r for r in real if r.get('split')==fold]
        if not subset or len({TARGET[r['label']] for r in subset})<2:reasons.append(f'{fold}_CLASS_COVERAGE_INADEQUATE')
    return {'version':GATE_VERSION,'status':'SUPERVISED_TRAINING_NOT_JUSTIFIED' if reasons else 'SUPERVISED_TRAINING_SUPPORTED',
        'reasons':reasons,'counts':{'final_binary_labels':len(valid),'representative_labels':len(real),
            'positive':positive,'negative':negative,'vendors':len(vendors),'employees':len(employees),'span_days':span},
        'target':'Confirmed material exception or material human intervention; never engine routing',
        'limitation':'Synthetic rows and deterministic routing are pipeline tests, not generalization evidence.'}
