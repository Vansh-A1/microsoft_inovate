#!/usr/bin/env python3
"""Pixel-truth evaluation of pinned public fictional sources via local durable API.

No production injection, external inference, expected answers in prompts, finance
submission or automatic correction. Original PDFs/PNGs are cached separately in
ignored runtime; the manifest and reuse notices were checked before downloading.
Exit zero confirms measurement completion, not invoice accuracy or clearance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from uuid import uuid4
import httpx

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/'data/clearledger_public/manifest.json'
ORIGIN='http://127.0.0.1:3000'
FINAL={'READY','NEEDS_INPUT','QUARANTINED','FAILED_RETRYABLE','FAILED_FINAL','DEPENDENCY_UNAVAILABLE'}
MONEY={'subtotal_amount','tax_amount','total_amount','document_discount_amount','shipping_amount','other_charges_amount',
       'unit_price','amount','discount_amount','net_amount','gross_amount'}
CODE=[ROOT/'apps/api/app/extraction'/n for n in ('layout.py','native.py','typellm.py','row_grounding.py','cpu_ocr.py','rapidocr_runtime.py')]+[
    ROOT/'apps/api/app/services/document_worker.py',ROOT/'apps/api/app/documents/normalizer.py']


def code_hashes():return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in CODE}


def literal(raw,field,tokens):
    if not isinstance(raw,str):return None
    value=' '.join(raw.split())
    if field.split('.')[-1] in MONEY:
        for token in tokens:value=value.replace(token,'').strip()
    return value


def score(doc,case):
    by={o['field_path']:o for o in doc.get('observations',[])}
    candidate=(doc.get('draft') or {}).get('candidate',{})
    def check(field,expected,page=None):
        o=by.get(field,{});raw=literal(o.get('raw_value'),field,case['money_tokens'])
        states=case.get('accepted_states',{}).get(field,['PRESENT'])
        equal=expected in (raw or '') if field in case.get('contains_fields',[]) else raw==expected
        source=o.get('source') or {}
        return {'read':o.get('state') in states and equal,'page':page is None or source.get('page')==page,
                'state':o.get('state'),'raw':o.get('raw_value'),'candidate':candidate.get(field)}
    headers={f:check(f,v) for f,v in case['headers'].items()}
    rows=[{f:check(f'lines.{i}.{f}',v,row['page']) for f,v in row.items() if f!='page'} for i,row in enumerate(case['rows'])]
    absent={f:{'missing':by.get(f,{}).get('state')=='MISSING' and by.get(f,{}).get('raw_value') is None,
        'canonical_unresolved':candidate.get(f) is None,'state':by.get(f,{}).get('state'),'raw':by.get(f,{}).get('raw_value')} for f in case['absent']}
    return {'headers':headers,'rows':rows,'absent':absent,
        'header_matches':sum(v['read'] for v in headers.values()),'header_checked':len(headers),
        'row_matches':sum(v['read'] and v['page'] for row in rows for v in row.values()),'row_checked':sum(map(len,rows)),
        'expected_rows':len(rows),'actual_rows':len({int(f.split('.')[1]) for f in by if f.startswith('lines.')}),
        'required_abstentions':{f:candidate.get(f) is None for f in case['must_be_unresolved']}}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
    parser.add_argument('--case');parser.add_argument('--corpus',choices=['clearledger_public','clearledger_public_reserved'],default='clearledger_public');args=parser.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,64}',args.label):raise ValueError('Bounded lowercase measurement label required')
    os.umask(0o077);target=ROOT/'runtime/clearledger'/('public-'+args.label+'.json')
    if target.exists():raise RuntimeError('Measurement exists; historical evidence cannot be overwritten')
    truth=ROOT/'data'/args.corpus/'manifest.json'
    manifest=json.loads(truth.read_text());hashes=code_hashes()
    if args.case and args.case not in {case['id'] for case in manifest['cases']}:raise ValueError('Case must belong to frozen corpus')
    output={'version':'clearledger-public-measurement-v1','label':args.label,
        'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'code_sha256':hashes,'truth_sha256':hashlib.sha256(truth.read_bytes()).hexdigest(),'corpus':args.corpus,
        'limitations':f"{len(manifest['cases'])} externally authored fictional sources in this frozen corpus, not real-company or new-template-family accuracy. Actual loopback upload/proxy/durable worker/result at 0.5s polling. Existing model is resident; first worker/client request can be cold. No cold weight load. Human review/approvals/browser render excluded. Truth enters only post-extraction scoring; production hashes remain unchanged during this run.",'cases':[]}
    with httpx.Client(base_url=ORIGIN,timeout=20,follow_redirects=False) as client:
        session=client.post('/api/development/session',headers={'Origin':ORIGIN},json={'label':'Synthetic finance workspace'});session.raise_for_status()
        def post(path,**kw):
            response=client.post(path,headers={'Origin':ORIGIN,'Idempotency-Key':str(uuid4()),**kw.pop('headers',{})},**kw)
            response.raise_for_status();return response.json()
        for case in manifest['cases']:
            if args.case and args.case!=case['id']:continue
            if hashes!=code_hashes():raise RuntimeError('Production code changed during frozen evaluation')
            source=ROOT/'runtime/clearledger/public-research'/case['source']['local_path'];content=source.read_bytes()
            if hashlib.sha256(content).hexdigest()!=case['source']['sha256']:raise ValueError('Pinned public source changed')
            started=time.monotonic();value={'id':case['id'],'source_sha256':case['source']['sha256']};states=[]
            upload=post('/api/uploads',json={'filename':'public-fictional-'+source.name,'mime':'image/png' if source.suffix=='.png' else 'application/pdf','source_type':'VENDOR_INVOICE'})
            post('/api/uploads/'+upload['id']+'/bytes',headers={'Content-Type':'application/octet-stream'},content=content)
            post('/api/uploads/'+upload['id']+'/finalize',json={});value['upload_seconds']=round(time.monotonic()-started,3)
            deadline=started+300
            while time.monotonic()<deadline:
                response=client.get('/api/documents/'+upload['document_id']);response.raise_for_status();doc=response.json()
                state={'state':doc['state'],'last_successful_stage':doc['last_successful_stage']}
                if not states or state!={k:v for k,v in states[-1].items() if k!='seconds'}:states.append(state|{'seconds':round(time.monotonic()-started,3)})
                if doc['state'] in FINAL:break
                time.sleep(.5)
            else:value['observation_failure']='BOUNDED_OBSERVATION_TIMEOUT'
            value.update(end_to_end_seconds=round(time.monotonic()-started,3),states=states,state=doc['state'],last_error=doc['last_error'],
                finance_decision=doc['finance_decision'],document=doc,**score(doc,case))
            output['cases'].append(value);target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({k:v for k,v in value.items() if k not in ('document','headers','rows','absent')},ensure_ascii=False),flush=True)
    if hashes!=code_hashes():raise RuntimeError('Production code changed during frozen evaluation')


if __name__=='__main__':main()
