from copy import deepcopy
from decimal import Decimal
import json
from uuid import uuid4
import pytest
from app.rules.engine import RuleContext
from app.rules.finance_phase3 import evaluate,VERSION
from test_rules_phase1 import context


def inputs(name='vendor/clean'):
    c=json.loads(context(name).encoded);p=c['transaction'];refs=c['references'];policy=refs[p['approval_policy_id']];policy['authority_limits']={role:{'currency':'INR','ceiling_amount':'10000000'} for role in ('MANAGER','DEPARTMENT_HEAD','DIRECTOR','CFO')}
    profile={'id':str(uuid4()),'version':1,'currencies':['INR'],'waivable_rules':['EXP-003']}
    budget=refs[p['budget_id']];c['finance_v3']={'profile':profile,'duplicates':[],'duplicate_coverage':{'status':'COMPLETE'},'allocations':[],'budget':{'allocation':'200000','adjustments':'0','consumed':'0','open_po_commitments':'0','active_reservations':'0','available':'200000','po_commitment_coverage':'0','ledger_event_ids':[]},'approval':{'policy_valid':True,'authority_valid':True,'steps':[{'sequence':1,'role':'MANAGER','state':'APPROVED','authorized':True}]},'receipt_shares':[],'receipt_usage':[],'company_payments':[],'finance_submission_authorized':True,'aggregates':{},'waivers':[]}
    return c


def rule(c,name):return next(r for r in evaluate(RuleContext.pin(**c)).results if r.rule_id==name)


def test_phase3_preserves_clean_and_exact_shortfall():
    c=inputs();assert evaluate(RuleContext.pin(**c)).decision=='PASS'
    c=inputs('vendor/partial_grn');r=rule(c,'GRN-001');assert r.status=='FAIL' and r.observed[0]['eligible_new_quantity']=='50.0000' and Decimal(r.observed[0]['quantity_shortfall'])==20

@pytest.mark.parametrize('operator,absolute,relative,price,expected',[('MAX','20','0.01','1015','PASS'),('MIN','20','0.01','1015','FAIL'),('AND','20','0.01','1015','FAIL'),('OR','20','0.01','1015','PASS')])
def test_tolerance_operator_is_explicit(operator,absolute,relative,price,expected):
    c=inputs();p=c['transaction'];line=p['lines'][0];pl=c['references'][line['po_line_id']];pl['tolerance']={'operator':operator,'price_absolute_amount':absolute,'price_relative_rate':relative};line['unit_price']=price
    r=rule(c,'PO-003');assert r.status==expected and r.observed[0]['unit_price_variance']=='15.00'


def test_approved_uom_conversion_and_unknown_conversion():
    c=inputs();p=c['transaction'];line=p['lines'][0];line.update(uom='BOX',quantity='2',unit_price='10000')
    assert rule(c,'PO-003').status=='UNKNOWN'
    r={'id':str(uuid4()),'version':1,'_kind':'uom_conversions','from_uom':'BOX','to_uom':'EA','factor':'10','status':'APPROVED','effective_from':'2026-01-01','effective_to':'2027-01-01'};c['references'][r['id']]=r
    assert rule(c,'PO-003').status=='PASS' and rule(c,'GRN-001').observed[0]['requested_quantity']=='20'


def test_contract_is_not_service_acceptance():
    c=inputs();p=c['transaction'];cid=str(uuid4());lid=str(uuid4());p.update(po_id=None,contract_id=cid);line=p['lines'][0];line.update(po_line_id=None,grn_line_id=None,contract_line_id=lid)
    base=c['references'][next(k for k,r in c['references'].items() if r['_kind']=='purchase_orders')]
    c['references'][cid]=base|{'id':cid,'_kind':'contracts','non_po_authorized':True,'acceptance_required':True};c['references'][lid]={'id':lid,'version':1,'_kind':'contract_lines','contract_id':cid,'unit_price':'1000','uom':'EA','tolerance':{'operator':'MAX','price_absolute_amount':'0','price_relative_rate':'0'}}
    r=rule(c,'GRN-001');assert r.status=='FAIL' and r.decision_effect=='HOLD'
    sid=str(uuid4());actor=next(r for r in c['references'].values() if r['_kind']=='employees' and 'MANAGER' in r.get('roles',[]));actor['roles'].append('SERVICE_ACCEPTER');line['service_acceptance_id']=sid
    c['references'][sid]={'id':sid,'version':1,'_kind':'service_acceptances','contract_id':cid,'contract_line_id':lid,'accepted_amount':'25000','accepted_quantity':'20','accepter_id':actor['id'],'status':'ACCEPTED'}
    assert rule(c,'GRN-001').status=='PASS'


