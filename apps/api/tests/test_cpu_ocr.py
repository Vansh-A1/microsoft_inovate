"""CPU stdio pinning, geometry, configuration and real fallback boundaries."""
from pathlib import Path
import pytest
from app.documents.config import ProviderSettings
from app.documents.processor import DocumentFailure
from app.extraction.cpu_ocr import mapped_spans,validate_handshake,MODEL_HASHES,FallbackOCR,CPUOCR
from app.extraction.ocr import OCRPage


def handshake():return {'ready':True,'models':dict(MODEL_HASHES),'packages':{'rapidocr':'3.9.2','onnxruntime':'1.23.2'},
    'providers':{name:['CPUExecutionProvider'] for name in ('text_det','text_cls','text_rec')}}


def test_exact_model_package_and_actual_cpu_sessions_are_required():
    validate_handshake(handshake())
    for key,value in [('models',{}),('packages',{'rapidocr':'3.9.3'}),('ready',False),('providers',{'text_det':['CUDAExecutionProvider']})]:
        data=handshake();data[key]=value
        with pytest.raises(DocumentFailure):validate_handshake(data)


@pytest.mark.parametrize('settings',[{'ocr_backend':'GPU'},{'ocr_backend':'RAPIDOCR_CPU_EXPERIMENTAL'},
    {'ocr_python':'relative/python'},{'ocr_backend':'RAPIDOCR_CPU_EXPERIMENTAL','ocr_python':'embedded invoice command'}])
def test_ocr_backend_and_interpreter_are_server_configured_and_validated(settings):
    with pytest.raises(ValueError):ProviderSettings(**settings)


def test_measured_cpu_regions_map_exactly_back_through_exif_without_fake_words():
    data={'spans':[{'text':'Total: INR 32.00','pixels':{'x1':10,'x2':50,'y1':20,'y2':40}}]}
    spans=mapped_spans(data,{'derived_dimensions':[100,200],'exif_orientation':6})
    assert spans[0]['layout_bbox']=={'x1':.1,'x2':.5,'y1':.1,'y2':.2}
    assert spans[0]['bbox']==pytest.approx({'x1':.1,'x2':.2,'y1':.5,'y2':.9})
    assert spans[0]['text']=='Total: INR 32.00' and spans[0]['kind']=='line'


@pytest.mark.parametrize('item',[None,[],{'text':'Value','pixels':{'x1':False,'x2':10,'y1':0,'y2':10}},
    {'text':32.0,'pixels':{}},{'text':'Value','pixels':{'x1':0,'x2':101,'y1':0,'y2':10}},
    {'text':'Value','pixels':{'x1':float('nan'),'x2':10,'y1':0,'y2':10}}])
def test_invalid_unbounded_or_nan_geometry_is_not_evidence(item):
    with pytest.raises(DocumentFailure,match='OCR_RESPONSE_INVALID'):mapped_spans({'spans':[item]},{'derived_dimensions':[100,100]})


class Engine:
    version='unit-engine'
    def __init__(self,failure=False):self.failure=failure;self.calls=0;self.metadata={'models':'unit pin contract'}
    def recognize(self,*args):
        self.calls+=1
        if self.failure:raise DocumentFailure('OCR_FAILED')
        return OCRPage('Actual engine output',(),'UNIT_REAL_CONTRACT','unit-engine')


def test_primary_failure_uses_only_real_configured_fallback_and_retains_failure():
    primary=Engine(True);fallback=Engine();adapter=FallbackOCR(primary,fallback)
    out=adapter.recognize(Path('/tmp/unused'),{})
    assert out.provider=='UNIT_REAL_CONTRACT' and primary.calls==fallback.calls==1
    assert adapter.metadata=={'candidate_failure':'OCR_FAILED','fallback':'TESSERACT'}
    with pytest.raises(DocumentFailure,match='OCR_FAILED'):FallbackOCR(primary,None).recognize(Path('/tmp/unused'),{})


def test_fallback_cannot_restart_the_original_time_budget(monkeypatch):
    times=iter((10,25));monkeypatch.setattr('app.extraction.cpu_ocr.time.monotonic',lambda:next(times))
    fallback=Engine();adapter=FallbackOCR(Engine(True),fallback);adapter.timeout_seconds=10
    with pytest.raises(DocumentFailure,match='OCR_TIMEOUT'):adapter.recognize(Path('/tmp/unused'),{})
    assert fallback.calls==0


def test_missing_isolated_interpreter_is_explicit_not_empty_success(tmp_path):
    with pytest.raises(DocumentFailure,match='OCR_NOT_CONFIGURED'):CPUOCR(tmp_path/'unavailable-python',tmp_path)


