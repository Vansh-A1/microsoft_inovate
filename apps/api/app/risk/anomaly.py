"""Transparent statistical signals, never a calibrated exception probability."""
from decimal import Decimal
import math

ALGORITHM='ROBUST_STATISTICAL'
VERSION='anomaly-p5-v1'
DEFAULT_THRESHOLD='60.0'


def score(features):
    values=features['values'];factors=[]
    if features['history_coverage']!='COMPLETE':return {'status':'HISTORY_INCOMPLETE','score':None,'score_kind':'ANOMALY_SCORE','factors':[],'explanation_status':'UNAVAILABLE'}
    if features['cold_start']:return {'status':'INSUFFICIENT_HISTORY','score':None,'score_kind':'ANOMALY_SCORE','factors':[],'explanation_status':'INSUFFICIENT_HISTORY'}
    for key in ('vendor_amount_ratio','employee_category_ratio'):
        value=values[key]
        if value is not None and value>0:
            contribution=min(100,20*abs(math.log2(value)))
            factors.append({'feature':key,'value':value,'signal':round(contribution,6),
                'text':f'Amount is {value:.2f} times the prior same-currency submitted cohort median.',
                'lineage':features['lineage'].get(key,{})})
    z=values['robust_amount_z']
    if z is not None:factors.append({'feature':'robust_amount_z','value':z,'signal':round(min(100,15*z),6),
        'text':f'Amount deviation is {z:.2f} robust scales from the prior submitted cohort median.',
        'lineage':features['lineage'].get('robust_amount_z',{})})
    if not factors:return {'status':'NOT_APPLICABLE','score':None,'score_kind':'ANOMALY_SCORE','factors':[],'explanation_status':'UNAVAILABLE'}
    factors.sort(key=lambda f:(-f['signal'],f['feature']))
    return {'status':'AVAILABLE','score':max(f['signal'] for f in factors),'score_kind':'ANOMALY_SCORE',
        'factors':factors,'explanation_status':'STATISTICAL','algorithm':ALGORITHM,'algorithm_version':VERSION,
        'score_convention':'0–100; larger means a larger statistical deviation, not probability',
        'shap_status':'NOT_APPLICABLE','limitations':'Prior submitted amounts and transparent statistical association; no causation, misconduct or production validation.'}


def combine(deterministic_decision,mode,result,threshold=DEFAULT_THRESHOLD):
    """A model can request review; finance HOLD/REVIEW are never relaxed."""
    if deterministic_decision!='PASS':return deterministic_decision,None
    if mode in ('RULES_ONLY','SHADOW'):return 'PASS',None
    if result.get('status')!='AVAILABLE' or result.get('score') is None:return 'REVIEW','MODEL_UNAVAILABLE'
    if Decimal(str(result['score']))>=Decimal(threshold):return 'REVIEW','ANOMALY_ESCALATION'
    return 'PASS',None
