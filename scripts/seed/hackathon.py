#!/usr/bin/env python3
"""Persist a separate synthetic demo scope; compute outcomes through real APIs."""
import argparse
import base64
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time
from uuid import UUID,uuid5

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'apps/api'),str(ROOT/'scripts/seed'),str(ROOT/'scripts')]
from app.core.config import Settings
from app.core.identity import Identity
from app.db.session import Database
from app.services.references import seed_references
from app.services.reference_imports import active_records,stage,validate,activate
from app.schemas.canonical import fixture_canonical
from phase3 import entries
from demo import private_json

NS=UUID('bc7f9d92-a35c-4de2-9c15-aa4805f58f54')
RUNTIME=ROOT/'runtime/demo'
MANIFEST=RUNTIME/'scenarios.json'
TENANT=str(uuid5(NS,'10000000-0000-4000-8000-000000000001'))
ENTITY=str(uuid5(NS,'20000000-0000-4000-8000-000000000001'))
def partial_id(name):return str(uuid5(NS,'independent-partial-'+name))

def partial_references():
    """Separate synthetic capacity so a preceding PASS cannot consume this case."""
    def first(kind):return remap(json.loads((ROOT/f'data/synthetic/reference/{kind}.json').read_text())['records'][0])
    budget=first('budgets');budget.update(id=partial_id('budget'),code='HACKATHON-PARTIAL-BUDGET')
    allocation=deepcopy(budget['ledger'][0]);allocation['id']=partial_id('allocation');budget['ledger']=[allocation]
    po=first('purchase_orders');line=po.pop('lines')[0]
    po.update(id=partial_id('po'),display_number='HACKATHON-PO-PARTIAL',budget_id=budget['id'])
    line.update(id=partial_id('po-line'),po_id=po['id'],budget_id=budget['id'])
    receipt=first('goods_receipts');received=receipt.pop('lines')[0]
    receipt.update(id=partial_id('grn'),display_number='HACKATHON-GRN-PARTIAL',po_id=po['id'])
    received.update(id=partial_id('grn-line'),goods_receipt_id=receipt['id'],po_id=po['id'],po_line_id=line['id'],
        received_quantity='50.0000',accepted_quantity='50.0000',returned_quantity='0.0000',reversed_quantity='0.0000')
    return [{'kind':kind,'payload':record} for kind,record in [('budgets',budget),('purchase_orders',po),('po_lines',line),('goods_receipts',receipt),('grn_lines',received)]]
LABELS={
 'reviewer':('Hackathon finance reviewer','51000000-0000-4000-8000-000000000001',['FINANCE_REVIEWER','FINANCE_SUBMITTER','DUPLICATE_REVIEWER','RECEIPT_ALLOCATOR','REPORT_EXPORTER']),
 'manager':('Hackathon manager','51000000-0000-4000-8000-000000000003',['MANAGER','FINANCE_REVIEWER']),
 'head':('Hackathon department head','51000000-0000-4000-8000-000000000004',['DEPARTMENT_HEAD','FINANCE_REVIEWER']),
 'auditor':('Hackathon auditor','51000000-0000-4000-8000-000000000005',['AUDITOR','REPORT_EXPORTER']),
 'operations':('Hackathon operations','51000000-0000-4000-8000-000000000006',['OPERATIONS_ADMIN','OPERATIONS_READER']),
}


def remap(value):
    if isinstance(value,dict):return {k:remap(v) for k,v in value.items()}
    if isinstance(value,list):return [remap(v) for v in value]
    if isinstance(value,str):
        try:return str(uuid5(NS,str(UUID(value))))
        except ValueError:return value
    return value


def visual_invoice():
    """Actual synthetic source with a ruled table, not parser-ready pipe rows.

    The document contains facts; no expected extraction response is supplied to
    the provider. This layout exercises visual relationships conservatively.
    """
    from io import BytesIO
    from reportlab.pdfgen import canvas
    import pymupdf
    from document_fixtures import HEADER
    output=BytesIO();c=canvas.Canvas(output,pagesize=(612,792),invariant=1)
    c.setTitle('SYNTHETIC HACKATHON INVOICE');c.setFont('Helvetica-Bold',17)
    c.drawString(38,750,'SYNTHETIC DEMO INVOICE')
    c.setFont('Helvetica',9);c.drawString(38,730,'Fictional supplier and amounts. No payment execution.')
    for index,text in enumerate(HEADER):
        c.setFont('Helvetica',11);c.drawString(38,700-index*22,text)
    widths=[110,35,58,49,63,47,61,70,43];x=[38]
    for width in widths:x.append(x[-1]+width)
    headers=['Description','Qty','Unit price','Discount','Net','Tax rate','Tax','Gross','UOM']
    values=['Widgets','20','1000.00','0.00','20000.00','0.18','3600.00','23600.00','EA']
    for y in [340,310,280]:c.line(x[0],y,x[-1],y)
    for point in x:c.line(point,280,point,340)
    for row,y in [(headers,320),(values,291)]:
        c.setFont('Helvetica',8)
        for i,value in enumerate(row):c.drawString(x[i]+3,y,value)
    c.setFont('Helvetica',10);c.drawString(38,250,'Tax is exclusive; all amounts are in INR.')
    c.drawString(38,35,'SYNTHETIC - Page 1 of 1');c.save()
    with pymupdf.open(stream=output.getvalue(),filetype='pdf') as pdf:
        return pdf[0].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).tobytes('png')


