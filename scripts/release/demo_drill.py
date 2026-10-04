#!/usr/bin/env python3
"""Opt-in local provider outage/recovery acceptance using actual HTTP and jobs."""
import argparse
import json
from pathlib import Path
import sys
import time
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/seed'),str(ROOT/'scripts')]
from hackathon import Runner,visual_invoice
from demo import private_json,inference_health
STATE=ROOT/'runtime/release/provider-drill.json'

def upload(r,name,content,mime,key):
    item=r.request('POST','uploads',{'filename':name,'mime':mime,'source_type':'VENDOR_INVOICE'},key=key)
    r.request('POST',item['bytes_url'].replace('/api/v1/',''),content=content)
    r.request('POST','uploads/'+item['id']+'/finalize',{},key=key+'-finalize')
    return item['document_id']

def wait(r,identifier,states):
    deadline=time.monotonic()+210
    while time.monotonic()<deadline:
        doc=r.request('GET','documents/'+identifier)
        if doc['state'] in states:return doc
        time.sleep(.5)
    raise RuntimeError('Actual provider recovery drill timed out')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['offline','recover'])
    args=parser.parse_args();r=Runner()
    try:
        if args.action=='offline':
            if inference_health()['status']=='AVAILABLE':raise RuntimeError('Offline drill requires the owned inference service stopped')
            run='provider-drill-'+uuid4().hex
            visual=upload(r,'Synthetic provider outage.png',visual_invoice(),'image/png',run+'-visual')
            native=upload(r,'Synthetic native fast path.pdf',(ROOT/'data/documents_phase2/vendor_native.pdf').read_bytes(),'application/pdf',run+'-native')
            completed=wait(r,native,{'READY','NEEDS_INPUT','FAILED_FINAL'})
            if completed['state']!='READY' or completed['extraction_runs'][0]['metadata']['provider_id']!='NATIVE_TEXT':raise RuntimeError('Independent native path failed during provider outage')
            failed=wait(r,visual,{'FAILED_FINAL'})
            if failed['draft'] is not None or failed['last_error']!='PROVIDER_UNAVAILABLE':raise RuntimeError('Provider outage did not remain explicit and incomplete')
            jobs=[j for j in failed['jobs'] if j['stage']=='EXTRACT']
            if not jobs or jobs[-1]['attempts']!=3:raise RuntimeError('Provider retries were not bounded at three attempts')
            private_json(STATE,{'run':run,'visual':visual,'native':native,'failed_attempts':3,'last_error':failed['last_error']})
            print('OFFLINE VERIFIED: CPU/native processing works; visual extraction has no draft/decision and terminates after 3 actual retryable provider failures.')
        else:
            if inference_health()['status']!='AVAILABLE':raise RuntimeError('Recover drill requires the real pinned inference provider')
            state=json.loads(STATE.read_text());doc=r.request('GET','documents/'+state['visual'])
            job=next(j for j in r.request('GET','operations/jobs?state=FAILED',actor='operations')['items'] if j['document_id']==doc['id'] and j['stage']=='EXTRACT')
            body={'expected_attempts':job['attempts'],'reason':'Authorized local outage drill: restored pinned VLM; retry retained original stage'}
            first=r.request('POST',f'operations/jobs/document/{job["id"]}/retry',body,key=state['run']+'-retry',actor='operations')
            if r.request('POST',f'operations/jobs/document/{job["id"]}/retry',body,key=state['run']+'-retry',actor='operations')!=first:raise RuntimeError('Manual retry idempotency mismatch')
            completed=wait(r,doc['id'],{'READY','NEEDS_INPUT','FAILED_FINAL'})
            if completed['state'] not in ('READY','NEEDS_INPUT') or completed['draft'] is None:raise RuntimeError('Restored provider did not complete actual extraction')
            if not any(x['metadata'].get('provider_id')=='ENTERPRISE_VLM' for x in completed['extraction_runs'] if x['status'] in ('PARTIAL','COMPLETED')):raise RuntimeError('Recovered visual output lacks real VLM provenance')
            state['recovered']=True;private_json(STATE,state)
            print('RECOVERY VERIFIED: authorized repeated retry yields one real extraction/draft from the retained original, without a fabricated finance decision.')
    finally:r.http.close()

if __name__=='__main__':
    try:main()
    except RuntimeError as error:raise SystemExit(str(error)) from None
