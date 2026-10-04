"""Measured orientation geometry, original evidence and safe partial rows."""
import math
from dataclasses import replace
import pytest
from app.db.models import Base
from app.documents.processor import DocumentFailure
from app.extraction.cpu_ocr import mapped_spans
from app.extraction.orientation import affine,aligned_spans,align_layout,crop_pixels,residual_angle
from app.extraction.layout import printed_layout
from app.extraction.native import NativeTextExtractionAdapter
from app.domain.extraction import SCHEMA_VERSION,DocumentPage
from app.services.document_worker import source_table_reviewable
from test_clearledger_layout import span,positioned
from test_extraction_documents import normalized


def raw_spans(rotation=0,skew=0):
    words=[span('Supplier:',.06,.1,.1),span('Fictional Geometry Ltd',.22,.1,.22),
        span('Invoice number:',.06,.15,.16),span('OR-11',.25,.15,.08),
        span('Currency:',.06,.2,.12),span('INR',.22,.2,.05),
        span('Total:',.06,.25,.1),span('24.00',.22,.25,.07),
        span('Description',.06,.4,.15),span('Qty',.4,.4,.04),span('Unit price',.55,.4,.12),span('Amount',.8,.4,.1),
        span('Paper wallets',.06,.45,.18),span('2',.4,.45,.03),span('12.00',.55,.45,.08),span('24.00',.8,.45,.08)]
    out=[];theta=math.radians(skew)
    for word in words:
        box=word['bbox'];points=[]
        for x,y in [(box['x1'],box['y1']),(box['x2'],box['y1']),(box['x2'],box['y2']),(box['x1'],box['y2'])]:
            x*=1000;y*=1000
            x,y=(x-500)*math.cos(theta)-(y-500)*math.sin(theta)+500,(x-500)*math.sin(theta)+(y-500)*math.cos(theta)+500
            x,y={0:(x,y),90:(1000-y,x),180:(1000-x,1000-y),270:(y,1000-x)}[rotation]
            points.append([x,y])
        actual={'x1':min(x for x,y in points)/1000,'x2':max(x for x,y in points)/1000,
            'y1':min(y for x,y in points)/1000,'y2':max(y for x,y in points)/1000}
        out.append({'text':word['text'],'bbox':actual,'layout_bbox':actual,'kind':'line','polygon_layout_pixels':points})
    return tuple(out)


@pytest.mark.parametrize('rotation',[0,90,180,270])
def test_four_orientations_restore_only_layout_and_keep_measured_source_boxes(rotation):
    original=raw_spans(rotation);result,transform,meta=align_layout(original,1000,1000)
    assert meta['status']=='ALIGNED' and meta['image_bytes_transformed'] is False
    assert meta['clockwise_degrees']==(360-rotation)%360
    assert [s['bbox'] for s in result]==[s['bbox'] for s in original]
    headers,rows,notes=printed_layout({'spans':result})
    assert ('invoice_number','OR-11') in [(f,v) for f,v,_ in headers]
    assert len(rows)==1 and dict((f,v) for f,v,_ in rows[0])['amount']=='24.00'
    assert not notes


def test_small_skew_uses_actual_polygons_and_no_image_resampling():
    original=raw_spans(skew=4);result,_,meta=align_layout(original,1000,1000)
    assert meta['status']=='ALIGNED' and meta['residual_clockwise_degrees']==pytest.approx(4)
    assert meta['layout_only_deskew_degrees']==pytest.approx(-4)
    assert [s['bbox'] for s in result]==[s['bbox'] for s in original]
    assert len(printed_layout({'spans':result})[1])==1


def test_crop_retry_inverse_maps_context_to_original_preview_not_fake_field_box():
    transform=affine(100,200,90)
    pixels=crop_pixels({'x1':.8,'x2':.9,'y1':.1,'y2':.5},transform)
    assert 9<=pixels[0]<=10 and 19<=pixels[1]<=20
    assert 50<=pixels[2]<=51 and 40<=pixels[3]<=41
    original={'text':'2','bbox':{'x1':.1,'x2':.5,'y1':.1,'y2':.2},
        'polygon_layout_pixels':[[10,20],[50,20],[50,40],[10,40]]}
    read=aligned_spans((original,),transform)[0]
    assert read['bbox']==original['bbox']
    assert read['layout_bbox']==pytest.approx({'x1':.8,'x2':.9,'y1':.1,'y2':.5})
    with pytest.raises(ValueError):crop_pixels({'x1':False,'x2':.9,'y1':.1,'y2':.5},transform)


