"""Pinned isolated CPU candidate used only by the benchmark, not default intake."""
import json
import os
from pathlib import Path
import selectors
import subprocess
import time
from app.documents.processor import DocumentFailure
from app.extraction.ocr import OCRPage,original_box

ROOT=Path(__file__).resolve().parents[2]


class RapidCandidate:
    version='rapidocr-3.9.2-onnxruntime-1.23.2-CPU-PP-OCRv6-small'
    def __init__(self):
        self.timeout_seconds=30;self.metrics=[]
        env={'PATH':os.defpath,'LANG':'C.UTF-8','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'1'}
        self.process=subprocess.Popen([str(ROOT/'runtime/ocr-rapid/.venv/bin/python'),str(ROOT/'apps/api/app/extraction/rapidocr_runtime.py'),str(ROOT/'runtime/clearledger')],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1,env=env,cwd=ROOT)
        self.startup=self.read(30)
        if not self.startup.get('ready'):self.close();raise DocumentFailure('CANDIDATE_OCR_UNAVAILABLE')

    def read(self,timeout):
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout,selectors.EVENT_READ)
            if not selector.select(timeout):self.close();raise DocumentFailure('OCR_TIMEOUT',retryable=True)
        line=self.process.stdout.readline(2*1024*1024+1)
        if len(line)>2*1024*1024:self.close();raise DocumentFailure('OCR_RESPONSE_INVALID')
        try:return json.loads(line)
        except ValueError:self.close();raise DocumentFailure('OCR_RESPONSE_INVALID') from None

    def recognize(self,path,transform):
        if self.process.poll() is not None:raise DocumentFailure('CANDIDATE_OCR_UNAVAILABLE')
        self.process.stdin.write(json.dumps({'path':str(Path(path).resolve())})+'\n');self.process.stdin.flush()
        data=self.read(self.timeout_seconds)
        if data.get('failure'):raise DocumentFailure(data['failure'])
        width,height=transform['derived_dimensions'];spans=[]
        for s in data['spans']:
            box={k:float(v)/(width if k.startswith('x') else height) for k,v in s['pixels'].items()}
            if any(v<0 or v>1 for v in box.values()) or box['x1']>=box['x2'] or box['y1']>=box['y2']:raise DocumentFailure('OCR_RESPONSE_INVALID')
            spans.append({'text':s['text'],'bbox':original_box(box,transform.get('exif_orientation',1)),
                          'layout_bbox':box,'kind':'line','score_diagnostic_only':s['score_diagnostic_only']})
        # Text-detector lines retain exact punctuation. Word polygons remain in
        # diagnostic metrics; no synthetic word box or certainty is introduced.
        self.metrics.append({k:v for k,v in data.items() if k!='spans'})
        return OCRPage('\n'.join(s['text'] for s in spans),tuple(spans),'RAPIDOCR_CPU_CANDIDATE',self.version)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
