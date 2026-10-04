"""CPU contracts for the real gateway, uncertainty, routing and measured crops."""
from dataclasses import replace
import importlib.util
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4
import httpx
from fastapi.testclient import TestClient
from PIL import Image,ImageDraw
import pytest
from app.core.config import ROOT
from app.documents.config import ProviderSettings
from app.documents.processor import DocumentFailure
from app.domain.extraction import FieldObservation,ExtractionObservationState as State,VersionMetadata
from app.extraction.gateway import GatewayTransport
from app.extraction.grid import row_crops
from app.extraction.native import reconcile
from test_extraction_documents import extracted,provider_data,MockTransport
from app.extraction.typellm import TypeLLMExtractionAdapter
from app.db.models import Base
from app.services.document_worker import mapping_gaps

spec=importlib.util.spec_from_file_location('local_typellm_gateway',ROOT/'scripts/inference/typellm_gateway.py')
gateway=importlib.util.module_from_spec(spec);spec.loader.exec_module(gateway)
TOKEN='isolated-unit-test-authorization-value'
META={'served_model':'test-model','typellm':'0.5.1','model_revision':'a'*40,'bridge':'sglang-cu124-transport-v1'}


def test_gateway_transport_has_no_sdk_gpu_dependency_and_checks_model_pin(monkeypatch):
    monkeypatch.setenv('AP_TYPELLM_GATEWAY_TOKEN',TOKEN)
    config=ProviderSettings(endpoint='http://gateway.example',model='test-model',transport='TYPELLM_GATEWAY',model_revision='a'*40)
    transport=GatewayTransport(config);calls=[]
    def post(url,**kw):
        calls.append(kw)
        return httpx.Response(200,json={'result':{'total_raw':'INR 12.50'},'provider_metadata':META})
    monkeypatch.setattr(httpx,'post',post)
    out=transport.generate(context='untrusted document',questions={'total_raw':{}},images=None,timeout=10)
    assert out.result['total_raw']=='INR 12.50' and transport.provider_metadata==META
    assert calls[0]['headers']['Authorization']=='Bearer '+TOKEN
    monkeypatch.setattr(httpx,'post',lambda *a,**kw:httpx.Response(200,json={'result':{},'provider_metadata':META|{'model_revision':'b'*40}}))
    with pytest.raises(DocumentFailure,match='PROVIDER_RESPONSE_INVALID'):transport.generate(context='',questions={},images=None,timeout=10)


@pytest.mark.parametrize('status,code,retryable',[(401,'GATEWAY_AUTH_FAILED',False),(503,'PROVIDER_UNAVAILABLE',True),(504,'PROVIDER_TIMEOUT',True),(422,'PROVIDER_RESPONSE_INVALID',False)])
def test_gateway_http_failures_are_explicit(monkeypatch,status,code,retryable):
    monkeypatch.setenv('AP_TYPELLM_GATEWAY_TOKEN',TOKEN)
    monkeypatch.setattr(httpx,'post',lambda *a,**kw:httpx.Response(status,json={'detail':'secret provider payload must not be surfaced'}))
    with pytest.raises(DocumentFailure,match=code) as error:GatewayTransport(ProviderSettings(endpoint='http://gateway.example',model='test-model',transport='TYPELLM_GATEWAY')).generate(context='',questions={},images=None,timeout=10)
    assert error.value.retryable is retryable and 'secret' not in str(error.value)


def test_gateway_missing_secret_does_not_make_a_request(monkeypatch):
    monkeypatch.delenv('AP_TYPELLM_GATEWAY_TOKEN',raising=False)
    monkeypatch.setattr(httpx,'post',lambda *a,**kw:pytest.fail('Missing authentication must fail before network'))
    with pytest.raises(DocumentFailure,match='GATEWAY_AUTH_NOT_CONFIGURED'):GatewayTransport(ProviderSettings(endpoint='http://gateway.example',model='test-model',transport='TYPELLM_GATEWAY')).generate(context='',questions={},images=None,timeout=10)


