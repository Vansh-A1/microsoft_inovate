import csv,json
from io import BytesIO,StringIO
from uuid import uuid4
from openpyxl import Workbook
from app.core.config import ROOT
from test_document_intake import headers
from test_document_finance import processed,current_report
from test_vertical_slice import payload


def mapped_preview(client,doc,rows,extension='csv'):
    defaults=payload();defaults['source_document_id']=doc['id']
    mapping={'Number':'invoice_number','Total':'total_amount','Document':'source_document_id'}
    if extension=='csv':
        stream=StringIO();writer=csv.writer(stream);writer.writerow(list(mapping));writer.writerows(rows);content=stream.getvalue().encode()
    else:
        book=Workbook();sheet=book.active;sheet.title='Invoices';sheet.append(list(mapping))
        for row in rows:sheet.append(row)
        stream=BytesIO();book.save(stream);content=stream.getvalue()
    return client.post('/api/v1/imports/preview',files={'file':('mapped.'+extension,content)},data={'mapping_json':json.dumps(mapping),'defaults_json':json.dumps(defaults)},headers=headers())


def test_csv_actual_mapping_raw_parsed_cell_evidence_and_unverified_source(environment):
    db,ctx,other,client,cfg=environment;doc=processed(environment)
    r=mapped_preview(client,doc,[['P2-INV-00128','INR 23,600.00',doc['id']],['P2-BAD','=100+200','true']])
    assert r.status_code==201,r.text
    data=r.json();assert data['valid_count']==1 and data['invalid_count']==1
    cell=next(c for c in data['rows'][0]['cells'] if c['column']=='Total')
    assert cell['raw_value']=='INR 23,600.00' and cell['parsed_value']=='23600.00' and cell['validation']['state']=='VALID'
    committed=client.post('/api/v1/imports/'+data['id']+'/commit',headers=headers());assert committed.status_code==200,committed.text
    rid=committed.json()['rows'][0]['transaction_id']
    from app.services.worker import run_once
    assert run_once(db,ctx)
    case=client.get('/api/v1/transactions/'+rid).json();report=client.get('/api/v1/evaluations/'+case['latest_evaluation_id']).json()
    assert report['decision']!='PASS'
    evidence=next(e for rule in report['rules'] for e in rule['evidence'] if (e['reference'].get('import_cell') or {}).get('column')=='Total')
    source=client.get('/api/v1/evidence/'+evidence['id']).json()
    assert source['source']['cell']['raw_value']=='INR 23,600.00' and source['reference']['import_cell']['row']==2
    assert client.get('/api/v1/evidence/'+evidence['id'],headers={'Authorization':'Bearer test-second'}).status_code==404
    assert client.get('/api/v1/transactions/'+rid+'/sources').json()['documents'][0]['verified'] is False


def test_xlsx_formula_and_binary_float_money_are_retained_invalid(environment):
    db,ctx,other,client,cfg=environment;doc=processed(environment)
    r=mapped_preview(client,doc,[['OK','23600.00',doc['id']],['Formula','=SUM(100,200)',doc['id']],['Float',23600.25,doc['id']]],'xlsx')
    assert r.status_code==201,r.text
    data=r.json();assert data['valid_count']==1 and data['invalid_count']==2
    assert any(e['code']=='FORMULA_CELL_REJECTED' for e in data['rows'][1]['errors'])
    assert any(e['code']=='TEXT_CELL_REQUIRED' for e in data['rows'][2]['errors'])
    assert next(c for c in data['rows'][1]['cells'] if c['column']=='Total')['raw_value']=='=SUM(100,200)'


def test_attachment_claim_flag_or_fixture_uuid_is_insufficient(environment):
    db,ctx,other,client,cfg=environment;doc=processed(environment)
    r=mapped_preview(client,doc,[['Flag','23600.00','true'],['Fixture','23600.00',payload()['source_document_id']]])
    assert r.status_code==201,r.text
    assert r.json()['valid_count']==0 and r.json()['invalid_count']==2
    assert all(any(e['code']=='ACTUAL_DOCUMENT_REQUIRED' for e in row['errors']) for row in r.json()['rows'])


def test_mapped_import_missing_column_and_authority_mapping_rejected(environment):
    db,ctx,other,client,cfg=environment
    for mapping in ({'Amount':'risk_score'},{'Missing':'total_amount'}):
        r=client.post('/api/v1/imports/preview',files={'file':('mapped.csv',b'Amount\n10.00\n')},data={'mapping_json':json.dumps(mapping),'defaults_json':json.dumps(payload())},headers=headers())
        assert r.status_code==422,r.text
