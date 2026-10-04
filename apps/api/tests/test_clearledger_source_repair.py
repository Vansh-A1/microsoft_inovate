"""Source context, locale ambiguity and scoped model calls without finance clearance."""
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4
import pytest
from app.documents.normalizer import Normalizer,NormalizationError,normalize_currency,normalize_money
from app.domain.extraction import DocumentPage,FieldObservation,SCHEMA_VERSION,ExtractionObservationState as State
from app.extraction.layout import printed_layout
from app.extraction.native import NativeTextExtractionAdapter,reconcile,source
from app.extraction.typellm import TypeLLMExtractionAdapter
from app.documents.config import ProviderSettings
from test_clearledger_layout import span,positioned
from test_extraction_documents import normalized


def observation(field,raw,page=1):
    return {'id':str(uuid4()),'field_path':field,'state':'PRESENT','raw_value':raw,
        'source':{'page':page,'bbox':{'x1':.1,'x2':.2,'y1':.3,'y2':.4}}}


@pytest.mark.parametrize('raw,expected',[('€','EUR'),('₹','INR'),('eur','EUR')])
def test_only_supported_unique_printed_currency_symbols_normalize(raw,expected):
    assert normalize_currency(raw)==expected


@pytest.mark.parametrize('raw',['$','¥','£','EUR | USD','euros',''])
def test_ambiguous_or_unsupported_currency_does_not_choose_country_or_fx(raw):
    with pytest.raises(NormalizationError):normalize_currency(raw)


def test_comma_convention_comes_from_source_money_and_retains_literal_trace():
    obs=[observation('currency','€'),observation('subtotal_amount','1.007,50 €'),
        observation('tax_amount','191,43 €'),observation('total_amount','1.198,93 €'),
        observation('lines.0.unit_price','18,90 €'),observation('lines.0.quantity','25')]
    candidate,traces,findings=Normalizer().normalize(obs)
    assert candidate=={'currency':'EUR','subtotal_amount':'1007.50','tax_amount':'191.43','total_amount':'1198.93','lines.0.unit_price':'18.90','lines.0.quantity':'25'}
    total=next(t for t in traces if t['field_path']=='total_amount')
    assert total['raw_value']=='1.198,93 €' and total['number_format']=='DECIMAL_COMMA'
    assert set(total['number_format_source_observation_ids'])=={o['id'] for o in obs[1:5]}
    assert total['source']==obs[3]['source'] and not findings


def test_mixed_printed_decimal_conventions_keep_money_unknown_not_arithmetic_selected():
    obs=[observation('currency','EUR'),observation('subtotal_amount','1.234,50'),observation('tax_amount','12.50'),observation('lines.0.quantity','2')]
    candidate,traces,findings=Normalizer().normalize(obs)
    assert candidate['subtotal_amount'] is candidate['tax_amount'] is None
    assert candidate['lines.0.quantity']=='2' and candidate['currency']=='EUR'
    assert {f['code'] for f in findings}=={'NUMBER_FORMAT_CONFLICT'}
    assert all(t['number_format']=='CONFLICT' for t in traces if t['field_path'].endswith('_amount'))


def test_model_page_context_without_measured_cells_cannot_establish_comma_convention():
    obs=[observation('currency','€'),observation('total_amount','1.007,50 €')]
    obs[1]['source']['bbox']=None
    assert Normalizer().normalize(obs)[0]['total_amount'] is None


@pytest.mark.parametrize('raw',['4.80','0.00'])
def test_model_header_tax_without_document_summary_binding_stays_uncertain(monkeypatch,raw):
    from app.core.identity import Identity
    from app.services import document_worker as worker
    b,r,_,_=positioned()
    output=replace(r,header_fields=tuple(replace(f,raw_value=raw,source=source(b,1,f.field_path,None,raw)) if f.field_path=='tax_amount' else f for f in r.header_fields))
    class Adapter:
        sidecar={'table_coverage':'OBSERVED_ROWS','calls':1}
        def __init__(self,*args,**kwargs):pass
        def extract(self,*args):return output
    monkeypatch.setattr(worker,'TypeLLMExtractionAdapter',Adapter)
    identity=Identity(b.tenant_id,b.legal_entity_id,b.document_id,frozenset({'FINANCE_REVIEWER'}),'Header source unit')
    page={'page':1,'native_text':'','spans':[],'route':'VISUAL_REQUIRED','preview_key':'unit-private-object','transform':{}}
    out,_,_=worker.extract({'id':b.document_id,'source_type':'VENDOR_INVOICE'},identity,[page],None,ProviderSettings(endpoint='http://unit.example',model='unit'))
    tax=next(f for f in out.header_fields if f.field_path=='tax_amount')
    assert tax.state is State.AMBIGUOUS and tax.raw_value==raw
    assert tax.diagnostic_note.startswith('SOURCE_HEADER_AMOUNT_UNCONFIRMED:')
    assert normalized(out)[0]['tax_amount'] is None