def test_legacy_bridge_preserves_grammars_candidate_ids_and_batch_order():
    payload={'text':['first','second'],'sampling_params':[{'temperature':0,'sampling_seed':2,'regex':'money-string'},{'temperature':0,'sampling_seed':3}],
        'return_logprob':True,'token_ids_logprob':[[32,33],[34,35]]}
    items,batch=gateway.single_payloads(gateway.legacy_payload(payload))
    assert batch and [p['text'] for p in items]==['first','second']
    assert items[0]['sampling_params']=={'temperature':0,'regex':'money-string'} and items[1]['token_ids_logprob']==[34,35]
    assert items[0]['return_logprob'] and 'sampling_seed' in payload['sampling_params'][0]
    with pytest.raises(ValueError):gateway.legacy_payload({'sampling_params':{'temperature':.1,'sampling_seed':1}})


class Backend:
    def __init__(self,flush_ok=True):self.calls=[];self.flush_ok=flush_ok
    def get(self,path):
        self.calls.append(path)
        request=httpx.Request('GET','http://backend.example'+path)
        if path=='/flush_cache':return httpx.Response(200 if self.flush_ok else 400,text='Cache flushed.' if self.flush_ok else 'Busy',request=request)
        if path=='/get_model_info':return httpx.Response(200,json={'model_path':'/tmp/test-model'},request=request)
        return httpx.Response(200,json={},request=request)


def gateway_client(backend=None,engine=None):
    backend=backend or Backend();engine=engine or MockTransport({'total_raw':'12.50'})
    config={'served_model':'test-model','sglang_endpoint':'http://backend.example','model_path':'/tmp/test-model','gpu_status':'AVAILABLE','provider_metadata':META|{'model_source':'synthetic-test-model','precision':'BF16'}}
    return TestClient(gateway.create_app(config,TOKEN,engine,backend)),backend,engine


def body():return {'model':'test-model','context':'untrusted input','questions':{'total_raw':{'type':['string','null'],'instructions':'Copy printed amount','thinking':False}},'images':None,'timeout':10}


def test_gateway_auth_string_schema_and_cache_isolation():
    client,backend,engine=gateway_client()
    assert client.post('/generate',json=body()).status_code==401
    client.headers['Authorization']='Bearer '+TOKEN
    response=client.post('/generate',json=body());assert response.status_code==200,response.text
    assert response.json()['result']=={'total_raw':'12.50'}
    assert backend.calls==['/flush_cache','/flush_cache']
    assert 'thinking' not in response.text and len(engine.calls)==1
    assert client.get('/health').json()['status']=='AVAILABLE'
    bad=body();bad['questions']['total_raw']['type']='number'
    assert client.post('/generate',json=bad).status_code==422
    bad=body();bad['images']=['https://untrusted.example/private']
    assert client.post('/generate',json=bad).status_code==422


def test_gateway_fail_closed_when_cache_cannot_be_isolated():
    client,backend,engine=gateway_client(Backend(False));client.headers['Authorization']='Bearer '+TOKEN
    assert client.post('/generate',json=body()).status_code==503
    backend.flush_ok=True
    assert client.post('/generate',json=body()).status_code==503
    assert not engine.calls and client.get('/health').status_code==503


def test_gateway_provider_only_status_names_remap_back_to_application():
    engine=MockTransport({'total_raw':'12.50','total_observation_status':'PRESENT'})
    client,backend,_=gateway_client(engine=engine);client.headers['Authorization']='Bearer '+TOKEN
    data=body();data['questions']['total_state']={'type':'string','enum':[s.value for s in State],'depends_on':['total_raw'],'instructions':'Observation condition','thinking':False}
    response=client.post('/generate',json=data)
    assert response.status_code==200,response.text
    assert response.json()['result']['total_state']=='PRESENT' and 'total_observation_status' in engine.calls[0]['questions']


def test_provider_contradiction_preserved_as_ambiguity():
    bundle,_,_=extracted('receipt_native.pdf')
    data=provider_data()|{'total_amount_state':'MISSING','total_amount_raw':'INR 500.00'}
    result=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://shared.example',model='test-model'),MockTransport(data)).extract(bundle,'extraction-v1')
    field=next(f for f in result.header_fields if f.field_path=='total_amount')
    assert field.state is State.AMBIGUOUS and field.raw_value=='INR 500.00' and field.bbox is None