def test_unowned_or_tied_orientation_and_missing_polygons_do_not_transform_evidence():
    original=({'text':'Unowned text','bbox':{'x1':.1,'x2':.3,'y1':.2,'y2':.25},
        'layout_bbox':{'x1':.1,'x2':.3,'y1':.2,'y2':.25},'polygon_layout_pixels':[[100,200],[300,200],[300,250],[100,250]]},)
    result,_,meta=align_layout(original,1000,1000)
    assert result==original and meta['status']=='ORIENTATION_UNRESOLVED'
    plain=tuple({k:v for k,v in s.items() if k!='polygon_layout_pixels'} for s in original)
    assert align_layout(plain,1000,1000)[2]['status']=='MEASURED_POLYGONS_UNAVAILABLE'


def test_mixed_or_excessive_skew_does_not_establish_a_global_deskew():
    mixed=raw_spans(skew=5)+raw_spans(skew=-5)
    assert residual_angle(mixed)[0]==0
    assert residual_angle(raw_spans(skew=12))[0]==0


@pytest.mark.parametrize('polygon',[[],[[1,2]]*3,[[10,20],[50,20],[50,40],[False,40]],
    [[10,20],[50,20],[50,40],[0,40]],[[10,20],[50,float('nan')],[50,40],[10,40]],[[10,20]]*4])
def test_invalid_or_inconsistent_measured_quadrilaterals_cannot_be_evidence(polygon):
    item={'text':'Value','pixels':{'x1':10,'x2':50,'y1':20,'y2':40},'polygon_pixels':polygon}
    with pytest.raises(DocumentFailure,match='OCR_RESPONSE_INVALID'):mapped_spans({'spans':[item]},{'derived_dimensions':[100,200]})


def test_exif_backprojection_is_retained_while_virtual_orientation_only_changes_layout():
    item={'text':'Value','pixels':{'x1':10,'x2':50,'y1':20,'y2':40},'polygon_pixels':[[10,20],[50,20],[50,40],[10,40]]}
    actual=mapped_spans({'spans':[item]},{'derived_dimensions':[100,200],'exif_orientation':6})
    transformed=aligned_spans(actual,affine(100,200,90))[0]
    assert transformed['bbox']==pytest.approx({'x1':.1,'x2':.2,'y1':.5,'y2':.9})
    assert transformed['layout_bbox']==pytest.approx({'x1':.8,'x2':.9,'y1':.1,'y2':.5})


def test_separate_side_panel_cannot_contaminate_stacked_header_or_table_cells():
    words=[span('Supplier:',.04,.1,.1),span('Fictional Source Ltd',.04,.14,.25),
        span('Description',.45,.14,.15),span('Qty',.66,.14,.04),span('Unit price',.74,.14,.10),span('Amount',.9,.14,.07),
        span('Invoice number:',.04,.18,.16),span('SIDE-28',.04,.22,.1),
        span('File tags',.45,.22,.15),span('3',.66,.22,.04),span('8.00',.74,.22,.06),span('24.00',.9,.22,.06)]
    headers,rows,notes=printed_layout({'spans':words})
    by={f:v for f,v,_ in headers}
    assert by['vendor_name']=='Fictional Source Ltd' and by['invoice_number']=='SIDE-28'
    assert len(rows)==1 and not notes
    assert {f:v for f,v,_ in rows[0]}['description']=='File tags'