def test_currency_alone_and_bad_grouping_cannot_authorize_comma_decimal():
    with pytest.raises(NormalizationError):normalize_money('1,20.00','INR')
    with pytest.raises(NormalizationError):normalize_money('1,20.00','EUR','DECIMAL_COMMA')
    with pytest.raises(NormalizationError):normalize_money('12.34,50','EUR','DECIMAL_COMMA')
    # The low-level explicit point-format parser stays compatible. New source
    # normalization cannot select either convention from an isolated suffix.
    obs=[observation('currency','EUR'),observation('total_amount','1,234')]
    assert normalize_money('1,234','EUR')=='1234'
    assert Normalizer().normalize(obs)[0]['total_amount'] is None
    obs[1]['raw_value']='1.234'
    assert Normalizer().normalize(obs)[0]['total_amount'] is None
    obs+=[observation('subtotal_amount','1,20 €')]
    assert Normalizer().normalize(obs)[0]['total_amount']=='1234'


def test_unpunctuated_stacked_labels_and_small_native_font_extent_overlap():
    words=[span('ISSUE DATE',.5,.1,.15),span('2025-07-12',.5,.117,.15)]
    for word in words:word.pop('kind');word['font_size_points']=10
    headers,_,_=printed_layout({'spans':words})
    assert headers[0][:2]==('invoice_date','2025-07-12')
    words[1]['bbox']['y1']=.11
    assert not printed_layout({'spans':words})[0]
    for word in words:word.pop('font_size_points')
    assert not printed_layout({'spans':words})[0]
    assert not printed_layout({'spans':[span('INVOICE',.1,.1,.1),span('Unowned title',.1,.13,.1)]})[0]


def test_dense_metadata_columns_are_source_fields_and_summary_tax_is_separate():
    columns=['SKU','Barcode','Description','Unit','Qty','Price','Disc.','Tax','Total']
    values=['S-1','00000123','Paper','EA','2','5.00','0.00','0.50','10.00']
    words=[span(v,.02+i*.105,.1,.08) for i,v in enumerate(columns)]
    words+=[span(v,.02+i*.105,.14,.08) for i,v in enumerate(values)]
    words+=[span('VAT 7%',.6,.3,.13),span('0.70',.8,.3,.1)]
    headers,rows,notes=printed_layout({'spans':words})
    assert len(rows)==1 and not notes
    cells={f:v for f,v,_ in rows[0]}
    assert cells['sku']=='S-1' and cells['barcode']=='00000123' and cells['unit_price']=='5.00'
    assert cells['tax_amount']=='0.50' and headers[0][:2]==('tax_amount','0.70')


def test_wide_metadata_cells_need_actual_separation_and_all_financial_anchors():
    columns=['SKU','Barcode','Description','Unit','Qty','Price','Tax','Total']
    headings=[span(v,x,.1,width) for v,x,width in zip(columns,[.08,.22,.46,.62,.69,.76,.84,.92],[.06,.07,.13,.04,.03,.05,.04,.06])]
    values=[span(v,x,.14,width) for v,x,width in zip(['S-7','0001234','Wide printed item','EA','4','5.00','1.00','20.00'],
        [.04,.17,.29,.62,.69,.76,.84,.92],[.10,.10,.29,.04,.03,.05,.04,.06])]
    _,rows,notes=printed_layout({'spans':headings+values})
    assert len(rows)==1 and not notes
    assert {f:raw for f,raw,_ in rows[0]}['description']=='Wide printed item'
    overlapping=[p|{'bbox':p['bbox']|{'x2':.64}} if p['text']=='Wide printed item' else p for p in values]
    assert not printed_layout({'spans':headings+overlapping})[1]
    crossing=[p|{'bbox':p['bbox']|{'x1':.71,'x2':.80}} if p['text']=='4' else p for p in values]
    assert not printed_layout({'spans':headings+crossing})[1]
    missing=[p for p in values if p['text']!='4']
    _,rows,_=printed_layout({'spans':headings+missing})
    assert not rows  # shifted metadata cannot invent a missing quantity


def test_stacked_number_label_can_share_height_with_distant_unrelated_column():
    words=[span('Tax ID: EXAMPLE',.05,.1,.18),span('INVOICE NO.',.6,.1,.15),span('I-785',.6,.13,.1)]
    assert printed_layout({'spans':words})[0][0][:2]==('invoice_number','I-785')
    words[0]['bbox'].update(x1=.5,x2=.59)
    assert not printed_layout({'spans':words})[0]


