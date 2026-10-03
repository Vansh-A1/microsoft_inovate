from copy import deepcopy
from datetime import date
from uuid import uuid4
from app.core.identity import Identity
from app.services.reference_imports import validate_records,resolve,select_policy
S=Identity(uuid4(),uuid4(),uuid4(),frozenset({'REFERENCE_ADMIN'}))

def profile():return {'kind':'finance_profiles','payload':{'id':str(uuid4()),'version':1,'effective_from':'2026-01-01','effective_to':'2027-01-01','ruleset':'rules-p3-v1','currencies':['INR'],'duplicate_window_days':7,'near_amount_absolute':'10.00','fuzzy_number_cutoff':85,'phash_distance':6,'waivable_rules':['EXP-003'],'waiver_roles':['FINANCE_CONTROLLER'],'freshness_days':30}}

def test_valid_import_and_no_float_money():
    r=profile();assert validate_records([r],{},S)==[]
    r['payload']['near_amount_absolute']=10.0
    assert any(e['code']=='DECIMAL_STRING_REQUIRED' for e in validate_records([r],{},S))

def test_duplicate_identity_scope_and_period():
    r=profile();other=deepcopy(r)
    assert any(e['code']=='DUPLICATE_ID' for e in validate_records([r,other],{},S))
    r['payload']['tenant_id']=str(uuid4());r['payload']['effective_to']='2025-01-01'
    assert {'FOREIGN_SCOPE','PERIOD_INVALID'}<={e['code'] for e in validate_records([r],{},S)}

def test_profile_cannot_waive_mandatory_controls_or_silently_enable_fx():
    r=profile();r['payload']['waivable_rules']=['BUD-001'];r['payload']['currencies']=['USD']
    assert {'NONWAIVABLE_CONTROL','UNSUPPORTED_FINANCE_PROFILE'}<={e['code'] for e in validate_records([r],{},S)}

def test_exact_curated_alias_and_fuzzy_never_binding():
    r={'id':str(uuid4()),'version':1,'_kind':'vendors','legal_name':'Synthetic Paper Limited','aliases':['SP Ltd'],'effective_from':'2026-01-01','effective_to':'2027-01-01'};refs={r['id']:r}
    assert resolve(refs,'vendors',identifier=r['id'])['method']=='EXACT'
    assert resolve(refs,'vendors',name='sp ltd')['method']=='CURATED_ALIAS'
    result=resolve(refs,'vendors',name='Synthetic Papers Limited');assert result['state']=='UNRESOLVED' and result['record'] is None and result['candidates']

def test_overlapping_effective_policy_never_picks_permissive():
    p={'branch':'EMPLOYEE_EXPENSE','category':'MEALS','currency':'INR'}
    r={'id':str(uuid4()),'version':1,'_kind':'expense_policies','category':'MEALS','currency':'INR','effective_from':'2026-01-01','effective_to':'2027-01-01','dimensions':{}}
    assert select_policy({'a':r},'expense_policies',p,'2026-09-25')[0]==r
    assert select_policy({'a':r,'b':r|{'id':str(uuid4())}},'expense_policies',p,'2026-09-25')[0] is None


def test_additive_phase3_scale_catalog_and_manifest_reproducibility():
    import sys,json,hashlib
    from app.core.config import ROOT
    from app.schemas.canonical import Canonical
    sys.path.insert(0,str(ROOT/'scripts/seed'))
    from finance_catalog import catalog,transactions
    generated=json.loads((ROOT/'data/finance_phase3/catalog.json').read_text());assert generated['records']==catalog()
    assert len(transactions())==200 and len({r['id'] for r in transactions()})==200
    for row in transactions():Canonical.model_validate(row['transaction'])
    manifest=json.loads((ROOT/'data/finance_phase3/manifest.json').read_text())
    for f in manifest['files']:assert hashlib.sha256((ROOT/'data/finance_phase3'/f['path']).read_bytes()).hexdigest()==f['sha256']


def test_malformed_reference_collection_shapes_are_invalid_not_crashes():
    document={'kind':'documents','payload':{'id':str(uuid4()),'version':1,'facts':{},'verification':'HUMAN_VERIFIED_SYNTHETIC','source_type':'EMPLOYEE_RECEIPT'}}
    assert validate_records([document],{},S)==[]
    for field,value in [('waivable_rules',{}),('currencies','INR'),('dimensions',[]),('bands',[None]),('ledger',{})]:
        r=profile();r['payload'][field]=value
        assert any(e['code'] in ('OBJECT_REQUIRED','ARRAY_REQUIRED','OBJECT_ARRAY_REQUIRED') for e in validate_records([r],{},S))
