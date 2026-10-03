#!/usr/bin/env python3
"""Measure the actual synthetic CPU corpus; never replay fixture responses."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.identity import Identity
from app.core.config import Settings
from app.documents.processor import DocumentProcessor,DocumentFailure
from app.documents.normalizer import Normalizer,validate_draft
from app.documents.config import ProviderSettings
from app.domain.extraction import to_data
from app.services.document_worker import extract


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'generated/reports/documents-phase2.json')
    args=parser.parse_args();settings=Settings.load()
    # Deliberately CPU-only: configured enterprise endpoints are not benchmarked here.
    providers=ProviderSettings(ocr_executable=settings.document_providers.ocr_executable,
        ocr_data_directory=settings.document_providers.ocr_data_directory,
        ocr_library_directory=settings.document_providers.ocr_library_directory)
    corpus=ROOT/'data/documents_phase2';expected=json.loads((corpus/'expected.json').read_text())
    identity=Identity(uuid4(),uuid4(),uuid4(),frozenset({'FINANCE_REVIEWER'}),'Synthetic CPU benchmark')
    rows=[]
    for file in sorted(p for p in corpus.iterdir() if p.suffix in ('.pdf','.jpg','.png')):
        started=time.perf_counter();row={'file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
        try:
            processed=DocumentProcessor(settings.document_limits).process(file)
            with tempfile.TemporaryDirectory(prefix='ap-p2-benchmark-') as folder:
                class Artifacts:
                    def path(self,scope,key):return Path(folder)/key
                    def get(self,scope,key):return self.path(scope,key).read_bytes()
                storage=Artifacts()
                for page in processed['pages']:
                    page['preview_key']=str(page['page'])+'.png'
                    storage.path(identity,page['preview_key']).write_bytes(base64.b64decode(page.pop('preview_base64')))
                receipt=file.name.startswith('receipt_')
                kind='EMPLOYEE_RECEIPT' if receipt else 'VENDOR_INVOICE'
                result,diagnostics,routing=extract({'id':uuid4(),'source_type':kind},identity,processed['pages'],storage,providers)
                r=to_data(result)
                observations=[o|{'id':str(uuid4())} for o in r['header_fields']]
                observations.extend(o|{'id':str(uuid4()),'field_path':f'lines.{line["row_index"]-1}.{o["field_path"]}'} for line in r['line_items'] for o in line['fields'])
                candidate,traces,findings=Normalizer().normalize(observations)
                findings+=validate_draft(candidate,traces,kind,diagnostics)
                ground=expected['receipt' if receipt else 'vendor']
                comparison={key:{'expected':value,'candidate':candidate.get(key),'exact_match':candidate.get(key)==value} for key,value in ground.items()}
                row.update(state='NEEDS_INPUT' if findings else 'READY',pages=len(processed['pages']),routing=routing,
                    critical_fields=comparison,findings=findings,observations=len(observations),
                    measured_boxes=sum(bool(o.get('source') and o['source'].get('bbox')) for o in observations))
        except DocumentFailure as exc:row.update(state='PROCESSING_FAILURE',failure_code=exc.code)
        row['elapsed_seconds']=round(time.perf_counter()-started,6);rows.append(row)
    report={'version':'document-cpu-benchmark-v1','dataset_version':expected['version'],
        'synthetic':True,'live_enterprise_vlm':'DEFERRED_EXTERNAL_RUNTIME','gpu_latency_vram':None,
        'notes':'Actual CPU native/OCR execution on 14 synthetic sources; fields compare only printed independent ground truth. No finance decision or production quality percentage.',
        'cases':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(rows),'states':{s:sum(r['state']==s for r in rows) for s in sorted({r['state'] for r in rows})},'report':str(args.output)}))


if __name__=='__main__':main()
