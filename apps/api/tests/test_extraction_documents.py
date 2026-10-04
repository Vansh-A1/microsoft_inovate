from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import pytest
from app.core.config import ROOT
from app.documents.config import ProviderSettings
from app.documents.processor import parse, DocumentFailure
from app.documents.normalizer import Normalizer, normalize_money, normalize_date, number_keys, NormalizationError, validate_draft
from app.domain.extraction import DocumentBundle, DocumentPage, DocumentSourceType, SCHEMA_VERSION, to_data, ExtractionObservationState as State
from app.extraction.native import NativeTextExtractionAdapter, HEADER_FIELDS, reconcile
from app.extraction.typellm import TypeLLMExtractionAdapter, questions,RECEIPT_ONLY
from app.extraction.ocr import original_box
from app.documents.normalizer import normalized_value


def extracted(name):
    pages=parse((ROOT/'data/documents_phase2'/name).read_bytes())['pages']
    bundle=DocumentBundle(uuid4(),1,uuid4(),uuid4(),DocumentSourceType.VENDOR_INVOICE,
        tuple(DocumentPage(p['page'],p['native_text'] or None) for p in pages))
    adapter=NativeTextExtractionAdapter(pages)
    return bundle,adapter.extract(bundle,SCHEMA_VERSION),adapter


def normalized(result):
    r=to_data(result)
    obs=[o|{'id':str(uuid4())} for o in r['header_fields']]
    obs += [o|{'id':str(uuid4()),'field_path':f'lines.{row["row_index"]-1}.{o["field_path"]}'} for row in r['line_items'] for o in row['fields']]
    return Normalizer().normalize(obs)


def test_actual_native_header_rows_normalization_and_source():
    bundle,result,adapter=extracted('vendor_multipage.pdf')
    candidate,traces,findings=normalized(result)
    assert candidate['total_amount']=='23600.00' and candidate['lines.1.quantity']=='10'
    assert len(result.line_items)==2 and result.line_items[1].fields[0].page==2
    assert not findings and not validate_draft(candidate,traces,'VENDOR_INVOICE',adapter.diagnostics)
    assert next(f for f in result.header_fields if f.field_path=='total_amount').bbox is not None
    assert candidate['invoice_number']=='P2-INV-00128'


@pytest.mark.parametrize('name,field,expected',[
    ('ambiguous_date.pdf','invoice_date','AMBIGUOUS'),('missing_total.pdf','total_amount','MISSING'),
    ('conflicting_total.pdf','total_amount','AMBIGUOUS'),('uncertain_bundle.pdf','invoice_number','AMBIGUOUS')])
def test_critical_uncertainty_cannot_validate(name,field,expected):
    _,result,adapter=extracted(name);candidate,traces,findings=normalized(result)
    trace=next(t for t in traces if t['field_path']==field)
    assert trace['status']==expected and candidate[field] is None
    assert validate_draft(candidate,traces,'VENDOR_INVOICE',adapter.diagnostics)


def test_embedded_instructions_have_no_extraction_authority():
    _,a,_=extracted('vendor_native.pdf');_,b,_=extracted('untrusted_instructions.pdf')
    assert [(f.field_path,f.raw_value,f.state) for f in a.header_fields]==[(f.field_path,f.raw_value,f.state) for f in b.header_fields]
    assert normalized(b)[0]['total_amount']=='23600.00'


@pytest.mark.parametrize('raw,currency,expected',[('₹1,20,000.00','INR','120000.00'),('INR 118,000.00','INR','118000.00'),('$1,000.50','USD','1000.50'),('(INR 10.25)','INR','-10.25')])
def test_decimal_string_money(raw,currency,expected):assert normalize_money(raw,currency)==expected


@pytest.mark.parametrize('raw,currency',[(120000.0,'INR'),('$120.00',None),('₹100.00','USD'),('1,20.00','INR'),('1e6','INR'),('NaN','INR'),('12,34,56','INR')])
def test_bad_or_ambiguous_money(raw,currency):
    with pytest.raises(NormalizationError):normalize_money(raw,currency)


