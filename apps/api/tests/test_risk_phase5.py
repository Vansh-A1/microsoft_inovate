from copy import deepcopy
from datetime import datetime,timezone
from decimal import Decimal
import math
import pytest
from app.risk.features import build,schema,VERSION
from app.risk.anomaly import score,combine
from app.risk.datasets import sampled,temporal_split,supervised_gate

CUTOFF='2026-10-01T12:00:00+00:00'
P={'branch':'VENDOR_INVOICE','vendor_id':'vendor','currency':'INR','total_amount':'100.00','invoice_date':'2026-10-01'}

def history(n=10,amounts=None,**changes):
    return [{'object_id':str(i),'version':1,'known_at':f'2026-09-{i+1:02}T12:00:00+00:00',
        'facts':P|{'invoice_date':f'2026-09-{i+1:02}','total_amount':str(amounts[i] if amounts else 90+i)}}|changes for i in range(n)]

def features(p=None,rows=None,**kwargs):return build(p or P,'current',1,CUTOFF,'snapshot',rows if rows is not None else history(),**kwargs)


def test_cutoff_excludes_current_all_revisions_future_versions_and_future_business_dates():
    rows=history()+[{'object_id':'current','version':99,'known_at':'2026-01-01T00:00:00Z','facts':P|{'total_amount':'999999'}}]
    rows+=[{'object_id':'future','version':1,'known_at':'2026-10-02T00:00:00Z','facts':P|{'total_amount':'999999'}}]
    rows+=[{'object_id':'future-day','version':1,'known_at':'2026-09-01T00:00:00Z','facts':P|{'invoice_date':'2026-10-02'}}]
    rows+=[{'object_id':'0','version':2,'known_at':'2026-10-02T00:00:00Z','facts':P|{'vendor_id':'other','total_amount':'999999'}}]
    baseline=features();actual=features(rows=rows)
    assert actual['values']==baseline['values'] and actual['history_manifest']==baseline['history_manifest']
    assert actual['values']['history_count']==10


def test_latest_known_version_selected_before_party_currency_cohort_filters():
    rows=history()
    rows+=[{'object_id':'0','version':2,'known_at':'2026-09-30T00:00:00Z','facts':P|{'vendor_id':'other'}}]
    assert features(rows=rows)['values']['history_count']==9
    rows[-1]['known_at']='2026-10-01T12:00:00Z'
    assert features(rows=rows)['values']['history_count']==10


def test_future_lifecycle_payment_approval_label_and_disposition_have_no_predictive_effect():
    rows=history();changed=deepcopy(rows)
    for r in changed:r['facts'].update(lifecycle='PAID',future_approval='APPROVED',label='CLEAN_CONFIRMED',duplicate_disposition='DISTINCT',settlement_date='2026-12-01')
    assert features(rows=rows)['values']==features(rows=changed)['values']


@pytest.mark.parametrize('count',[0,1,4])
def test_cold_start_is_explicit_and_never_zero_score(count):
    f=features(rows=history(count));r=score(f)
    assert f['values']['history_count']==count and f['cold_start']
    assert f['values']['vendor_amount_ratio'] is None and r['score'] is None
    assert r['status']=='INSUFFICIENT_HISTORY'


def test_currency_known_time_and_incomplete_coverage_remain_missing():
    rows=history(5)+history(5,object_id='other')
    for r in rows[5:]:r['facts']=r['facts']|{'currency':'USD','total_amount':'1000000'}
    assert features(rows=rows)['values']['history_count']==5
    no_time=history(5,known_at=None);assert features(rows=no_time)['excluded_unknown_knowledge_time']==5
    f=features(coverage=False);assert f['values']['history_count'] is None and f['values']['same_amount_count_30d'] is None
    assert score(f)['status']=='HISTORY_INCOMPLETE'


def test_zero_mad_denominator_and_actual_anomaly_direction_are_explicit():
    f=features(rows=history(5,amounts=[100]*5));low=score(f)
    assert f['values']['robust_amount_z'] is None and f['missing_reasons']['robust_amount_z']=='ZERO_MAD'
    high=score(features(P|{'total_amount':'1600.00'},history(5,amounts=[100]*5)))
    assert low['score']==0 and high['score']==80 and high['score']>low['score']
    assert high['score_kind']=='ANOMALY_SCORE' and high['explanation_status']=='STATISTICAL'
    assert high['shap_status']=='NOT_APPLICABLE'


@pytest.mark.parametrize('amount',[None,0.1,False,'NaN','Infinity'])
def test_invalid_amount_never_becomes_money_or_finite_clean_score(amount):
    f=features(P|{'total_amount':amount});assert f['values']['log_amount'] is None
    assert score(f)['score'] is None


