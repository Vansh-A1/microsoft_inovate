#!/usr/bin/env python3
"""Measured actual local browser proxy -> durable worker -> document result.

Only allowlisted fictional benchmark files; loopback HTTP, configured demo role.
No finance commit, human verification, credentials printing or external traffic.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from uuid import uuid4
import httpx

ROOT=Path(__file__).resolve().parents[2]
ORIGIN='http://127.0.0.1:3000'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True)
    p.add_argument('--case',choices=['t01','t04'],default='t04');args=p.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,64}',args.label):raise SystemExit('Use a bounded lowercase measurement label')
    os.umask(0o077)
    manifest=json.loads((ROOT/'data/clearledger_challenge/manifest.json').read_text())
    case=next(c for c in manifest['cases'] if c['id']==args.case)
    source=ROOT/'data/clearledger_challenge'/case['path'];content=source.read_bytes()
    assert hashlib.sha256(content).hexdigest()==case['sha256']
    target=ROOT/'runtime/clearledger'/('async-'+args.label+'-'+args.case+'.json')
    if target.exists():raise SystemExit('Result exists; choose a fresh label')
    with httpx.Client(base_url=ORIGIN,timeout=20,follow_redirects=False) as client:
        session=client.post('/api/development/session',headers={'Origin':ORIGIN},json={'label':'Synthetic finance workspace'})
        session.raise_for_status()
        def post(path,**kwargs):
            response=client.post(path,headers={'Origin':ORIGIN,'Idempotency-Key':str(uuid4()),**kwargs.pop('headers',{})},**kwargs)
            response.raise_for_status();return response
        started=time.monotonic()
        upload=post('/api/uploads',json={'filename':'fictional-challenge-'+source.name,
            'mime':'image/png' if source.suffix=='.png' else 'application/pdf','source_type':'VENDOR_INVOICE'}).json()
        post('/api/uploads/'+upload['id']+'/bytes',headers={'Content-Type':'application/octet-stream'},content=content)
        post('/api/uploads/'+upload['id']+'/finalize',json={})
        upload_seconds=time.monotonic()-started;states=[];deadline=started+180
        while time.monotonic()<deadline:
            response=client.get('/api/documents/'+upload['document_id']);response.raise_for_status();doc=response.json()
            state={'state':doc['state'],'last_successful_stage':doc['last_successful_stage']}
            if not states or state!={k:v for k,v in states[-1].items() if k!='seconds'}:states.append(state|{'seconds':round(time.monotonic()-started,3)})
            if doc['state'] in ('READY','NEEDS_INPUT','QUARANTINED','FAILED_RETRYABLE','FAILED_FINAL'):break
            time.sleep(.5)
        else:raise RuntimeError('Durable processing did not finish within observation bound')
        output={'source_sha256':case['sha256'],'case':args.case,'upload_seconds':round(upload_seconds,3),
            'end_to_end_seconds':round(time.monotonic()-started,3),'states':states,
            'state':doc['state'],'last_error':doc['last_error'],'finance_decision':doc['finance_decision'],
            'document_id':doc['id'],'jobs':doc['jobs'],'extraction_runs':doc['extraction_runs'],
            'limitations':'Loopback upload/proxy/queue/workers/polling; excludes human confirmation, browser rendering and finance approvals. Polling granularity 0.5s. Fictional source only.'}
        target.write_text(json.dumps(output,indent=2)+'\n')
        print(json.dumps({k:v for k,v in output.items() if k not in ('document_id','jobs','extraction_runs')}))


if __name__=='__main__':main()