def test_ambiguous_dates_explicit_locale_and_conservative_keys():
    with pytest.raises(NormalizationError,match='DATE_AMBIGUOUS'):normalize_date('03/04/2026')
    assert normalize_date('03/04/2026','DMY')=='2026-04-03'
    assert normalize_date('03/04/2026','MDY')=='2026-03-04'
    assert number_keys(' inv 00128 ')['candidate']=='INV00128'
    assert number_keys('IO-001')['candidate']=='IO001'


@pytest.mark.parametrize('field,raw',[('lines.0.quantity','INR 20'),('lines.0.tax_rate','18%'),('eligible_nights','₹2')])
def test_dimensionless_values_cannot_be_money_or_guess_percentage(field,raw):
    with pytest.raises(NormalizationError):normalized_value(field,raw,'INR')


def provider_data():
    # This helper's bundle is explicitly VENDOR_INVOICE, including receipt
    # source filenames. A provider answers only the actual question contract.
    return {k:v for f in HEADER_FIELDS if f not in RECEIPT_ONLY for k,v in ((f+'_state','MISSING'),(f+'_raw',None))}


class MockTransport:
    def __init__(self,data):self.data=data;self.calls=[]
    def generate(self,**kwargs):
        self.calls.append(kwargs)
        if isinstance(self.data,Exception):raise self.data
        return SimpleNamespace(result=self.data,thinking={'secret':'not retained'})


def test_typellm_real_generate_contract_string_money_and_null_uncertainty():
    bundle,_,_=extracted('receipt_native.pdf');data=provider_data()|{'total_amount_state':'PRESENT','total_amount_raw':'INR 500.00','invoice_date_state':'PRESENT','invoice_date_raw':None}
    transport=MockTransport(data);adapter=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://shared-inference.example',model='approved-external-model'),transport)
    out=adapter.extract(bundle,SCHEMA_VERSION)
    assert next(f for f in out.header_fields if f.field_path=='total_amount').raw_value=='INR 500.00'
    assert next(f for f in out.header_fields if f.field_path=='invoice_date').state is State.AMBIGUOUS
    q=transport.calls[0]['questions']
    assert q['total_amount_raw']['type']==['string','null'] and all(v['thinking'] is False for v in q.values())
    assert 'secret' not in str(to_data(out)) and adapter.metadata.prompt_template_version
    assert adapter.sidecar['calls']==1


@pytest.mark.parametrize('data',[provider_data()|{'total_amount_state':'PRESENT','total_amount_raw':500.0},provider_data()|{'decision':'PASS'},provider_data()|{'currency_state':'CLEAN'}])
def test_typellm_invalid_responses_rejected(data):
    bundle,_,_=extracted('receipt_native.pdf')
    a=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://service.example',model='external'),MockTransport(data))
    with pytest.raises(DocumentFailure,match='PROVIDER_RESPONSE_INVALID'):a.extract(bundle,SCHEMA_VERSION)


def test_provider_outage_not_empty_success_and_no_implicit_fixture():
    bundle,_,_=extracted('receipt_native.pdf')
    a=TypeLLMExtractionAdapter(ProviderSettings(endpoint='http://service.example',model='external'),MockTransport(TimeoutError()))
    with pytest.raises(DocumentFailure,match='PROVIDER_TIMEOUT') as failure:a.extract(bundle,SCHEMA_VERSION)
    assert failure.value.retryable
    with pytest.raises(DocumentFailure,match='VLM_NOT_CONFIGURED'):TypeLLMExtractionAdapter().extract(bundle,SCHEMA_VERSION)


def test_provider_disagreement_stays_ambiguous():
    bundle,actual,_=extracted('vendor_native.pdf')
    changed=replace(actual,header_fields=tuple(replace(f,raw_value='INR 21,600.00') if f.field_path=='total_amount' else f for f in actual.header_fields))
    out=reconcile(actual,changed)
    f=next(f for f in out.header_fields if f.field_path=='total_amount')
    assert f.state is State.AMBIGUOUS and f.parsed_candidate is None and '21,600' in f.raw_value


@pytest.mark.parametrize('orientation',range(1,9))
def test_exact_exif_inverse_bounds(orientation):
    result=original_box({'x1':.1,'y1':.2,'x2':.3,'y2':.4},orientation)
    assert all(0<=v<=1 for v in result.values()) and result['x1']<result['x2'] and result['y1']<result['y2']