@pytest.mark.parametrize('payload',["print('[]',flush=True)","print('{}\\n{}',flush=True)",
    "import os,time;os.write(1,b'{');time.sleep(5)"])
def test_actual_stdio_rejects_invalid_json_and_times_out_partial_responses(payload):
    import subprocess,sys,threading,time
    adapter=CPUOCR.__new__(CPUOCR);adapter.lock=threading.RLock()
    adapter.process=subprocess.Popen([sys.executable,'-c',payload],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    started=time.monotonic()
    try:
        with pytest.raises(DocumentFailure):adapter._read(.2)
        assert time.monotonic()-started<2
        assert adapter.process.poll() is not None
        assert adapter.process.stdout.closed
    finally:adapter.close()


def test_valid_cpu_primary_does_not_depend_on_stale_tesseract_paths(monkeypatch,tmp_path):
    from app.services.document_worker import configured_ocr
    from app.extraction import cpu_ocr
    primary=Engine()
    monkeypatch.setattr(cpu_ocr,'resident',lambda *args:primary)
    def unavailable(*args):raise DocumentFailure('OCR_NOT_CONFIGURED')
    monkeypatch.setattr('app.services.document_worker.TesseractOCRAdapter',unavailable)
    providers=ProviderSettings(ocr_backend='RAPIDOCR_CPU_EXPERIMENTAL',ocr_python='/configured/python',ocr_executable='/stale/tesseract')
    adapter=configured_ocr(providers,type('Storage',(),{'root':tmp_path})())
    assert adapter.primary is primary and adapter.fallback is None
    assert adapter.recognize(tmp_path,{}).provider=='UNIT_REAL_CONTRACT'
    with pytest.raises(DocumentFailure,match='OCR_NOT_CONFIGURED'):
        configured_ocr(ProviderSettings(ocr_executable='/stale/tesseract'),None)


def incomplete_table():
    from test_clearledger_layout import span
    return [span('Description',.05,.1,.15),span('Qty',.4,.1),span('Unit price',.55,.1,.12),span('Amount',.8,.1,.1),
            span('Paper wallets',.05,.15,.18),span('17.25',.55,.15,.08),span('17.25',.8,.15,.08)]


def test_missing_single_numeric_cell_routes_bounded_context_crop_not_fake_evidence():
    from app.extraction.layout import table_retry_regions
    words=incomplete_table();regions=table_retry_regions({'spans':words})
    assert len(regions)==1 and regions[0]['field']=='quantity'
    assert regions[0]['crop']['y1']<.15 and regions[0]['crop']['y2']>.17
    assert not table_retry_regions({'spans':words[:-1]})  # two absent columns
    assert not table_retry_regions({'spans':words[4:]})  # no printed heading ownership
    crossing=[dict(s) for s in words];crossing[4]=crossing[4]|{'bbox':{'x1':.05,'x2':.5,'y1':.15,'y2':.17}}
    assert not table_retry_regions({'spans':crossing})


def test_retry_accepts_only_one_measured_cell_and_maps_rotated_original_box():
    from app.extraction.cpu_ocr import missing_cell_read
    from app.extraction.layout import table_retry_regions
    region=table_retry_regions({'spans':incomplete_table()})[0]
    data={'spans':[{'text':'1','pixels':{'x1':41,'x2':43,'y1':15,'y2':17}}]}
    spans=mapped_spans(data,{'derived_dimensions':[100,100],'exif_orientation':6})
    actual=missing_cell_read(spans,region)
    assert actual['text']=='1' and actual['bbox']==pytest.approx({'x1':.15,'x2':.17,'y1':.57,'y2':.59})
    assert missing_cell_read(spans+spans,region) is None
    assert missing_cell_read(tuple(s|{'layout_bbox':{'x1':.2,'x2':.7,'y1':.15,'y2':.17}} for s in spans),region) is None
    assert missing_cell_read(tuple(s|{'layout_bbox':{'x1':.41,'x2':.43,'y1':.3,'y2':.32}} for s in spans),region) is None


@pytest.mark.parametrize('name,value',[('seconds','1.2'),('seconds',float('nan')),('memory_peak_kib',False)])
def test_retry_telemetry_cannot_bypass_bounded_response_validation(name,value):
    data={'spans':[],name:value}
    with pytest.raises(DocumentFailure,match='OCR_RESPONSE_INVALID'):mapped_spans(data,{'derived_dimensions':[100,100]})