def test_repeated_line_demands_are_aggregated():
    c=inputs();line=c['transaction']['lines'][0];c['transaction']['lines']=[line,line|{'id':str(uuid4()),'quantity':'40'}]
    assert rule(c,'GRN-001').status=='FAIL'


def test_fuzzy_phash_do_not_confirm_and_resolution_is_separate():
    c=inputs();r={'id':str(uuid4()),'version':1,'classification':'POSSIBLE_DUPLICATE','signals':{'active_obligation':True,'phash':{'distance':1}}};c['finance_v3']['duplicates']=[r]
    assert rule(c,'DUP-001').decision_effect=='REVIEW' and rule(c,'DUP-003').status=='PASS'
    r['disposition']='CONFIRMED_DUPLICATE';assert rule(c,'DUP-003').decision_effect=='HOLD'


def test_shared_receipt_capacity_and_company_card():
    c=inputs('employee/shared_within');p=c['transaction'];item=p['items'][0];v=c['finance_v3'];v['receipt_shares']=[{'id':str(uuid4()),'version':1,'item_id':item['id'],'employee_id':p['employee_id'],'document_id':item['source_document_id'],'amount':item['claimed_amount']}]
    assert rule(c,'EXP-005').status=='PASS' and rule(c,'SYS-001').status=='PASS'
    v['receipt_usage']=[{'id':str(uuid4()),'version':1,'resource_id':item['source_document_id'],'amount':'800'}];assert rule(c,'EXP-005').decision_effect=='HOLD'
    c=inputs('employee/clean_taxi');p=c['transaction'];item=p['items'][0];r={'id':str(uuid4()),'version':1,'employee_id':p['employee_id'],'document_id':item['source_document_id'],'amount':item['claimed_amount'],'payment_type':'COMPANY_CARD','currency':'INR','status':'CONFIRMED'};c['finance_v3']['company_payments']=[r]
    assert rule(c,'EXP-006').decision_effect=='HOLD'


def test_adding_mandatory_failure_cannot_clear_hold_and_waiver_retains_result():
    c=inputs('vendor/partial_grn');assert evaluate(RuleContext.pin(**c)).decision=='HOLD';c['finance_v3']['approval']['authority_valid']=False;assert evaluate(RuleContext.pin(**c)).decision=='HOLD'
    c=inputs('employee/daily_meals');assert rule(c,'EXP-003').status=='FAIL';c['finance_v3']['waivers']=[{'rule_id':'EXP-003','rule_version':rule(c,'EXP-003').version,'expires_at':'2026-10-10T00:00:00+00:00'}]
    result=evaluate(RuleContext.pin(**c));assert result.decision=='PASS' and next(r for r in result.results if r.rule_id=='EXP-003').status=='FAIL'

@pytest.mark.parametrize('returned,reversed,prior,new,expected',[('10','0','30','50','FAIL'),('0','0','30','50','PASS'),('0','10','30','40','PASS'),('0','0','30','51','FAIL')])
def test_net_delivery_capacity_returns_and_exact_boundary(returned,reversed,prior,new,expected):
    c=inputs();line=c['transaction']['lines'][0];grn=c['references'][line['grn_line_id']];grn.update(accepted_quantity='80',returned_quantity=returned,reversed_quantity=reversed)
    # Isolate current active allocation from seeded historical allocations.
    for r in c['references'].values():
        if r.get('_kind')=='matching_allocations':r['lifecycle']='REVERSED'
    c['finance_v3']['allocations']=[{'id':str(uuid4()),'version':1,'resource_id':grn['id'],'kind':'GRN_LINE','quantity':prior,'amount':'0','state':'CONSUMED','metadata':{}}];line['quantity']=new
    assert rule(c,'GRN-001').status==expected