def test_two_unread_cells_keep_measured_description_amount_and_precise_human_questions():
    b,_,_,_=positioned()
    words=[span('Description',.05,.1,.15),span('Qty',.4,.1),span('Unit price',.55,.1,.12),span('Amount',.8,.1,.1),
        span('Blue record labels',.05,.15,.25),span('37.50',.8,.15,.08)]
    detail={'page':1,'native_text':'','spans':words}
    adapter=NativeTextExtractionAdapter([detail]);out=adapter.extract(replace(b,pages=(DocumentPage(1,''),)),SCHEMA_VERSION)
    assert source_table_reviewable(out,adapter.diagnostics)
    fields={f.field_path:f for f in out.line_items[0].fields}
    assert fields['quantity'].state.value==fields['unit_price'].state.value=='MISSING'
    assert fields['quantity'].raw_value is fields['quantity'].bbox is None
    candidate,traces,_=normalized(out)
    assert candidate['lines.0.quantity'] is candidate['lines.0.unit_price'] is None
    from app.documents.normalizer import validate_draft
    questions=[f['message'] for f in validate_draft(candidate,traces,'VENDOR_INVOICE',adapter.diagnostics) if f['code']=='SOURCE_CELL_UNREAD']
    assert len(questions)==2 and all('Blue record labels' in q and 'do not calculate' in q for q in questions)
    # No amount anchor or crossing into another column still cannot establish a row.
    assert not printed_layout({'spans':words[:-1]})[1]
    crossing=words[:-1]+[span('37.50',.65,.15,.3)]
    assert not printed_layout({'spans':crossing})[1]


def test_side_panel_baselines_cannot_steal_table_rows_with_small_residual_skew():
    words=[span('Supplier:',.04,.1,.1),span('Source Ltd',.04,.14,.16),
        span('Description',.45,.14,.15),span('Qty',.66,.14,.04),span('Unit price',.74,.14,.10),span('Amount',.9,.14,.07),
        span('Invoice number:',.04,.18,.16),span('SIDE-28',.04,.22,.1),
        span('File tags',.45,.196,.15),span('3',.66,.195,.04),span('8.00',.74,.19,.06),span('24.00',.9,.189,.06),
        span('Invoice date:',.04,.25,.16),span('2026-10-04',.04,.28,.13),
        span('Paper slips',.45,.27,.15),span('2',.66,.269,.04),span('7.00',.74,.268,.06),span('14.00',.9,.267,.06)]
    h,rows,notes=printed_layout({'spans':words})
    assert dict((f,v) for f,v,_ in h)['invoice_number']=='SIDE-28'
    assert [[v for _,v,_ in row] for row in rows]==[['File tags','3','8.00','24.00'],['Paper slips','2','7.00','14.00']]
    assert not notes


@pytest.mark.parametrize('lower_coverage',[False,True])
def test_aligned_pixel_read_is_bounded_maps_to_original_and_attests_actual_derivative(monkeypatch,tmp_path,lower_coverage):
    import json,threading
    from io import StringIO
    from types import SimpleNamespace
    from app.extraction.cpu_ocr import CPUOCR
    source=tmp_path/'source.png';source.write_bytes(b'Unit source boundary; actual pixel transform is checked by opt-in integration')
    original=raw_spans(rotation=90)
    def wire(spans):
        return {'spans':[{'text':s['text'],'pixels':{k:v*1000 for k,v in s['bbox'].items()},'polygon_pixels':s['polygon_layout_pixels']} for s in spans],'seconds':.4,'memory_peak_kib':100}
    adapter=CPUOCR.__new__(CPUOCR);adapter.root=tmp_path;adapter.lock=threading.RLock();adapter.timeout_seconds=15;adapter.metadata={}
    stream=StringIO();adapter.process=SimpleNamespace(stdin=stream,poll=lambda:None)
    count=[]
    def read(timeout):
        count.append(timeout);request=json.loads(stream.getvalue().splitlines()[-1]);out=wire(original)
        if 'alignment' in request:
            if lower_coverage:
                out['spans']=out['spans'][:8];out['spans'][7]['text']='94.00'
            out['alignment_read']={'source_to_layout':request['alignment'],'image_bytes_transformed':True,'derived_sha256':'a'*64,
                'derived_dimensions':[math.ceil(v) for v in request['alignment']['layout_dimensions']],'pillow_version':'12.3.0'}
        return out
    monkeypatch.setattr(adapter,'_read',read)
    result=adapter.recognize(source,{'derived_dimensions':[1000,1000]})
    requests=[json.loads(line) for line in stream.getvalue().splitlines()]
    assert len(requests)==len(count)==2 and all(0<t<=15 for t in count)
    assert set(requests[0])=={'path'} and set(requests[1])=={'path','alignment'}
    assert source.read_bytes().startswith(b'Unit source boundary')
    assert [s['bbox'] for s in result.spans]==[s['bbox'] for s in original]
    assert adapter.metadata['aligned_pixel_read']['image_bytes_transformed'] is True
    if lower_coverage:
        assert adapter.metadata['alignment_read_disagreements'][0]['first_raw']=='24.00'
        assert adapter.metadata['alignment_read_disagreements'][0]['second_raw']=='94.00'
        assert '94.00' not in [s['text'] for s in result.spans]
    else:assert adapter.metadata['layout_alignment']['refined_from_aligned_pixel_read'] is True


