import json
from pathlib import Path
from dataclasses import replace
from decimal import localcontext
import pytest
from app.core.config import ROOT
from app.schemas.canonical import fixture_canonical,Canonical
from app.rules.engine import RuleContext,evaluate,combine,RuleResult,RULE_IDS


def context(name):
    case=json.loads((ROOT/f'data/golden_cases/{name}.json').read_text());transaction=case['transaction'];refs={}
    for file in (ROOT/'data/synthetic/reference').glob('*.json'):
        if file.stem in ('tenants','legal_entities'):continue
        for r in json.loads(file.read_text())['records']:
            if r['tenant_id']!=transaction['tenant_id'] or r['legal_entity_id']!=transaction['legal_entity_id']:continue
            refs[r['id']]=r|{'_kind':file.stem}
            for key,kind in [('lines','po_lines' if file.stem=='purchase_orders' else 'grn_lines'),('ledger','budget_ledger'),('allocations','matching_allocations')]:
                for child in r.get(key,[]):refs[child['id']]=child|{'_kind':kind}
    duplicates=[r for r in refs.values() if r['_kind']=='historical_transactions' and r.get('vendor_id')==transaction.get('vendor_id') and r.get('invoice_number')==transaction.get('invoice_number') and r.get('invoice_date')==transaction.get('invoice_date') and r.get('total_amount')==transaction.get('total_amount') and r['currency']==transaction['currency'] and r['lifecycle'] not in ('CANCELLED','REVERSED')] if transaction['branch']=='VENDOR_INVOICE' else []
    daily=[r for r in refs.values() if r['_kind']=='historical_transactions' and r.get('employee_id')==transaction.get('employee_id') and r.get('category')==transaction['category'] and r.get('expense_date')==transaction.get('expense_date') and r.get('capacity_state') in ('RESERVED','CONSUMED')] if transaction['branch']=='EMPLOYEE_EXPENSE' else []
    approvals=[a|{'policy_id':a['approval_policy_id'],'policy_version':1,'approved_at':a['approved_at'].replace('Z','+00:00')} for a in transaction['approvals']]
    return RuleContext.pin(transaction=fixture_canonical(transaction),transaction_id=transaction['id'],transaction_version=1,tenant_id=transaction['tenant_id'],legal_entity_id=transaction['legal_entity_id'],author_id=transaction['submitter_id'],snapshot_id='80000000-0000-4000-8000-000000000001',references=refs,duplicates=duplicates,daily_history=daily,receipt_conflicts=[],capacity={},capacity_evidence=[],po_commitment_used={},approvals=approvals,evaluated_at=case['evaluation_at'].replace('Z','+00:00'),context_complete=True,import_source=None)


@pytest.mark.parametrize('name,expected',[('vendor/clean','PASS'),('vendor/paid_duplicate','HOLD'),('vendor/partial_grn','HOLD'),('vendor/approval_pending','HOLD'),('employee/clean_taxi','PASS'),('employee/hotel_two_nights','PASS'),('employee/hotel_unknown_nights','REVIEW'),('employee/daily_meals','REVIEW')])
def test_golden_rules(name,expected):
    pinned=context(name)
    with localcontext() as ambient:
        ambient.prec=2
        result=evaluate(pinned)
    assert result.decision==expected
    assert {r.rule_id for r in result.results}==set(RULE_IDS)
    assert all(r.evidence for r in result.results)
    assert all(e.bbox is None for r in result.results for e in r.evidence)
    assert evaluate(pinned)==result


@pytest.mark.parametrize('field',['tax_amount','subtotal_amount','shipping_amount','total_amount','currency','invoice_date'])
def test_missing_never_passes(field):
    data=json.loads(context('vendor/clean').encoded);data['transaction'][field]=None
    result=evaluate(RuleContext.pin(**data))
    assert result.decision!='PASS' and not result.eligible
    assert any(r.status=='UNKNOWN' for r in result.results)


@pytest.mark.parametrize('value',[1.5,True,False,float('inf'),float('nan'),'1e3','1,000.00','NaN','Infinity','1.1234567'])
def test_money_intake_rejects_unsafe_values(value):
    from pydantic import ValidationError
    p=json.loads(context('vendor/clean').encoded)['transaction'];p['total_amount']=value
    with pytest.raises(ValidationError):Canonical.model_validate(p)


@pytest.mark.parametrize('status,effect,expected',[('UNKNOWN','REVIEW','REVIEW'),('ERROR','REVIEW','REVIEW'),('FAIL','HOLD','HOLD'),('FAIL','REVIEW','REVIEW')])
def test_precedence(status,effect,expected):
    base=list(evaluate(context('vendor/clean')).results);base[0]=replace(base[0],status=status,decision_effect=effect)
    assert combine(base).decision==expected
    base[1]=replace(base[1],status='FAIL',decision_effect='HOLD')
    assert combine(base).decision=='HOLD'


def test_daily_aggregate_and_nightly_units():
    meal=next(r for r in evaluate(context('employee/daily_meals')).results if r.rule_id=='EXP-003')
    assert meal.observed['aggregate_amount']=='1800.00' and len(meal.observed['related_transaction_ids'])==2
    hotel=next(r for r in evaluate(context('employee/hotel_two_nights')).results if r.rule_id=='EXP-003')
    assert hotel.observed['claimed_per_night']=='7500' and hotel.status=='PASS'


def test_no_approval_authority_intake():
    from pydantic import ValidationError
    p=json.loads(context('vendor/clean').encoded)['transaction']
    for key in ('tenant_id','roles','approvals','required_approval_roles','history_ids','decision'):
        with pytest.raises(ValidationError):Canonical.model_validate(p|{key:'forged'})


def test_credit_currency_and_scope_incomplete_abstain():
    data=json.loads(context('vendor/clean').encoded)
    for patch in [{'document_type':'CREDIT_NOTE'},{'currency':'USD'}]:
        changed=data|{'transaction':data['transaction']|patch}
        assert not evaluate(RuleContext.pin(**changed)).eligible
    assert not evaluate(RuleContext.pin(**(data|{'context_complete':False}))).eligible