def test_inline_total_cannot_claim_a_following_tax_basis_row_as_its_value():
    words=[span('Total:',.05,.1,.07),span('236.00',.18,.1,.08),
           span('Tax basis: EXCLUSIVE',.05,.14,.2)]
    headers,_,_=printed_layout({'spans':words})
    assert next(h for h in headers if h[0]=='total_amount')[:2]==('total_amount','236.00')
    assert not any(h[0]=='total_amount' and 'EXCLUSIVE' in h[1] for h in headers)


def test_source_monetary_units_supply_unique_currency_or_explicit_ambiguity():
    b,_,_,_=positioned()
    for raw,state,expected in [('€ 18,90',State.PRESENT,'€'),('$18.90',State.AMBIGUOUS,'$')]:
        details={'page':1,'native_text':'','spans':[span('Total:',.1,.1,.1),span(raw,.3,.1,.15)]}
        out=NativeTextExtractionAdapter([details]).extract(replace(b,pages=(DocumentPage(1,''),)),SCHEMA_VERSION)
        f=next(f for f in out.header_fields if f.field_path=='currency')
        assert f.state is state and f.raw_value==expected and f.bbox is not None
        candidate,traces,_=normalized(out)
        assert candidate['currency']==('EUR' if state is State.PRESENT else None)


def test_provider_null_is_not_a_printed_conflict_but_real_conflict_is_retained():
    b,r,_,_=positioned()
    old=next(f for f in r.header_fields if f.field_path=='total_amount')
    unread=replace(old,state=State.ILLEGIBLE,raw_value=None,diagnostic_note='PROVIDER_VALUE_UNREAD: unable to read')
    other=replace(r,header_fields=tuple(unread if f.field_path=='total_amount' else f for f in r.header_fields))
    kept=next(f for f in reconcile(r,other).header_fields if f.field_path=='total_amount')
    assert kept.state is State.PRESENT and kept.raw_value=='35.40' and kept.source==old.source
    true_conflict=replace(other,header_fields=tuple(replace(f,state=State.PRESENT,raw_value='38.40',diagnostic_note=None) if f.field_path=='total_amount' else f for f in other.header_fields))
    ambiguous=next(f for f in reconcile(r,true_conflict).header_fields if f.field_path=='total_amount')
    assert ambiguous.state is State.AMBIGUOUS and '35.40 | 38.40'==ambiguous.raw_value
    genuine_illegibility=replace(other,header_fields=tuple(replace(f,diagnostic_note='Source ink unreadable') if f.field_path=='total_amount' else f for f in other.header_fields))
    assert next(f for f in reconcile(r,genuine_illegibility).header_fields if f.field_path=='total_amount').state is State.AMBIGUOUS


def test_source_header_scope_reuses_other_page_totals_and_does_not_repeat_header_call():
    b,r,_,_=positioned();b=replace(b,pages=(DocumentPage(1,''),DocumentPage(2,'')))
    page1=tuple(replace(f,state=State.MISSING,raw_value=None,source=None) if f.field_path in ('vendor_name','subtotal_amount','tax_amount','total_amount') else f for f in r.header_fields)
    page2=tuple(replace(f,source=replace(f.source,page=2)) if f.field_path in ('subtotal_amount','tax_amount','total_amount') else
        FieldObservation(f.field_path,State.MISSING) for f in r.header_fields)
    class Transport:
        def __init__(self):self.calls=[]
        def generate(self,**kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(result={name:('Fictional reviewed source vendor' if name=='vendor_name_raw' else 'PRESENT' if name=='vendor_name_state' else None if name.endswith('_raw') else 'MISSING') for name in kwargs['questions']})
    second_rows=tuple(replace(row,fields=tuple(replace(f,source=replace(f.source,page=2)) if f.source else f for f in row.fields)) for row in r.line_items)
    t=Transport();a=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://unit.example',model='unit'),t,
        image_loader=lambda p:'data:image/png;base64,unit',header_observations={1:page1,2:page2},row_observations={1:r.line_items,2:second_rows})
    out=a.extract(b,SCHEMA_VERSION)
    assert len(t.calls)==1 and a.sidecar['header_fields_requested'][1]['fields']==[]
    assert 'total_amount_raw' not in t.calls[0]['questions'] and 'invoice_date_raw' not in t.calls[0]['questions']
    assert next(f for f in out.header_fields if f.field_path=='total_amount').raw_value=='35.40'
    assert next(f for f in out.header_fields if f.field_path=='total_amount').page==2
    assert len(out.line_items)==2  # distinct equal items are preserved, not deduplicated
    assert [row.fields[0].page for row in out.line_items]==[1,2]