def test_actual_conflicting_ocr_cell_keeps_canonical_unknown_and_skips_model_votes(monkeypatch,tmp_path):
    from uuid import uuid4
    from app.core.identity import Identity
    from app.documents.config import ProviderSettings
    from app.extraction.ocr import OCRPage
    from app.services import document_worker as worker
    b,_,_,pages=positioned();measured=tuple(pages[0]['spans'])
    page=pages[0]|{'native_text':'','spans':[],'route':'VISUAL_REQUIRED','preview_key':'unit-original'}
    box=next(s['bbox'] for s in measured if s['text']=='35.40')
    class OCR:
        metadata={'alignment_read_disagreements':[{'bbox':box,'first_raw':'35.40','second_raw':'85.40'}]}
        def recognize(self,*args):return OCRPage('Actual OCR contract',measured,'UNIT_OCR','unit-v1')
    monkeypatch.setattr(worker,'configured_ocr',lambda *args:OCR())
    identity=Identity(b.tenant_id,b.legal_entity_id,uuid4(),frozenset({'FINANCE_REVIEWER'}),'Unit ambiguity boundary')
    storage=type('Storage',(),{'path':lambda *args:tmp_path/'source.png','get':lambda *args:b'Unit image boundary'})()
    class NeverCall:
        def generate(self,**kwargs):raise AssertionError('A model vote cannot resolve conflicting measured source reads')
    monkeypatch.setattr('app.extraction.typellm.SDKTransport',lambda *args:NeverCall())
    out,_,routing=worker.extract({'id':b.document_id,'source_type':'VENDOR_INVOICE'},identity,[page],storage,
        ProviderSettings(ocr_executable='/unit/ocr',endpoint='http://unit.invalid',model='unit'))
    total=next(f for f in out.header_fields if f.field_path=='total_amount')
    assert total.state.value=='AMBIGUOUS' and total.raw_value=='35.40' and total.source is not None
    assert normalized(out)[0]['total_amount'] is None
    assert 'OCR_ALIGNMENT_READ_DISAGREEMENT' in total.diagnostic_note
    assert 'ENTERPRISE_VLM' not in routing['paths']


def test_conflict_detection_requires_corresponding_source_regions_not_segmentation():
    from app.extraction.orientation import read_disagreements
    a={'text':'10.00','bbox':{'x1':.1,'x2':.2,'y1':.3,'y2':.34}}
    b=a|{'text':'70.00'}
    assert read_disagreements((a,),(b,))[0]['first_raw']=='10.00'
    assert not read_disagreements((a,),(a|{'text':'  10.00  '},))
    assert not read_disagreements((a,),(b|{'bbox':{'x1':.1,'x2':.8,'y1':.3,'y2':.34}},))


@pytest.mark.parametrize('changed',[{'derived_sha256':'fake'},{'image_bytes_transformed':False},{'derived_dimensions':[99,99]},{'source_to_layout':{}},{'pillow_version':'unbounded'}])
def test_pixel_retry_cannot_fabricate_its_transform_attestation(changed):
    from app.extraction.cpu_ocr import alignment_read
    transform=affine(100,200,90)
    value={'source_to_layout':transform,'image_bytes_transformed':True,'derived_sha256':'a'*64,
        'derived_dimensions':[math.ceil(v) for v in transform['layout_dimensions']],'pillow_version':'12.3.0'}
    with pytest.raises(DocumentFailure):alignment_read({'alignment_read':value|changed},transform)