def test_decimal_operands_lineage_version_and_predictive_identifier_exclusion():
    operands={'known_at':'2026-10-01T11:00:00Z','currency':'INR','po_remaining_amount':'200.00',
        'expected_line_amount':'100.00','price_difference_amount':'1.00','receipt_shortfall':'2',
        'budget_post_exposure_amount':'600.00','budget_allocated_amount':'1000.00','payment_account_changed':False}
    f=features(operands=operands)
    assert f['values']['po_value_ratio']==0.5 and f['values']['price_variance_ratio']==0.01
    assert f['values']['budget_utilization_after']==0.6 and f['values']['receipt_shortfall']==2
    assert f['values']['payment_account_changed'] is False and not f['missing']['payment_account_changed']
    assert f['schema_version']==VERSION and f['feature_names']==schema()['order']
    assert f['lineage']['vendor_amount_ratio']['amount']=='100.00'
    assert not {'vendor_id','employee_id','account','name','email','phone'}&set(f['values'])
    assert all(v is None or not isinstance(v,float) or math.isfinite(v) for v in f['values'].values())
    operands['known_at']='2026-10-02T00:00:00Z';assert features(operands=operands)['values']['po_value_ratio'] is None


@pytest.mark.parametrize('mode',['RULES_ONLY','SHADOW','RULES_PLUS_ANOMALY','RULES_PLUS_MODEL'])
def test_actual_statistical_results_never_relax_mandatory_finance_decisions(mode):
    low=score(features(rows=history(5,amounts=[100]*5)))
    high=score(features(P|{'total_amount':'1600'},history(5,amounts=[100]*5)))
    assert combine('HOLD',mode,low)==('HOLD',None)
    assert combine('REVIEW',mode,low)==('REVIEW',None)
    assert combine('HOLD',mode,high)==('HOLD',None)
    assert combine('PASS',mode,high)[0]==('PASS' if mode in ('RULES_ONLY','SHADOW') else 'REVIEW')
    assert combine('PASS',mode,{'status':'MODEL_UNAVAILABLE','score':None})[0]==('PASS' if mode in ('RULES_ONLY','SHADOW') else 'REVIEW')


def test_pass_sampling_is_reproducible_and_not_a_clean_label():
    assert [sampled(str(i),'seed','0.1') for i in range(1000)]==[sampled(str(i),'seed','0.1') for i in range(1000)]
    assert 50<sum(sampled(str(i),'seed','0.1') for i in range(1000))<150
    assert sampled('any','seed','1')
    with pytest.raises(ValueError):sampled('any','seed','0')


def dataset_row(tid,at,label='CLEAN_CONFIRMED',**kwargs):
    return {'transaction_id':tid,'cutoff':at,'label':label,'quality':'FINAL','branch':'VENDOR_INVOICE',
        'party_id':'vendor','data_origin':'SYNTHETIC','group_keys':[]}|kwargs


def test_time_splits_keep_corrections_duplicates_and_transitive_receipts_together():
    rows=[dataset_row('a','2026-01-01T00:00:00Z',group_keys=['document:x']),
        dataset_row('b','2026-01-02T00:00:00Z',group_keys=['document:x','document:y']),
        dataset_row('c','2026-03-01T00:00:00Z',group_keys=['document:y']),
        dataset_row('d','2026-04-01T00:00:00Z')]
    s=temporal_split(rows,'2026-02-01T00:00:00Z','2026-03-15T00:00:00Z','2026-05-01T00:00:00Z')
    assert [r['transaction_id'] for r in s['included']]==['d']
    assert {r['exclusion'] for r in s['excluded']}=={'GROUP_SPANS_TEMPORAL_SPLITS'}
    assert len({r['group_id'] for r in s['excluded']})==1


def test_unseen_group_holdout_excludes_training_and_preserves_test_cohort():
    rows=[dataset_row('a','2026-01-01T00:00:00Z'),dataset_row('b','2026-04-01T00:00:00Z')]
    s=temporal_split(rows,'2026-02-01T00:00:00Z','2026-03-01T00:00:00Z','2026-05-01T00:00:00Z',['vendor'])
    assert s['included'][0]['split']=='UNSEEN_VENDOR'
    assert s['excluded'][0]['exclusion']=='HELD_OUT_PARTY_EARLIER_PERIOD'


def test_synthetic_labels_and_correction_only_never_justify_a_supervised_classifier():
    rows=[dataset_row(str(i),'2026-01-01T00:00:00Z','POLICY_EXCEPTION' if i%2 else 'CLEAN_CONFIRMED') for i in range(10000)]
    gate=supervised_gate(rows);assert gate['status']=='SUPERVISED_TRAINING_NOT_JUSTIFIED'
    assert gate['counts']['representative_labels']==0 and gate['counts']['final_binary_labels']==10000
    correction=dataset_row('a','2026-01-01T00:00:00Z','DOCUMENT_CORRECTION_ONLY')
    s=temporal_split([correction],'2026-02-01T00:00:00Z','2026-03-01T00:00:00Z','2026-05-01T00:00:00Z')
    assert s['excluded'][0]['exclusion']=='NON_BINARY_TAXONOMY'