def test_capacity_invariants_over_many_decimal_boundaries():
    # Decimal boundary sweep is deliberately one invariant test, not 160 inflated cases.
    for accepted in range(1,9):
        for previous in range(accepted+1):
            c=inputs();line=c['transaction']['lines'][0];grn=c['references'][line['grn_line_id']];grn.update(accepted_quantity=str(accepted),returned_quantity='0',reversed_quantity='0')
            for r in c['references'].values():
                if r.get('_kind')=='matching_allocations':r['lifecycle']='REVERSED'
            c['finance_v3']['allocations']=[{'id':str(uuid4()),'version':1,'resource_id':grn['id'],'kind':'GRN_LINE','quantity':str(previous),'amount':'0','metadata':{}}]
            line['quantity']=str(accepted-previous+1)
            assert rule(c,'GRN-001').decision_effect=='HOLD'


@pytest.mark.parametrize('unit,key',[('ITEM','per_item_limit'),('TRIP','trip_limit'),('MONTH','monthly_limit')])
def test_configured_expense_aggregate_dimensions(unit,key):
    c=inputs('employee/clean_taxi');p=c['transaction'];c['references'][p['expense_policy_id']][key]='1000';c['finance_v3']['aggregates'][unit]={'amount':'1200','related_ids':[]}
    assert key in rule(c,'EXP-002').observed['failed']
    c['finance_v3']['aggregates'][unit]['amount']='1000';assert rule(c,'EXP-002').status=='PASS'


@pytest.mark.parametrize('kind',['COMPANY_CARD','ADVANCE'])
def test_verified_payment_offsets_do_not_change_requested(kind):
    c=inputs('employee/clean_taxi');p=c['transaction'];item=p['items'][0];original=p['requested_amount'];c['finance_v3']['company_payments']=[{'id':str(uuid4()),'version':1,'employee_id':p['employee_id'],'document_id':item['source_document_id'],'currency':'INR','payment_type':kind,'status':'CONFIRMED','amount':'400'}]
    assert rule(c,'EXP-006').decision_effect=='HOLD' and c['transaction']['requested_amount']==original


def test_split_pattern_is_review_only_and_not_a_duplicate_confirmation():
    c=inputs('employee/clean_taxi');c['finance_v3']['split_pattern']={'threshold':'2500','aggregate':'4800','related_records':[]}
    assert rule(c,'PAT-001').decision_effect=='REVIEW' and rule(c,'DUP-003').status=='PASS'


def test_currency_and_unknown_denominator_never_become_pass():
    c=inputs('employee/clean_taxi');c['transaction']['currency']='USD';assert evaluate(RuleContext.pin(**c)).decision!='PASS'
    c=inputs('employee/hotel_unknown_nights');assert rule(c,'EXP-003').status=='UNKNOWN'


def test_policy_gap_overlap_and_stale_sources_preserve_unknown_with_evidence():
    c=inputs('employee/clean_taxi');policy=c['references'][c['transaction']['expense_policy_id']]
    policy['effective_to']='2026-01-01';assert rule(c,'REF-001').status=='UNKNOWN' and evaluate(RuleContext.pin(**c)).decision!='PASS'
    c=inputs('employee/clean_taxi');policy=c['references'][c['transaction']['expense_policy_id']]
    extra=policy|{'id':str(uuid4()),'allowance_amount':'999999'};c['references'][extra['id']]=extra
    assert rule(c,'REF-001').status=='UNKNOWN' and evaluate(RuleContext.pin(**c)).decision!='PASS'
    c=inputs();rid=c['transaction']['vendor_id'];c['finance_v3']['stale_references']=[rid]
    result=rule(c,'REF-001');assert result.status=='UNKNOWN' and any(str(e.record_id)==rid for e in result.evidence)
