"""External literal scores cannot erase locale, source-page or unknown boundaries."""
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path

spec=spec_from_file_location('public_evaluation',Path(__file__).resolve().parents[3]/'scripts/benchmark/clearledger_public.py')
evaluation=module_from_spec(spec);spec.loader.exec_module(evaluation)


def test_currency_unit_removal_preserves_printed_decimal_convention():
    assert evaluation.literal(' 1.007,50 € ','total_amount',['€'])=='1.007,50'
    assert evaluation.literal('1007.50','total_amount',['€'])!='1.007,50'
    assert evaluation.literal('AED 2','quantity',['AED'])=='AED 2'  # money units cannot legitimize a quantity
    assert evaluation.literal(None,'tax_amount',['AED']) is None


def test_equal_raw_values_on_wrong_page_or_ambiguous_row_do_not_pass_literal_score():
    case={'headers':{},'money_tokens':['$'],'rows':[{'page':2,'description':'Separate source item','quantity':'2'}],
        'absent':[],'must_be_unresolved':[]}
    doc={'observations':[{'field_path':'lines.0.description','state':'PRESENT','raw_value':'Separate source item','source':{'page':1}},
        {'field_path':'lines.0.quantity','state':'AMBIGUOUS','raw_value':'2','source':{'page':2}}],
        'draft':{'candidate':{'lines.0.quantity':None}}}
    result=evaluation.score(doc,case)
    assert result['row_checked']==2 and result['row_matches']==0
    assert result['rows'][0]['description']['read'] and not result['rows'][0]['description']['page']
    assert not result['rows'][0]['quantity']['read']


def test_missing_tax_is_not_zero_and_dollar_present_cannot_pass_required_ambiguity():
    case={'headers':{'currency':'$'},'accepted_states':{'currency':['AMBIGUOUS']},'money_tokens':['$'],
        'rows':[],'absent':['tax_amount'],'must_be_unresolved':['currency']}
    doc={'observations':[{'field_path':'currency','state':'PRESENT','raw_value':'$'},
        {'field_path':'tax_amount','state':'PRESENT','raw_value':'0.00'}],
        'draft':{'candidate':{'currency':None,'tax_amount':'0.00'}}}
    result=evaluation.score(doc,case)
    assert result['header_matches']==0 and result['required_abstentions']['currency']
    assert not result['absent']['tax_amount']['missing'] and not result['absent']['tax_amount']['canonical_unresolved']
