"""Measured row identity, unread cells and bounded unassociated generation."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from app.core.config import ROOT
from app.db.models import Base  # initialize the existing schema registry before worker imports
from app.documents.config import ProviderSettings
from app.documents.processor import DocumentFailure,DocumentProcessor
from app.documents.normalizer import validate_draft
from app.domain.extraction import DocumentBundle,DocumentPage,SCHEMA_VERSION,ExtractionObservationState as State
from app.extraction.layout import printed_layout
from app.extraction.native import NativeTextExtractionAdapter,reconcile
from app.extraction.row_grounding import source_rows
from app.extraction.typellm import TypeLLMExtractionAdapter
from app.services.document_worker import source_table_reviewable
from test_clearledger_layout import span,positioned
from test_clearledger_grounding import table,item
from test_extraction_documents import normalized


@pytest.mark.parametrize('missing',[1,2,3])
def test_single_unread_cell_keeps_its_source_row_and_following_legitimate_equal_row(missing):
    b,_,_,_=positioned()
    middle=item(.40,'Different item');middle.pop(missing)
    details={'page':1,'native_text':'','spans':table()+item(.34)+middle+item(.46)}
    adapter=NativeTextExtractionAdapter([details]);out=adapter.extract(replace(b,pages=(DocumentPage(1,''),)),SCHEMA_VERSION)
    assert len(out.line_items)==3 and adapter.diagnostics==['TABLE_CELL_UNREAD']
    core=('description','quantity','unit_price','amount');field=core[missing]
    observation=next(f for f in out.line_items[1].fields if f.field_path==field)
    assert observation.state is State.MISSING and observation.raw_value is None
    assert observation.source.page==1 and observation.bbox is None
    assert source_table_reviewable(out,adapter.diagnostics)
    identities=source_rows(out)
    assert len({r['identity'] for r in identities})==3 and identities[1]['unread_fields']==[field]
    assert out.line_items[0].fields[0].raw_value==out.line_items[2].fields[0].raw_value=='Paper'
    assert out.line_items[0].fields[0].bbox.y2<out.line_items[2].fields[0].bbox.y1
    candidate,traces,_=normalized(out);assert candidate[f'lines.1.{field}'] is None
    findings=validate_draft(candidate,traces,'VENDOR_INVOICE',adapter.diagnostics)
    question=next(f['message'] for f in findings if f['field']==f'lines.1.{field}')
    assert 'line 2 (Different item) on page 1' in question and 'do not calculate' in question


def test_multiple_blank_cells_crossing_values_and_ocr_conflicts_do_not_satisfy_reviewable_gate():
    b,r,_,_=positioned()
    middle=item(.4)[::3]
    _,rows,notes=printed_layout({'spans':table()+item(.34)+middle+item(.46)})
    assert len(rows)==1 and notes==['TABLE_COVERAGE_UNCERTAIN']
    assert not source_table_reviewable(r,notes)
    other=replace(r,line_items=(replace(r.line_items[0],fields=tuple(replace(f,raw_value='99.00') if f.field_path=='unit_price' else f for f in r.line_items[0].fields)),))
    conflict=reconcile(r,other)
    assert not source_table_reviewable(conflict)
    assert normalized(conflict)[0]['lines.0.unit_price'] is None


def test_identical_printed_rows_on_separate_pages_have_distinct_source_identity():
    b,_,_,_=positioned();pages=DocumentProcessor().process(ROOT/'data/clearledger_row_identity/q04.pdf')['pages']
    b=replace(b,pages=tuple(DocumentPage(p['page'],p['native_text']) for p in pages))
    out=NativeTextExtractionAdapter(pages).extract(b,SCHEMA_VERSION)
    assert len(out.line_items)==3
    identities=source_rows(out)
    assert [r['page'] for r in identities]==[1,2,3] and len({r['identity'] for r in identities})==3
    assert len({r.fields[0].raw_value for r in out.line_items})==1


class RepeatingTransport:
    def __init__(self,count=3,timeout=False):self.calls=[];self.count=count;self.timeout=timeout
    def generate(self,**kwargs):
        self.calls.append(kwargs)
        if 'row_count_raw' in kwargs['questions']:return SimpleNamespace(result={'row_count_raw':str(self.count),'row_count_state':'PRESENT'})
        if self.timeout:raise TimeoutError('Unit timeout without partial result')
        raw={'description':'Paper','quantity':'2','unit_price':'5.00','amount':'10.00'}
        return SimpleNamespace(result={f+'_'+part:(value if part=='raw' else 'PRESENT') for f,value in raw.items() for part in ('raw','state')})


def crop(page,ordinal,count):
    # Identical pixel payload/hash is allowed for distinct measured source rows.
    return 'data:image/png;base64,unit-identical-crop',{'version':'ruled-table-crops-v1','preview_dimensions':[800,600],
        'row_extent_pixels':[60,100+ordinal*50,740,140+ordinal*50],'sha256':'a'*64,'field_bbox':None}


def adapter(transport,crops=None,two_pages=False):
    b,r,_,_=positioned()
    if two_pages:b=replace(b,pages=b.pages+(DocumentPage(2,''),))
    return b,TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://unit.example',model='unit'),transport,
        image_loader=lambda p:'data:image/png;base64,unit-page',header_observations={p.page:r.header_fields for p in b.pages},
        printed_columns={p.page:('description','quantity','unit_price','amount') for p in b.pages},row_image_loader=crops)


def test_unassociated_repetition_retains_two_candidates_and_stops_remaining_generation():
    t=RepeatingTransport();b,a=adapter(t);out=a.extract(b,SCHEMA_VERSION)
    assert len(t.calls)==3 and len(out.line_items)==3 and a.sidecar['table_coverage']=='UNCERTAIN'
    assert a.sidecar['generation_stops']==[{'page':1,'row':2,'remaining':1,'reason':'REPEATED_UNASSOCIATED_CANDIDATES'}]
    assert all(f.state is State.AMBIGUOUS for row in out.line_items[:2] for f in row.fields if f.raw_value is not None)
    assert out.line_items[0].fields[0].raw_value==out.line_items[1].fields[0].raw_value=='Paper'
    assert all(f.state is State.MISSING and f.raw_value is None for f in out.line_items[2].fields)
    candidate,traces,_=normalized(out)
    assert all(candidate[f'lines.{i}.quantity'] is None for i in range(3))
    findings=validate_draft(candidate,traces,'VENDOR_INVOICE')
    assert any(f['code']=='MODEL_ROW_ASSOCIATION_UNCONFIRMED' for f in findings)
    assert not any(f['code']=='SOURCE_CELL_UNREAD' for f in findings)


def test_equal_model_values_in_distinct_measured_regions_remain_three_separate_items():
    t=RepeatingTransport();b,a=adapter(t,crop);out=a.extract(b,SCHEMA_VERSION)
    assert len(t.calls)==4 and len(out.line_items)==3 and not a.sidecar['generation_stops']
    assert len({r['source_identity'] for r in a.sidecar['row_association_checks']})==3
    assert all(next(f for f in row.fields if f.field_path=='quantity').state is State.PRESENT for row in out.line_items)
    assert all(f.bbox is None for row in out.line_items for f in row.fields)  # crops never become field boxes


def test_duplicate_source_region_prevents_second_model_call_and_cannot_manufacture_items():
    t=RepeatingTransport();b,a=adapter(t,lambda page,ordinal,count:crop(page,1,count));out=a.extract(b,SCHEMA_VERSION)
    assert len(t.calls)==2 and len(out.line_items)==3
    assert a.sidecar['generation_stops']==[{'page':1,'row':2,'remaining':2,'reason':'DUPLICATE_SOURCE_REGION'}]
    assert out.line_items[0].fields[0].state is State.AMBIGUOUS
    assert all(f.raw_value is None and f.state is State.MISSING for row in out.line_items[1:] for f in row.fields)


def test_model_equal_values_across_pages_are_not_value_deduplicated():
    t=RepeatingTransport(count=1);b,a=adapter(t,two_pages=True);out=a.extract(b,SCHEMA_VERSION)
    assert len(t.calls)==4 and len(out.line_items)==2 and not a.sidecar['generation_stops']
    assert [row.fields[0].source.page for row in out.line_items]==[1,2]


def test_timeout_discards_partial_run_and_fresh_retry_preserves_unique_source_rows():
    t=RepeatingTransport(timeout=True);b,a=adapter(t,crop)
    with pytest.raises(DocumentFailure,match='PROVIDER_TIMEOUT') as failure:a.extract(b,SCHEMA_VERSION)
    assert failure.value.retryable and len(t.calls)==2
    retry=RepeatingTransport();b,a=adapter(retry,crop);out=a.extract(b,SCHEMA_VERSION)
    assert len(retry.calls)==4 and len(out.line_items)==3 and not a.sidecar['generation_stops']


def test_row_count_disagreement_never_turns_missing_into_a_fabricated_literal():
    _,r,_,_=positioned();other=replace(r,line_items=r.line_items+(replace(r.line_items[0],row_index=2),))
    out=reconcile(r,other)
    assert all(f.raw_value is None and f.state is State.MISSING for row in out.line_items for f in row.fields if f.field_path=='tax_amount')