def prepare():
    settings=Settings.load()
    if not settings.development:raise RuntimeError('Hackathon data requires development mode')
    path=ROOT/'runtime/dev/settings.json';data=json.loads(path.read_text())
    for _,(label,actor,roles) in LABELS.items():
        expected={'tenant_id':TENANT,'legal_entity_id':ENTITY,'actor_id':remap(actor),'roles':roles,'label':label}
        existing=next((i for i in data['identities'].values() if i['label']==label),None)
        if existing is not None and existing!=expected:raise RuntimeError('Existing hackathon identity differs; no automatic role change')
        if existing is None:data['identities'][secrets.token_urlsafe(32)]=expected
    private_json(path,data)
    for branch,name in [('vendor','vendor/clean'),('employee','employee/clean_taxi')]:
        raw=json.loads((ROOT/f'data/golden_cases/{name}.json').read_text())['transaction']
        private_json(RUNTIME/'templates'/f'{branch}.json',{'tenant_id':TENANT,'legal_entity_id':ENTITY,'transaction':remap(fixture_canonical(raw))})
    folder=RUNTIME/'reference';folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    for file in (ROOT/'data/synthetic/reference').glob('*.json'):
        private_json(folder/file.name,remap(json.loads(file.read_text())))
    reviewer=LABELS['reviewer']
    ctx=Identity(UUID(TENANT),UUID(ENTITY),UUID(remap(reviewer[1])),frozenset(reviewer[2])|{'DEVELOPMENT_ADMIN','REFERENCE_ADMIN'},'Hackathon synthetic bootstrap')
    db=Database(settings.database_url);db.settings=settings
    try:
        with db.session(ctx) as session:
            seed_references(session,ctx,source_root=folder)
            if not any(r.kind=='finance_profiles' for r in active_records(session,ctx).values()):
                batch=stage(session,ctx,{'source_system':'HACKATHON_SYNTHETIC','source_version':'hackathon-v1','records':remap(entries()),'reason':'Separate synthetic hackathon finance catalog; no company-policy claim'},'hackathon-prepare')
                checked=validate(session,ctx,UUID(batch['id']),'hackathon-prepare')
                if checked['state']!='VALID':raise RuntimeError('Hackathon catalog validation failed')
                activate(session,ctx,UUID(batch['id']),'Explicit synthetic hackathon reference version','hackathon-prepare')
            if partial_id('po') not in active_records(session,ctx):
                batch=stage(session,ctx,{'source_system':'HACKATHON_SYNTHETIC','source_version':'partial-capacity-v1','records':partial_references(),'reason':'Independent fictional 100 ordered / 50 accepted capacity; preceding scenarios must not consume it'},'hackathon-partial')
                checked=validate(session,ctx,UUID(batch['id']),'hackathon-partial')
                if checked['state']!='VALID':raise RuntimeError('Independent partial reference validation failed')
                activate(session,ctx,UUID(batch['id']),'Independent synthetic partial-delivery references','hackathon-partial')
    finally:db.engine.dispose()
    print('Hackathon synthetic scope prepared. Existing scopes, roles, evidence and evaluations preserved; no credentials printed.')


