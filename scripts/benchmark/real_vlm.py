#!/usr/bin/env python3
"""Opt-in real TypeLLM/VLM compatibility smoke; expected data never enters prompts."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
from uuid import uuid4
import subprocess
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings
from app.core.identity import Identity
from app.documents.processor import DocumentProcessor
from app.documents.normalizer import Normalizer,validate_draft
from app.domain.extraction import DocumentBundle,DocumentPage,DocumentSourceType,SCHEMA_VERSION,to_data
from app.extraction.typellm import TypeLLMExtractionAdapter
from app.extraction.grid import row_crops
from app.integrations.storage import LocalStorage


def observed(result):
    data=to_data(result)
    values=[o|{'id':str(uuid4())} for o in data['header_fields']]
    values.extend(o|{'id':str(uuid4()),'field_path':f'lines.{r["row_index"]-1}.{o["field_path"]}'} for r in data['line_items'] for o in r['fields'])
    return values


def real_extract(file,kind,settings,identity,storage,use_row_crops=True):
    content=file.read_bytes();start=time.monotonic()
    processed=DocumentProcessor(settings.document_limits).process(file);crops={}
    pages=[];page_details={}
    for p in processed['pages']:
        png=base64.b64decode(p.pop('preview_base64'));key,sha=storage.put(identity,png,maximum=settings.document_limits.maximum_derived_bytes)
        p['preview_key']=key;page_details[p['page']]=p
        pages.append(DocumentPage(p['page'],p['native_text'] or None,key))
    bundle=DocumentBundle(uuid4(),1,identity.tenant_id,identity.legal_entity_id,DocumentSourceType(kind),tuple(pages))
    def row_image(page,ordinal,count):
        if page.page not in crops:crops[page.page]=row_crops(storage.get(identity,page.artifact_ref),settings.document_providers.maximum_rows)
        if len(crops[page.page])!=count:return None
        png,trace=crops[page.page][ordinal-1];key,sha=storage.put(identity,png,maximum=4*1024*1024)
        return 'data:image/png;base64,'+base64.b64encode(png).decode(),trace|{'storage_key':key,'preview_key':page.artifact_ref,'page_transform':page_details[page.page]['transform']}
    adapter=TypeLLMExtractionAdapter(settings.document_providers,
        image_loader=lambda p:'data:image/png;base64,'+base64.b64encode(storage.get(identity,p.artifact_ref)).decode(),row_image_loader=row_image if use_row_crops else None)
    result=adapter.extract(bundle,SCHEMA_VERSION)
    if result.metadata.provider_id!='ENTERPRISE_VLM' or not any(v.name=='bridge' for v in result.metadata.runtime_versions):raise RuntimeError('Real provider acceptance must not use fixtures or a parser result')
    candidate,traces,findings=Normalizer().normalize(observed(result));findings+=validate_draft(candidate,traces,kind)
    return {'file':file.name,'original_sha256':hashlib.sha256(content).hexdigest(),'pages':len(pages),
        'seconds':time.monotonic()-start,'extraction':to_data(result),'routing':adapter.sidecar,
        'candidate':candidate,'normalization_findings':findings,'normalization_traces':traces}


def compare(case,expected):
    headers={o['field_path']:o for o in case['extraction']['header_fields']}
    checks={}
    for field,value in expected.get('raw_headers',{}).items():
        observation=headers.get(field,{})
        checks[field]={'expected':value,'actual':observation.get('raw_value'),'exact_raw_match':observation.get('raw_value')==value,'state':observation.get('state')}
    for field,state in expected.get('states',{}).items():checks[field]={'expected_state':state,'actual_state':headers.get(field,{}).get('state'),'exact_state_match':headers.get(field,{}).get('state')==state}
    for field,value in expected.get('canonical_headers',{}).items():checks[field]={'expected':value,'actual':case['candidate'].get(field),'exact_canonical_string_match':case['candidate'].get(field)==value}
    rows=case['extraction']['line_items'];line_checks=[]
    for i,expected_row in enumerate(expected.get('rows',[])):
        actual={o['field_path']:o['raw_value'] for o in rows[i]['fields']} if i<len(rows) else {}
        line_checks.append({field:{'expected':value,'actual':actual.get(field),'exact_raw_match':actual.get(field)==value} for field,value in expected_row.items()})
    return {'header_checks':checks,'line_checks':line_checks,'expected_rows':len(expected.get('rows',[])),'actual_rows':len(rows)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--primary',type=Path,required=True)
    parser.add_argument('--primary-expectations',type=Path);parser.add_argument('--output',type=Path,default=ROOT/'runtime/inference/reports/real-vlm-benchmark.json')
    parser.add_argument('--primary-only',action='store_true')
    parser.add_argument('--disable-row-crops',action='store_true',help='Measure actual full-page rows for crop comparison')
    args=parser.parse_args();os.umask(0o077);settings=Settings.load()
    os.environ.setdefault(settings.document_providers.gateway_token_env,(ROOT/'runtime/inference/gateway.key').read_text().strip())
    if settings.document_providers.transport!='TYPELLM_GATEWAY':raise SystemExit('Configure the real TypeLLM gateway explicitly.')
    corpus=ROOT/'runtime/inference/corpus';corpus.mkdir(parents=True,exist_ok=True)
    # A rasterization of an existing preserved synthetic PDF, not expected-result
    # rendering or model output. Its source hash is recorded independently.
    processed=DocumentProcessor(settings.document_limits).process(ROOT/'data/documents_phase2/vendor_native.pdf')
    scan=corpus/'vendor_scan.png';scan.write_bytes(base64.b64decode(processed['pages'][0]['preview_base64']))
    files=[('table_invoice_primary',args.primary,'VENDOR_INVOICE'),('clean_scan',scan,'VENDOR_INVOICE'),
        ('digital_pdf',ROOT/'data/documents_phase2/vendor_native.pdf','VENDOR_INVOICE'),
        ('multi_page',ROOT/'data/documents_phase2/vendor_multipage.pdf','VENDOR_INVOICE'),
        ('receipt_photo',ROOT/'data/documents_phase2/receipt_photo.jpg','EMPLOYEE_RECEIPT')]
    if args.primary_only:files=files[:1]
    identity=Identity(uuid4(),uuid4(),uuid4(),frozenset({'FINANCE_REVIEWER'}),'Real inference synthetic smoke')
    storage=LocalStorage(ROOT/'runtime/inference/benchmark-storage');cases=[];stop=threading.Event();samples=[]
    def memory():
        while not stop.is_set():
            try:samples.append(int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True,timeout=2).strip().splitlines()[0]))
            except Exception:pass
            stop.wait(.25)
    sampler=threading.Thread(target=memory,daemon=True);sampler.start()
    try:
        for name,file,kind in files:
            case=real_extract(file,kind,settings,identity,storage,use_row_crops=not args.disable_row_crops);case['case']=name;cases.append(case)
            # Independent comparisons load after model extraction. Never pass
            # these mappings, golden responses or answers to real_extract().
            if name=='table_invoice_primary' and args.primary_expectations:expected=json.loads(args.primary_expectations.read_text())
            else:
                ground=json.loads((ROOT/'data/documents_phase2/expected.json').read_text())
                expected={'canonical_headers':ground['receipt' if kind=='EMPLOYEE_RECEIPT' else 'vendor']}
            case['independent_comparison']=compare(case,expected)
            print(name,round(case['seconds'],3),'seconds',len(case['extraction']['line_items']),'rows',flush=True)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps({'version':'real-vlm-smoke-v1','scope':f'{len(files)} actual source variants; compatibility smoke, not production accuracy',
                'row_crops_enabled':not args.disable_row_crops,
                'synthetic_variant_warning':'The digital and rasterized invoice share one synthetic source; the multi-page fixture repeats printed headers.',
                'peak_whole_device_memory_mib':max(samples) if samples else None,'cases':cases},indent=2)+'\n')
    finally:stop.set();sampler.join(timeout=3)


if __name__=='__main__':main()
