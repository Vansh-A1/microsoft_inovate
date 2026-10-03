#!/usr/bin/env python3
"""Loopback API measurements; only public timing/count metadata is emitted."""
from pathlib import Path
from time import perf_counter
import json,platform,statistics,sys,urllib.request
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings

def main():
    settings=Settings.load()
    if not settings.development:raise SystemExit('This benchmark targets the owned loopback development application only.')
    token=next(iter(settings.identities))
    def get(path):
        request=urllib.request.Request('http://127.0.0.1:8000/api/v1/'+path,headers={'Authorization':'Bearer '+token})
        with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
    records=get('transactions?limit=25')['items'];case=next(r for r in records if r.get('latest_evaluation_id'));tid=case['id'];eid=case['latest_evaluation_id']
    routes={'list_25':'transactions?limit=25','case_detail':'transactions/'+tid,'review_queue_25':'reviews/queue?limit=25','audit_timeline':'transactions/'+tid+'/audit','report':'evaluations/'+eid+'/report','admin_catalog':'admin/catalog'}
    # Use the established operational queue/timeline contracts.
    routes['review_queue_25']='reviews?limit=25';routes['audit_timeline']='transactions/'+tid+'/timeline'
    measurements={}
    for name,path in routes.items():
        get(path);times=[]
        for _ in range(20):
            started=perf_counter();get(path);times.append((perf_counter()-started)*1000)
        measurements[name]={'samples':len(times),'median_ms':round(statistics.median(times),3),'p95_ms':round(sorted(times)[18],3),'max_ms':round(max(times),3)}
    output={'version':'release-api-v1','synthetic':True,'python':platform.python_version(),'measurements':measurements,'scope':'Warm loopback HTTP; development synthetic data; shared local host. No cloud, VLM or enterprise throughput claim.'}
    folder=ROOT/'runtime/release';folder.mkdir(parents=True,exist_ok=True);(folder/'api-phase6.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
