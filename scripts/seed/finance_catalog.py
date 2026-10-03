"""Generate an additive, entirely fictional Phase-3 catalog; never alter old fixtures."""
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from uuid import UUID,uuid5
import json,sys
ROOT=Path(__file__).resolve().parents[2]
NS=UUID('6c85fb51-c45c-4a82-82b6-861d49dfcf48')
def uid(name):return str(uuid5(NS,name))
def originals(kind):return json.loads((ROOT/f'data/synthetic/reference/{kind}.json').read_text())['records']
def catalog():
    records=[]
    def add(kind,p):p['synthetic']=True;p.pop('tenant_id',None);p.pop('legal_entity_id',None);records.append({'kind':kind,'payload':p});return p
    base_vendor=originals('vendors')[0];base_employee=originals('employees')[0];cc=originals('cost_centers')[0]
    for i in range(1,3):add('cost_centers',dict(cc,id=uid(f'cc-{i}'),name=f'SYNTHETIC COST CENTER {i}'))
    for i in range(1,20):add('vendors',dict(base_vendor,id=uid(f'vendor-{i}'),legal_name=f'SYNTHETIC SUPPLIER {i:02}',payment_account_token=f'SYNTHETIC_EQUALITY_{i:02}',aliases=[f'SYNTHETIC SUPPLIER ALIAS {i:02}']))
    for i in range(4,30):add('employees',dict(base_employee,id=uid(f'employee-{i}'),name=f'SYNTHETIC EMPLOYEE {i:02}',employee_number=f'SYNTHETIC-E{i:02}'))
    po=originals('purchase_orders')[0];line=po['lines'][0];receipt=originals('goods_receipts')[0];grn=receipt['lines'][0]
    for i in range(1,50):
        vendor_id=uid(f'vendor-{i%19+1}');pid=uid(f'po-{i}');lid=uid(f'po-line-{i}');gid=uid(f'grn-{i}');rid=uid(f'grn-line-{i}')
        parent=deepcopy(po);parent.update(id=pid,vendor_id=vendor_id,display_number=f'SYNTHETIC-PO-{i:03}',approved_ceiling_amount='1000000.00');parent.pop('lines');add('purchase_orders',parent)
        child=deepcopy(line);child.update(id=lid,po_id=pid,vendor_id=vendor_id,ordered_quantity='100.0000');add('po_lines',child)
        parent=deepcopy(receipt);parent.update(id=gid,po_id=pid);parent.pop('lines');add('goods_receipts',parent)
        child=deepcopy(grn);child.update(id=rid,po_id=pid,po_line_id=lid,accepted_quantity='100.0000',returned_quantity='0.0000',reversed_quantity='0.0000');add('grn_lines',child)
    budget=deepcopy(originals('budgets')[0]);budget.update(id=uid('usd-budget'),currency='USD');budget['ledger']=[{'id':uid('usd-allocation'),'entry_type':'ALLOCATION','amount':'100000.00','currency':'USD'}];add('budgets',budget)
    add('fx_rates',{'id':uid('fx-usd-inr'),'version':1,'from_currency':'USD','to_currency':'INR','rate':'83.00','business_date':'2026-09-28','convention':'TARGET_PER_SOURCE','source_note':'Fictional explicit demonstration rate; no market-price claim.'})
    return records

def transactions():
    sys.path.insert(0,str(ROOT/'apps/api'));from app.schemas.canonical import fixture_canonical
    base=fixture_canonical(json.loads((ROOT/'data/golden_cases/vendor/clean.json').read_text())['transaction']);records=[]
    for i in range(200):
        p=deepcopy(base);p['invoice_number']=f'SYNTHETIC-SCALE-{i:04}';p['invoice_date']=(date(2026,1,1)+timedelta(days=i)).isoformat();p['source_document_id']=None
        line=p['lines'][0];line['id']=uid(f'transaction-line-{i}')
        records.append({'id':uid(f'transaction-{i}'),'version':1,'synthetic':True,'source_coverage':'UNVERIFIED_STRUCTURED_SCALE_INPUT','transaction':p})
    return records

def generate():
    target=ROOT/'data/finance_phase3';target.mkdir(exist_ok=True)
    files={'catalog.json':{'synthetic':True,'source_system':'SYNTHETIC_PHASE3_SCALE','source_version':'v1','records':catalog()},'transactions.json':{'synthetic':True,'records':transactions()}}
    manifest={'synthetic':True,'generator':'scripts/seed/finance_catalog.py','version':'phase3-fixtures-v1','files':[],'totals_with_original_catalog':{'vendors':20,'employees':30,'po_lines':50,'cost_centers':3,'currencies':['INR','USD'],'transactions':200},'source_note':'Scale inputs do not assert finance eligibility; missing source evidence must remain unresolved.'}
    for name,value in files.items():
        raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode();(target/name).write_bytes(raw);manifest['files'].append({'path':name,'sha256':sha256(raw).hexdigest(),'bytes':len(raw)})
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');return manifest

def activate_catalog(database,identity):
    sys.path.insert(0,str(ROOT/'apps/api'));from app.services.reference_imports import stage,validate,activate,active_records
    from dataclasses import replace
    admin=replace(identity,roles=identity.roles|{'REFERENCE_ADMIN'})
    with database.session(admin) as s:
        active=active_records(s,admin)
        if uid('vendor-1') in active:return {'state':'ALREADY_ACTIVE'}
        batch=stage(s,admin,{'source_system':'SYNTHETIC_PHASE3_SCALE','source_version':'v1','records':catalog(),'reason':'Explicit fictional scale catalog'},'phase3-scale');bid=UUID(batch['id']);checked=validate(s,admin,bid,'phase3-scale')
        if checked['state']!='VALID':raise ValueError(checked['validation'])
        return activate(s,admin,bid,'Activate validated fictional scale catalog','phase3-scale')

if __name__=='__main__':print(json.dumps(generate()['totals_with_original_catalog']))