def test_complete_native_stays_cheap_but_high_text_coverage_missing_rows_escalates():
    bundle,result,_=extracted('vendor_native.pdf')
    assert not mapping_gaps(result,'VENDOR_INVOICE')
    assert mapping_gaps(replace(result,line_items=()),'VENDOR_INVOICE')==['LINE_ITEMS_NOT_MAPPED']
    changed=replace(result,header_fields=tuple(replace(f,state=State.AMBIGUOUS) if f.field_path=='currency' else f for f in result.header_fields))
    assert 'currency' in mapping_gaps(changed,'VENDOR_INVOICE')


def test_visual_additional_address_observation_survives_reconciliation():
    bundle,primary,_=extracted('vendor_native.pdf')
    other=replace(primary,header_fields=primary.header_fields+(FieldObservation('vendor_address',State.PRESENT,'Visible synthetic address',source=primary.header_fields[0].source),))
    combined=reconcile(primary,other)
    assert next(f for f in combined.header_fields if f.field_path=='vendor_address').raw_value=='Visible synthetic address'


@pytest.mark.parametrize('state',[State.AMBIGUOUS,State.ILLEGIBLE,State.NOT_APPLICABLE])
def test_empty_native_mapping_preserves_visual_uncertainty_and_source(state):
    _,primary,_=extracted('vendor_native.pdf')
    empty=replace(primary,header_fields=tuple(FieldObservation(f.field_path,State.MISSING) for f in primary.header_fields),
        line_items=tuple(replace(row,fields=tuple(FieldObservation(f.field_path,State.MISSING) for f in row.fields)) for row in primary.line_items))
    other=replace(primary,header_fields=tuple(replace(f,state=state,raw_value='uncertain printed value') for f in primary.header_fields),
        line_items=tuple(replace(row,fields=tuple(replace(f,state=state,raw_value='uncertain printed row') for f in row.fields)) for row in primary.line_items))
    merged=reconcile(empty,other)
    assert merged.header_fields==other.header_fields
    assert merged.line_items==other.line_items


def test_row_count_disagreement_retains_larger_candidate_set_as_ambiguous():
    _,primary,_=extracted('vendor_multipage.pdf')
    incomplete=replace(primary,line_items=primary.line_items[:1])
    merged=reconcile(incomplete,primary)
    assert len(merged.line_items)==2
    assert all(f.state is State.AMBIGUOUS and f.diagnostic_note.startswith('ROW_ASSOCIATION_UNCONFIRMED:') for row in merged.line_items for f in row.fields if f.raw_value is not None)
    missing={(row.row_index,f.field_path):f for row in primary.line_items for f in row.fields if f.state is State.MISSING}
    assert all(f.state is State.MISSING and f.raw_value is None and f.source==missing[(row.row_index,f.field_path)].source
        for row in merged.line_items for f in row.fields if (row.row_index,f.field_path) in missing)
    assert merged.line_items[1].fields[0].source==primary.line_items[1].fields[0].source


@pytest.mark.parametrize('field,value',[('quantity','INR 20'),('tax_rate','INR 0.18')])
def test_reconciliation_does_not_treat_currency_as_a_quantity_or_rate(field,value):
    _,primary,_=extracted('vendor_native.pdf')
    other=replace(primary,line_items=tuple(replace(row,fields=tuple(replace(f,raw_value=value) if f.field_path==field else f for f in row.fields)) for row in primary.line_items))
    merged=reconcile(primary,other)
    assert next(f for f in merged.line_items[0].fields if f.field_path==field).state is State.AMBIGUOUS


def test_visual_printed_row_amount_uses_the_decimal_normalizer():
    from app.documents.normalizer import normalized_value,NORMALIZER_VERSION
    assert normalized_value('lines.0.amount','INR 1,234.50','INR')[0]=='1234.50'
    assert NORMALIZER_VERSION=='document-normalizer-v4'


@pytest.mark.parametrize('raw,currency',[('100.00',None),(100.0,'INR')])
def test_visual_row_amount_cannot_normalize_without_currency_or_from_float(raw,currency):
    from app.documents.normalizer import normalized_value,NormalizationError
    with pytest.raises(NormalizationError):normalized_value('lines.0.amount',raw,currency)


