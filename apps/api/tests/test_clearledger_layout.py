"""Actual text geometry, conservative uncertainty and no model-supplied finance facts."""
from dataclasses import replace
from io import BytesIO
from uuid import uuid4
import pytest
from app.db.models import Base
from app.documents.processor import parse
from app.domain.extraction import DocumentBundle, DocumentPage, DocumentSourceType, SCHEMA_VERSION, to_data
from app.extraction.native import NativeTextExtractionAdapter
from app.extraction.layout import printed_layout
from app.extraction.typellm import TypeLLMExtractionAdapter
from app.documents.config import ProviderSettings
from app.services.document_worker import printed_mapping_complete, mapping_gaps
from test_extraction_documents import extracted, normalized, MockTransport


def positioned():
    from reportlab.pdfgen import canvas
    out=BytesIO();c=canvas.Canvas(out,pagesize=(720,720));c.setFont('Helvetica',10)
    for y,left,value,right,rv in [(670,'Supplier:','Fictional Cedar Ltd','Invoice number:','LAY-29'),
        (650,'Currency:','INR','Invoice date:','2026-09-19'),
        (630,'Subtotal:','30.00','Tax:','5.40'),(610,'Total:','35.40','Tax basis:','EXCLUSIVE')]:
        for x,text in [(30,left),(130,value),(380,right),(510,rv)]:c.drawString(x,y,text)
    for y,values in [(550,['Description','Qty','Unit price','Amount']),
                     (525,['Paper packs','2','15.00','30.00'])]:
        for x,text in zip([30,260,370,530],values):c.drawString(x,y,text)
    c.save();pages=parse(out.getvalue())['pages']
    b=DocumentBundle(uuid4(),1,uuid4(),uuid4(),DocumentSourceType.VENDOR_INVOICE,
                    tuple(DocumentPage(p['page'],p['native_text']) for p in pages))
    a=NativeTextExtractionAdapter(pages);return b,a.extract(b,SCHEMA_VERSION),a,pages


def test_actual_multicolumn_labels_and_table_regions_do_not_flatten_values():
    b,r,a,_=positioned();by={f.field_path:f for f in r.header_fields}
    assert by['vendor_name'].raw_value=='Fictional Cedar Ltd' and by['invoice_number'].raw_value=='LAY-29'
    assert by['currency'].raw_value=='INR' and by['tax_amount'].raw_value=='5.40'
    assert not a.diagnostics
    cells={f.field_path:f for f in r.line_items[0].fields}
    assert cells['quantity'].raw_value=='2' and cells['amount'].raw_value=='30.00'
    assert cells['amount'].source.document_id==b.document_id and cells['amount'].bbox is not None
    assert cells['amount'].bbox.x1>cells['quantity'].bbox.x2
    candidate,_,_=normalized(r);assert candidate['currency']=='INR' and candidate['total_amount']=='35.40'


def test_absent_optional_financial_fields_do_not_trigger_guessing_or_clear_validation():
    _,r,a,_=positioned()
    assert printed_mapping_complete(r,'VENDOR_INVOICE',a.diagnostics)
    assert 'shipping_amount' in mapping_gaps(r,'VENDOR_INVOICE')
    candidate,traces,findings=normalized(r)
    assert candidate['shipping_amount'] is None and candidate['document_discount_amount'] is None
    from app.documents.normalizer import validate_draft
    assert validate_draft(candidate,traces,'VENDOR_INVOICE')


def span(text,x,y,width=.05,height=.02):
    return {'text':text,'bbox':{'x1':x,'x2':x+width,'y1':y,'y2':y+height},'kind':'word'}


def test_ocr_word_layout_keeps_distinct_columns_and_ignores_duplicate_line_regions():
    words=[span('Supplier:',.05,.1,.1),span('Cedar',.2,.1),span('Ltd',.27,.1),
           span('Invoice',.55,.1,.08),span('number:',.64,.1,.08),span('DOC-73',.8,.1,.1)]
    h,rows,d=printed_layout({'spans':words+[{'text':'flattened unrelated words','bbox':{'x1':.05,'x2':.9,'y1':.1,'y2':.12},'kind':'line'}]})
    assert [(f,v) for f,v,_ in h]==[('vendor_name','Cedar Ltd'),('invoice_number','DOC-73')]
    assert not rows and not d


