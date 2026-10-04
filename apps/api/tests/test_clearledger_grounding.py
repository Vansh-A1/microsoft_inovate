"""Independent geometry, question scope and abstention behavior, no gold prompt."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from app.documents.config import ProviderSettings
from app.documents.processor import DocumentFailure
from app.domain.extraction import DocumentSourceType,SCHEMA_VERSION
from app.extraction.layout import printed_layout,table_columns
from app.extraction.typellm import TypeLLMExtractionAdapter
from test_clearledger_layout import span,positioned


def test_labels_above_values_keep_independent_measured_column_evidence():
    words=[span('Supplier:',.05,.1,.13),span('Invoice number:',.55,.1,.18),
           span('Willow',.05,.135,.1),span('Ltd',.16,.135,.05),span('I-73',.55,.135,.1)]
    headers,rows,diagnostics=printed_layout({'spans':words})
    assert [(f,v) for f,v,_ in headers]==[('vendor_name','Willow Ltd'),('invoice_number','I-73')]
    assert headers[0][2]==pytest.approx({'x1':.05,'x2':.21,'y1':.1,'y2':.155})
    assert not rows and not diagnostics


@pytest.mark.parametrize('delta,crossing',[('.12',False),('.035',True)])
def test_stacked_large_gap_or_crossing_value_does_not_establish_a_fact(delta,crossing):
    words=[span('Supplier:',.05,.1,.13),span('Invoice number:',.55,.1,.18),
           span('Unassigned company',.05,.1+float(delta),.6 if crossing else .12),
           span('I-73',.55,.1+float(delta),.1)]
    headers,_,_=printed_layout({'spans':words})
    assert not headers


def table():
    return [span('Description',.05,.3,.15),span('Qty',.4,.3),span('Unit price',.55,.3,.12),span('Amount',.8,.3,.1)]


def item(y,text='Paper'):
    return [span(text,.05,y,.12),span('2',.4,y),span('5.00',.55,y),span('10.00',.8,y)]


def test_close_wrap_before_complete_next_item_retains_union_and_one_row():
    details={'spans':table()+item(.34)+[span('recycled',.05,.37,.12)]+item(.41,'Folders')}
    _,rows,notes=printed_layout(details)
    assert len(rows)==2 and rows[0][0][1]=='Paper recycled' and not notes
    assert rows[0][0][2]['y2']==pytest.approx(.39)


def test_last_item_note_or_footer_is_not_silently_attached():
    _,rows,notes=printed_layout({'spans':table()+item(.34)+[span('terms text',.05,.37,.12)]})
    assert rows[0][0][1]=='Paper' and notes==['TABLE_COVERAGE_UNCERTAIN']


def test_independent_column_scope_requires_a_unique_complete_heading():
    assert table_columns({'spans':table()})==('description','quantity','unit_price','amount')
    assert table_columns({'spans':table()[:-1]}) is None
    assert table_columns({'spans':table()+[span('Amount',.93,.3,.05)]}) is None


class Transport:
    def __init__(self,extra=False):self.calls=[];self.extra=extra
    def generate(self,**kw):
        self.calls.append(kw)
        if 'row_count_raw' in kw['questions']:return SimpleNamespace(result={'row_count_raw':'1','row_count_state':'PRESENT'})
        data={k:('MISSING' if k.endswith('_state') else None) for k in kw['questions']}
        if 'description_raw' in data:
            for key,value in [('description','Paper'),('quantity','2'),('unit_price','5.00'),('amount','10.00')]:
                data[key+'_raw']=value;data[key+'_state']='PRESENT'
            if self.extra:data['tax_amount_raw']='99.00'
        return SimpleNamespace(result=data)


def test_invoice_questions_exclude_receipt_only_fields_and_preserve_missing_columns():
    bundle,_,_,_=positioned();transport=Transport()
    adapter=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://test.example',model='test'),transport,
        image_loader=lambda p:'data:image/png;base64,opaque',printed_columns={1:('description','quantity','unit_price','amount')})
    out=adapter.extract(bundle,SCHEMA_VERSION)
    assert 'merchant_name_raw' not in transport.calls[0]['questions'] and 'expense_date_raw' not in transport.calls[0]['questions']
    assert 'invoice_number_raw' in transport.calls[0]['questions']
    assert set(transport.calls[-1]['questions'])=={f+'_'+part for f in ('description','quantity','unit_price','amount') for part in ('raw','state')}
    row={f.field_path:f for f in out.line_items[0].fields}
    assert row['amount'].raw_value=='10.00'
    for name in ('tax_amount','tax_rate','discount_amount','net_amount','gross_amount','uom'):
        assert row[name].state.value=='MISSING' and row[name].raw_value is None and row[name].source is None
    assert adapter.sidecar['call_metrics'][-1]['question_count']==8


def test_receipt_questions_do_not_manufacture_invoice_identifiers():
    bundle,_,_,_=positioned();bundle=replace(bundle,source_type=DocumentSourceType.EMPLOYEE_RECEIPT)
    transport=Transport();out=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://test.example',model='test'),transport,
        image_loader=lambda p:'data:image/png;base64,opaque').extract(bundle,SCHEMA_VERSION)
    assert len(transport.calls)==1 and not out.line_items
    assert 'invoice_number_raw' not in transport.calls[0]['questions'] and 'merchant_name_raw' in transport.calls[0]['questions']


def test_unrequested_model_tax_or_any_extra_key_is_rejected():
    bundle,_,_,_=positioned()
    adapter=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://test.example',model='test'),Transport(extra=True),
        image_loader=lambda p:'data:image/png;base64,opaque',printed_columns={1:('description','quantity','unit_price','amount')})
    with pytest.raises(DocumentFailure,match='PROVIDER_RESPONSE_INVALID'):adapter.extract(bundle,SCHEMA_VERSION)


@pytest.mark.parametrize('field',['discount_amount','net_amount','tax_rate','tax_amount','gross_amount'])
def test_model_only_row_accounting_candidate_never_normalizes(monkeypatch,field):
    from app.core.identity import Identity
    from app.domain.extraction import FieldObservation,ExtractionObservationState as State
    from app.extraction.native import source
    from app.services import document_worker as worker
    from test_extraction_documents import normalized
    bundle,observed,_,_=positioned()
    row=observed.line_items[0]
    observed=replace(observed,line_items=(replace(row,fields=tuple(f for f in row.fields if f.field_path!=field)+(FieldObservation(field,State.PRESENT,'0.18' if field=='tax_rate' else '12.00',
        source=source(bundle,1,field,None,'0.18' if field=='tax_rate' else '12.00')),)),))
    class Adapter:
        sidecar={'table_coverage':'OBSERVED_ROWS'}
        def __init__(self,*args,**kwargs):pass
        def extract(self,*args):return observed
    monkeypatch.setattr(worker,'TypeLLMExtractionAdapter',Adapter)
    identity=Identity(bundle.tenant_id,bundle.legal_entity_id,bundle.document_id,frozenset({'FINANCE_REVIEWER'}),'Grounding unit test')
    page={'page':1,'native_text':'','spans':[],'route':'VISUAL_REQUIRED','preview_key':'private-object','transform':{}}
    result,_,_=worker.extract({'id':bundle.document_id,'source_type':'VENDOR_INVOICE'},identity,[page],None,
        ProviderSettings(endpoint='http://test.example',model='test'))
    value=next(f for f in result.line_items[0].fields if f.field_path==field)
    assert value.state is State.AMBIGUOUS and value.raw_value is not None
    assert normalized(result)[0]['lines.0.'+field] is None


def test_native_unread_accounting_columns_are_explicit_missing_reviewable_observations():
    from app.domain.extraction import ExtractionObservationState as State
    from test_extraction_documents import normalized
    _,observed,_,_=positioned()
    fields={f.field_path:f for f in observed.line_items[0].fields}
    for name in ('discount_amount','net_amount','tax_rate','tax_amount','gross_amount','uom'):
        assert fields[name].state is State.MISSING
        assert fields[name].raw_value is fields[name].source is None
        assert normalized(observed)[0]['lines.0.'+name] is None