def test_measured_grid_crops_map_header_and_row_without_field_boxes():
    image=Image.new('RGB',(800,600),'white');draw=ImageDraw.Draw(image)
    for y in (100,140,180,220):draw.line((60,y,740,y),fill='gray',width=1)
    draw.text((70,115),'QTY DESCRIPTION UNIT PRICE AMOUNT',fill='black')
    output=BytesIO();image.save(output,format='PNG')
    crops=row_crops(output.getvalue())
    assert len(crops)==2
    for content,trace in crops:
        assert trace['field_bbox'] is None and trace['preview_dimensions']==[800,600]
        assert trace['header_extent_pixels']==[60,100,741,141]
        assert len(trace['sha256'])==64 and content.startswith(b'\x89PNG')
    blank=BytesIO();Image.new('RGB',(800,600),'white').save(blank,format='PNG')
    assert row_crops(blank.getvalue())==[]


@pytest.mark.parametrize('settings',[{'transport':'UNSUPPORTED'},{'gateway_token_env':'secret/path'},{'model_revision':'not-pinned'}])
def test_invalid_provider_settings_rejected(settings):
    with pytest.raises(ValueError):ProviderSettings(**settings)


def test_reconciliation_compares_money_formats_only_with_agreed_currency():
    bundle,primary,_=extracted('vendor_native.pdf')
    other=replace(primary,header_fields=tuple(replace(f,raw_value='23600.00') if f.field_path=='total_amount' else f for f in primary.header_fields),
        line_items=tuple(replace(row,fields=row.fields+(FieldObservation('amount',State.PRESENT,'23600.00',source=row.fields[0].source),)) for row in primary.line_items))
    merged=reconcile(primary,other)
    total=next(f for f in merged.header_fields if f.field_path=='total_amount')
    assert total.state is State.PRESENT and total.raw_value=='INR 23,600.00' and 'alternate provider literal' in total.diagnostic_note
    assert all(f.state is State.PRESENT for f in merged.line_items[0].fields)
    assert len(merged.line_items[0].fields)==10
    different=replace(other,header_fields=tuple(replace(f,raw_value='USD') if f.field_path=='currency' else f for f in other.header_fields))
    conflict=reconcile(primary,different)
    assert next(f for f in conflict.header_fields if f.field_path=='total_amount').state is State.AMBIGUOUS


def test_visual_receipt_without_table_candidates_has_bounded_header_only_queries():
    from app.domain.extraction import DocumentSourceType
    bundle,_,_=extracted('receipt_native.pdf')
    bundle=replace(bundle,source_type=DocumentSourceType.EMPLOYEE_RECEIPT)
    class HeaderTransport:
        def __init__(self):self.calls=[]
        def generate(self,**kw):
            self.calls.append(kw)
            return SimpleNamespace(result={key:('MISSING' if key.endswith('_state') else None) for key in kw['questions']})
    transport=HeaderTransport()
    result=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://shared.example',model='test-model'),transport,
        image_loader=lambda p:'data:image/png;base64,opaque-test-image').extract(bundle,'extraction-v1')
    assert len(transport.calls)==1 and not result.line_items


def test_visual_row_discovery_does_not_trust_partial_ocr_pipe_candidates():
    bundle,_,_=extracted('vendor_native.pdf')
    class VisualTransport:
        def __init__(self):self.calls=[]
        def generate(self,**kw):
            self.calls.append(kw)
            if 'row_count_raw' in kw['questions']:
                return SimpleNamespace(result={'row_count_raw':'3','row_count_state':'PRESENT'})
            return SimpleNamespace(result={k:('MISSING' if k.endswith('_state') else None) for k in kw['questions']})
    transport=VisualTransport()
    result=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://service.example',model='test-model'),transport,
        image_loader=lambda p:'data:image/png;base64,opaque-test-image').extract(bundle,'extraction-v1')
    assert len(result.line_items)==3 and len(transport.calls)==5
    assert 'row_count_raw' in transport.calls[1]['questions']