class Runner:
    def __init__(self):
        import httpx
        settings=Settings.load()
        if not settings.development:raise RuntimeError('Loopback synthetic demo only')
        self.tokens={kind:next(k for k,v in settings.identities.items() if v['label']==label) for kind,(label,_,_) in LABELS.items()}
        self.http=httpx.Client(base_url='http://127.0.0.1:8000/api/v1/',timeout=180)
        self.saved=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {'version':'hackathon-demo-v1','synthetic':True,'tenant_id':TENANT,'legal_entity_id':ENTITY,'steps':{},'scenarios':[]}

    def request(self,method,path,body=None,*,key=None,actor='reviewer',content=None):
        headers={'Authorization':'Bearer '+self.tokens[actor]}
        if key:headers['Idempotency-Key']='hackathon-v1:'+key
        if content is not None:headers['Content-Type']='application/octet-stream'
        response=self.http.request(method,path,headers=headers,json=body,content=content)
        if not response.is_success:
            # Store safe code only; no response/source body/token/traceback logs.
            try:code=response.json()['error']['code']
            except Exception:code='HTTP_'+str(response.status_code)
            raise RuntimeError('Demo action failed: '+path+' / '+code)
        return response.json()

    def checkpoint(self):private_json(MANIFEST,self.saved)

    def once(self,name,fn):
        if name not in self.saved['steps']:
            self.saved['steps'][name]=fn();self.checkpoint()
        return self.saved['steps'][name]

    def facts(self,name):
        raw=json.loads((ROOT/f'data/golden_cases/{name}.json').read_text())['transaction']
        return remap(fixture_canonical(raw))

    def report(self,tid,version=1):
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            detail=self.request('GET','transactions/'+tid)
            if detail['processing_state']=='COMPLETED' and detail['version']==version:
                report=self.request('GET','evaluations/'+detail['latest_evaluation_id'])
                if report['transaction_version']==version:return report
            if detail['processing_state'] in ('FAILED_FINAL','FAILED_RETRYABLE'):raise RuntimeError('Finance demo job failed explicitly')
            time.sleep(.25)
        raise RuntimeError('Finance demo evaluation timeout')

    def approve(self,tid,version=1):
        request=self.once(f'approval-request:{tid}:{version}',lambda:self.request('POST',f'transactions/{tid}/approval-requests',{'expected_version':version,'reason':'Independent synthetic hackathon approval chain'},key=f'approval-request:{tid}:{version}'))
        for step in request['requirements']:
            actor={'MANAGER':'manager','DEPARTMENT_HEAD':'head'}.get(step['role'])
            if not actor:raise RuntimeError('Demo requires an unexpected authority; do not fake approval')
            self.once(f'approve:{tid}:{version}:{step["sequence"]}',lambda step=step,actor=actor:self.request('POST','approval-requests/'+request['id']+'/actions',{'expected_version':version,'sequence':step['sequence'],'action':'APPROVED','reason':'Authorized independent synthetic source and finance review'},key=f'approve:{tid}:{version}:{step["sequence"]}',actor=actor))
        return self.report(tid,version)

    def structured(self,name):
        created=self.once('create:'+name,lambda:self.request('POST','transactions',self.facts(name),key='create:'+name))
        return created['id'],self.approve(created['id'])

    def scenario(self,key,label,report,expected,extra=None):
        if report['decision']!=expected:raise RuntimeError('Computed demo outcome differs for '+key+': '+report['decision'])
        row={'key':key,'label':label,'transaction_id':report['transaction_id'],'evaluation_id':report['evaluation_id'],
            'transaction_version':report['transaction_version'],'decision':report['decision'],'case_url':'/cases/'+report['transaction_id'],
            'report_url':'/reports/'+report['evaluation_id'],'evidence':[r['rule_id'] for r in report['rules'] if r['decision_effect']!='NONE'],**(extra or {})}
        self.saved['scenarios']=[r for r in self.saved['scenarios'] if r['key']!=key]+[row];self.checkpoint()

    def vlm_document(self):
        image=visual_invoice()
        upload=self.once('vlm-layout-upload-v2',lambda:self.request('POST','uploads',{'filename':'Hackathon visual-table invoice.png','mime':'image/png','source_type':'VENDOR_INVOICE'},key='vlm-layout-upload-v2'))
        doc=self.request('GET','documents/'+upload['document_id'])
        if doc['state']=='AWAITING_UPLOAD':self.request('POST',upload['bytes_url'].replace('/api/v1/',''),content=image)
        doc=self.request('GET','documents/'+upload['document_id'])
        if doc['state']=='UPLOADED':self.request('POST','uploads/'+upload['id']+'/finalize',{},key='vlm-layout-finalize-v2')
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            doc=self.request('GET','documents/'+upload['document_id'])
            if doc['state'] in ('READY','NEEDS_INPUT'):break
            if doc['state'] in ('FAILED_FINAL','FAILED_RETRYABLE','QUARANTINED','DEPENDENCY_UNAVAILABLE'):raise RuntimeError('Actual VLM demo document is incomplete: '+doc['state'])
            time.sleep(.5)
        else:raise RuntimeError('Actual VLM demo document timed out')
        if doc['original']['sha256']!=hashlib.sha256(image).hexdigest():raise RuntimeError('Original image integrity mismatch')
        run=next(r for r in doc['extraction_runs'] if r['status'] in ('COMPLETED','PARTIAL'))
        metadata=run['metadata'];versions={v['name']:v['version'] for v in metadata['runtime_versions']}
        if metadata['provider_id']!='ENTERPRISE_VLM' or versions.get('model_revision')!='66285546d2b821cf421d4f5eb2576359d3770cd3':
            raise RuntimeError('Real VLM acceptance cannot use native/fixture fallback')
        # Independent source inspection occurs AFTER real generation, never in
        # prompts. This actual preserved synthetic page prints these row facts.
        printed={'description':'Widgets','quantity':'20','unit_price':'1000.00','discount_amount':'0.00','net_amount':'20000.00','tax_rate':'0.18','tax_amount':'3600.00','gross_amount':'23600.00','uom':'EA'}
        corrections=[{'field_path':'lines.0.'+k,'value':v,'page':1,'reason':'Demo reviewer verified the exact literal in the preserved synthetic source'} for k,v in printed.items() if doc['draft']['candidate'].get('lines.0.'+k)!=v]
        body={'draft_id':doc['draft']['id'],'transaction':self.facts('vendor/clean'),'source_confirmed':True,'reason':'Actual VLM extraction, explicit source review and selection of existing synthetic PO/GRN references','corrections':corrections}
        created=self.once('vlm-commit',lambda:self.request('POST','documents/'+doc['id']+'/commit',body,key='vlm-commit'))
        first=self.once('vlm-pass',lambda:self.approve(created['id']))
        self.scenario('vlm-pass','Actual image → VLM/TypeLLM → source verification → PO/GRN → PASS',first,'PASS',{'document_id':doc['id'],'document_url':'/documents/'+doc['id'],'provider':'ENTERPRISE_VLM','extraction_run':run['id'],'source_corrections':len(corrections)})
        return doc,created,body

    def partial_document(self):
        from document_fixtures import HEADER,TABLE,pdf
        from decimal import Decimal
        facts=self.facts('vendor/partial_grn')
        facts.update(invoice_number='HACKATHON-PARTIAL-001',po_id=partial_id('po'),budget_id=partial_id('budget'))
        facts['lines'][0].update(po_line_id=partial_id('po-line'),grn_line_id=partial_id('grn-line'))
        changes={'Invoice number':'HACKATHON-PARTIAL-001','PO reference':'HACKATHON-PO-PARTIAL',
            'Subtotal':'INR 70,000.00','Tax':'INR 12,600.00','Total':'INR 82,600.00'}
        headers=[line.split(':',1)[0]+': '+changes[line.split(':',1)[0]] if line.split(':',1)[0] in changes else line for line in HEADER]
        content=pdf([headers+[TABLE,'Widgets | 70 | 1000.00 | 0.00 | 70000.00 | 0.18 | 12600.00 | 82600.00 | EA']])
        upload=self.once('independent-partial-upload',lambda:self.request('POST','uploads',{'filename':'Independent 50-unit delivery.pdf','mime':'application/pdf','source_type':'VENDOR_INVOICE'},key='independent-partial-upload'))
        doc=self.request('GET','documents/'+upload['document_id'])
        if doc['state']=='AWAITING_UPLOAD':self.request('POST',upload['bytes_url'].replace('/api/v1/',''),content=content)
        if self.request('GET','documents/'+upload['document_id'])['state']=='UPLOADED':self.request('POST','uploads/'+upload['id']+'/finalize',{},key='independent-partial-finalize')
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            doc=self.request('GET','documents/'+upload['document_id'])
            if doc['state']=='READY':break
            time.sleep(.25)
        else:raise RuntimeError('Independent partial native document did not become READY')
        created=self.once('independent-partial-commit',lambda:self.request('POST','documents/'+doc['id']+'/commit',{'draft_id':doc['draft']['id'],'transaction':facts,'source_confirmed':True,'corrections':[],'reason':'Verify the printed 70-unit invoice against the independently approved 100-unit order and 50-unit accepted receipt'},key='independent-partial-commit'))
        result=self.approve(created['id'])
        observed=next(r for r in result['rules'] if r['rule_id']=='GRN-001')['observed']
        if len(observed)!=1 or Decimal(observed[0]['eligible_new_quantity'])!=50 or Decimal(observed[0]['quantity_shortfall'])!=20:
            raise RuntimeError('Partial demo must preserve exactly 50 available and a 20-unit shortfall')
        self.scenario('partial-delivery','Ordered 100; available 50; billed 70',result,'HOLD',{'quantity_evidence':observed,'document_id':doc['id'],'document_url':'/documents/'+doc['id']})

    def run(self):
        doc,created,body=self.vlm_document()
        for key,name,label,decision in [
            ('paid-duplicate','vendor/paid_duplicate','Repeated paid obligation','HOLD'),
            ('employee-clean','employee/clean_taxi','Clean employee expense','PASS'),
            ('employee-allowance','employee/daily_meals','Daily allowance exceeded','REVIEW'),
        ]:
            tid,result=self.structured(name)
            self.scenario(key,label,result,decision)
        self.partial_document()
        shared=self.once('shared-create',lambda:self.request('POST','transactions',self.facts('employee/shared_within'),key='shared-create'))
        detail=self.request('GET','transactions/'+shared['id']);item=detail['versions'][0]['payload']['items'][0]
        self.once('shared-resolution',lambda:self.request('POST','transactions/'+shared['id']+'/receipt-shares',{'expected_version':1,'document_id':item['source_document_id'],'item_id':item['id'],'amount':item['claimed_amount'],'quantity':'1','reason':'Authorized synthetic shared receipt within its eligible amount','evidence_ids':[shared['id']]},key='shared-resolution'))
        self.approve(shared['id'])
        for pair in self.request('GET','transactions/'+shared['id']+'/duplicate-candidates')['items']:
            if pair.get('disposition') is not None:continue
            # Separate known synthetic receipts/dates are inspected explicitly;
            # a fuzzy invoice/claim number alone is not duplicate proof.
            self.once('shared-distinct:'+pair['id'],lambda pair=pair:self.request('POST','duplicate-candidates/'+pair['id']+'/resolutions',{'expected_version':1,'disposition':'DISTINCT','reason':'Compared the preserved synthetic receipt IDs and business dates: separate obligations','evidence_ids':[shared['id'],pair['candidate_id']]},key='shared-distinct:'+pair['id']))
        self.scenario('shared-receipt','Authorized shared receipt allocation',self.report(shared['id']),'PASS')
        overflow_id,overflow=self.structured('employee/shared_exceeded')
        self.scenario('shared-overflow','Shared receipt capacity exceeded',overflow,'HOLD')
        # An explicitly introduced canonical transcription error must lose
        # eligibility; source-linked correction restores facts in another version.
        tid=created['id']
        facts=deepcopy(self.once('vlm-original-canonical',lambda:self.request('GET','transactions/'+tid)['versions'][0]['payload']))
        facts['total_amount']='23500.00'
        wrong=self.once('correction-error',lambda:self.request('POST','transactions/'+tid+'/revisions',{'expected_version':1,'reason':'Synthetic demo transcription error: total differs from preserved source','transaction':facts},key='correction-error'))
        self.once('correction-evaluate',lambda:self.request('POST','transactions/'+tid+'/evaluate',{'expected_version':wrong['version'],'reason':'Screen the new synthetic transcription version against retained source facts'},key='correction-evaluate'))
        before=self.once('correction-hold',lambda:self.report(tid,wrong['version']))
        if before['decision']!='HOLD':raise RuntimeError('Incorrect source total must not retain PASS')
        corrected=self.once('source-correction',lambda:self.request('POST','documents/'+doc['id']+'/commit',body|{'transaction_id':tid,'expected_version':wrong['version'],'reason':'Reviewer restores the actual printed source total; prior versions retained'},key='source-correction'))
        after=self.once('correction-pass',lambda:self.approve(tid,corrected['version']))
        retained=self.request('GET','evaluations/'+before['evaluation_id'])
        if retained['decision']!='HOLD' or retained['transaction']['total_amount']!='23500.00':raise RuntimeError('Original evaluation history changed')
        self.scenario('correction','Source correction → new version → new approvals → reevaluation',after,'PASS',{'original_evaluation_id':before['evaluation_id'],'original_decision':before['decision'],'original_version':before['transaction_version']})
        self.saved['complete']=True;self.checkpoint()
        print(json.dumps({'synthetic':True,'scope':TENANT,'computed_scenarios':[{k:r[k] for k in ('key','decision','transaction_version','case_url')} for r in self.saved['scenarios']],'manifest':'runtime/demo/scenarios.json'},indent=2))


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','run'])
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:
        runner=Runner()
        try:runner.run()
        finally:runner.http.close()


if __name__=='__main__':
    try:main()
    except RuntimeError as error:raise SystemExit('Hackathon demo: '+str(error)) from None
    except StopIteration:raise SystemExit('Hackathon demo configuration or provider metadata is incomplete; no successful outcome was fabricated.') from None
