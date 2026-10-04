#!/usr/bin/env python3
"""Measure the owned local model lifecycle and actual supplied-file extraction.

No expected answers or scores enter inference. Private results stay ignored.
Restart is opt-in and affects only the existing verified owned model service.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'apps/api'),str(ROOT/'scripts')]


def measure(action):
    samples=[];stop=threading.Event()
    def sample():
        while not stop.is_set():
            try:samples.append(int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True,timeout=2).strip().splitlines()[0]))
            except (OSError,ValueError,subprocess.SubprocessError):pass
            stop.wait(.25)
    thread=threading.Thread(target=sample,daemon=True);thread.start();started=time.monotonic()
    try:result=action()
    finally:stop.set();thread.join(timeout=3)
    return {'seconds':round(time.monotonic()-started,3),'peak_whole_device_memory_mib':max(samples) if samples else None,'result':result}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file',type=Path);p.add_argument('--restart-owned-model',action='store_true');args=p.parse_args()
    if not args.file.is_file():raise SystemExit('Supplied local file is unavailable')
    os.umask(0o077)
    from app.core.config import Settings
    from app.core.identity import Identity
    from app.db.models import Base
    from app.documents.processor import DocumentProcessor
    from app.documents.normalizer import Normalizer,validate_draft
    from app.integrations.storage import LocalStorage
    from app.services.document_worker import extract
    from app.domain.extraction import to_data
    from demo import inference_health
    settings=Settings.load()
    os.environ[settings.document_providers.gateway_token_env]=(ROOT/'runtime/inference/gateway.key').read_text().strip()
    identity=Identity(uuid4(),uuid4(),uuid4(),frozenset({'FINANCE_REVIEWER'}),'Local supplied-source measurement')
    storage=LocalStorage(ROOT/'runtime/clearledger/storage')
    def request():
        pages=DocumentProcessor().process(args.file)['pages']
        for page in pages:
            page['preview_key'],_=storage.put(identity,base64.b64decode(page.pop('preview_base64')),maximum=settings.document_limits.maximum_derived_bytes)
        observed,diagnostics,routing=extract({'id':uuid4(),'source_type':'VENDOR_INVOICE'},identity,pages,storage,settings.document_providers)
        data=to_data(observed)
        observations=[o|{'id':str(uuid4())} for o in data['header_fields']]
        observations += [o|{'id':str(uuid4()),'field_path':f'lines.{row["row_index"]-1}.{o["field_path"]}'} for row in data['line_items'] for o in row['fields']]
        candidate,traces,findings=Normalizer().normalize(observations)
        findings+=validate_draft(candidate,traces,'VENDOR_INVOICE',diagnostics)
        return {'observed':data,'routing':routing,'diagnostics':diagnostics,'candidate':candidate,'findings':findings,'finance_decision':None}
    results={}
    if args.restart_owned_model:
        subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/inference/local.py'),'stop'],check=True,capture_output=True)
        def start():
            subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/inference/local.py'),'start'],check=True,capture_output=True)
            deadline=time.monotonic()+150
            while time.monotonic()<deadline:
                health=inference_health()
                if health['status']=='AVAILABLE':return health
                time.sleep(.5)
            raise RuntimeError('Owned model did not become healthy')
        results['cold_service_startup']=measure(start)
        results['first_request_after_startup']=measure(request)
    else:
        if inference_health()['status']!='AVAILABLE':raise SystemExit('Verified local model service is unavailable')
        results['resident_first_request']=measure(request)
    results['resident_subsequent_request']=measure(request)
    target=ROOT/'runtime/clearledger'/('cold-warm-probe.json' if args.restart_owned_model else 'resident-probe.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({'source_sha256':hashlib.sha256(args.file.read_bytes()).hexdigest(),
        'limitations':'One supplied invoice, no accuracy score. Startup includes pinned verification and weight loading; subsequent requests reuse the resident service. Whole-device GPU memory includes all processes. No old-code cold baseline exists.',
        'runs':results},indent=2)+'\n')
    for name,run in results.items():
        out={k:v for k,v in run.items() if k!='result'}
        if 'routing' in run['result']:
            r=run['result'];out.update(paths=r['routing']['paths'],rows=len(r['observed']['line_items']),unresolved=len(r['findings']),finance_decision=None,
                provider_calls=r['routing'].get('enterprise',{}).get('calls'))
        print(json.dumps({'run':name,**out}),flush=True)


if __name__=='__main__':main()