def test_rotated_ocr_associates_upright_words_but_cites_original_coordinates():
    from app.extraction.ocr import original_box
    words=[span('Currency:',.05,.1,.12),span('INR',.2,.1),span('Category:',.55,.1,.12),span('HOTEL',.8,.1,.1)]
    for word in words:
        word['layout_bbox']=dict(word['bbox'])
        word['bbox']=original_box(word['bbox'],6)
    headers,_,_=printed_layout({'spans':words})
    assert [(f,v) for f,v,_ in headers]==[('currency','INR'),('category','HOTEL')]
    box=headers[0][2]
    assert box==pytest.approx({'x1':.1,'x2':.12,'y1':.75,'y2':.95})


@pytest.mark.parametrize('value',['','ambiguous','illegible'])
def test_critical_incomplete_mapping_cannot_skip_model(value):
    from app.domain.extraction import ExtractionObservationState as State
    _,r,_,_=positioned()
    state=State.MISSING if not value else (State.AMBIGUOUS if value=='ambiguous' else State.ILLEGIBLE)
    bad=replace(r,header_fields=tuple(replace(f,state=state,raw_value=value or None,
        source=f.source if value else None) if f.field_path=='currency' else f for f in r.header_fields))
    assert not printed_mapping_complete(bad,'VENDOR_INVOICE')


def test_wrapped_or_crossing_cells_abstain_instead_of_dropping_unseen_items():
    words=[span('Description',.05,.1,.15),span('Qty',.4,.1),span('Unit price',.55,.1,.12),span('Amount',.8,.1,.1),
           span('long crossing description',.05,.15,.45),span('1',.4,.15),span('12.00',.55,.15),span('12.00',.8,.15)]
    _,rows,d=printed_layout({'spans':words})
    assert not rows and d==['TABLE_COVERAGE_UNCERTAIN']


def test_known_headers_avoid_model_re_read_but_visual_rows_use_real_contract():
    from app.domain.extraction import ExtractionObservationState as State
    b,r,_,_=positioned()
    class Transport:
        def __init__(self):self.calls=[]
        def generate(self,**kw):
            from types import SimpleNamespace
            self.calls.append(kw)
            return SimpleNamespace(result={'row_count_state':'PRESENT','row_count_raw':'0'})
    t=Transport();a=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://test.example',model='test-model'),t,
        image_loader=lambda p:'data:image/png;base64,test',header_observations={1:r.header_fields})
    out=a.extract(b,SCHEMA_VERSION)
    assert len(t.calls)==1 and set(t.calls[0]['questions'])=={'row_count_raw','row_count_state'}
    assert next(f for f in out.header_fields if f.field_path=='vendor_name').raw_value=='Fictional Cedar Ltd'
    assert a.sidecar['header_fields_requested']==[{'page':1,'fields':[]}]


def test_two_printed_invoice_identities_still_require_segmentation():
    _,r,_,pages=positioned();page=pages[0]
    page['spans']+= [{k:v for k,v in s.items() if k!='kind'} for s in
                    [span('Invoice number:',.05,.98,.2,.01),span('OTHER-29',.3,.98,.1,.01)]]
    b=DocumentBundle(uuid4(),1,uuid4(),uuid4(),DocumentSourceType.VENDOR_INVOICE,(DocumentPage(1,page['native_text']),))
    a=NativeTextExtractionAdapter([page]);out=a.extract(b,SCHEMA_VERSION)
    assert next(f for f in out.header_fields if f.field_path=='invoice_number').state.value=='AMBIGUOUS'
    assert 'SEGMENTATION_UNCERTAIN' in a.diagnostics


def test_model_inferred_tax_treatment_cannot_become_normalized_source_fact(monkeypatch):
    from app.core.identity import Identity
    from app.services import document_worker as worker
    b,r,_,_=positioned()
    class Adapter:
        sidecar={'table_coverage':'OBSERVED_ROWS'}
        def __init__(self,*args,**kwargs):pass
        def extract(self,*args):return r
    monkeypatch.setattr(worker,'TypeLLMExtractionAdapter',Adapter)
    identity=Identity(b.tenant_id,b.legal_entity_id,uuid4(),frozenset({'FINANCE_REVIEWER'}),'Unit source check')
    page={'page':1,'native_text':'','spans':[],'route':'VISUAL_REQUIRED','preview_key':'private-object','transform':{}}
    out,_,_=worker.extract({'id':b.document_id,'source_type':'VENDOR_INVOICE'},identity,[page],None,
        ProviderSettings(endpoint='http://test.example',model='test'))
    basis=next(f for f in out.header_fields if f.field_path=='tax_basis')
    assert basis.raw_value=='EXCLUSIVE' and basis.state.value=='AMBIGUOUS'
    assert 'Model-only tax treatment' in basis.diagnostic_note
    assert normalized(out)[0]['tax_basis'] is None
