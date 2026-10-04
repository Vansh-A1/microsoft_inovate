"""Isolated optional CPU OCR. No OCR/ONNX dependencies in finance Python.

Only server configuration selects the child interpreter. Private stdio, bounded
responses/timeouts, explicit local model pins and actual CPU sessions. A real
Tesseract fallback remains available; errors never become extracted facts.
"""
import atexit
import json
import os
import math
from pathlib import Path
import selectors
import subprocess
import threading
import time
from app.documents.processor import DocumentFailure
from app.extraction.ocr import OCRPage,original_box

MODEL_HASHES={'PP-OCRv6_det_small.onnx':'090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f',
              'PP-OCRv6_rec_small.onnx':'6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884',
              'ch_ppocr_mobile_v2.0_cls_mobile.onnx':'e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c'}
_instances={};_cache_lock=threading.Lock()


def validate_handshake(data):
    if not isinstance(data,dict) or data.get('ready') is not True or data.get('models')!=MODEL_HASHES or data.get('packages')!={'rapidocr':'3.9.2','onnxruntime':'1.23.2'}:
        raise DocumentFailure('OCR_RUNTIME_PIN_MISMATCH')
    if data.get('providers')!={name:['CPUExecutionProvider'] for name in ('text_det','text_cls','text_rec')}:
        raise DocumentFailure('OCR_CPU_PROVIDER_REQUIRED')


def mapped_spans(data,transform):
    width,height=transform['derived_dimensions'];spans=[]
    if not isinstance(data,dict) or not isinstance(data.get('spans'),list) or len(data['spans'])>20000:raise DocumentFailure('OCR_RESPONSE_INVALID')
    for name in ('seconds','memory_peak_kib'):
        value=data.get(name,0)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:raise DocumentFailure('OCR_RESPONSE_INVALID')
    for item in data['spans']:
        if not isinstance(item,dict):raise DocumentFailure('OCR_RESPONSE_INVALID')
        text=item.get('text');pixels=item.get('pixels')
        if not isinstance(text,str) or not text.strip() or len(text)>1000 or not isinstance(pixels,dict) or set(pixels)!=set(('x1','y1','x2','y2')):
            raise DocumentFailure('OCR_RESPONSE_INVALID')
        if any(isinstance(v,bool) for v in pixels.values()):raise DocumentFailure('OCR_RESPONSE_INVALID')
        try:box={k:float(v)/(width if k.startswith('x') else height) for k,v in pixels.items()}
        except (ValueError,TypeError,ZeroDivisionError):raise DocumentFailure('OCR_RESPONSE_INVALID') from None
        if any(not 0<=v<=1 for v in box.values()) or box['x1']>=box['x2'] or box['y1']>=box['y2']:raise DocumentFailure('OCR_RESPONSE_INVALID')
        spans.append({'text':text,'bbox':original_box(box,transform.get('exif_orientation',1)),'layout_bbox':box,'kind':'line'})
    if sum(len(s['text']) for s in spans)>300000:raise DocumentFailure('OCR_RESPONSE_INVALID')
    return tuple(spans)


def missing_cell_read(spans,region):
    """Accept one new measured detector region wholly inside the missing cell.

    The crop is context for OCR, not evidence. Competing, crossing or vertically
    unrelated reads cannot fill a cell. No arithmetic supplies the missing value.
    """
    cell=region['cell'];selected=[]
    for span in spans:
        box=span['layout_bbox']
        overlap=min(box['y2'],cell['y2'])-max(box['y1'],cell['y1'])
        height=min(box['y2']-box['y1'],cell['y2']-cell['y1'])
        if cell['x1']<=box['x1']<box['x2']<=cell['x2'] and overlap>=height*.55:selected.append(span)
    return selected[0] if len(selected)==1 else None


class CPUOCR:
    version='rapidocr-3.9.2-onnxruntime-1.23.2-CPU-PP-OCRv6-small'
    def __init__(self,python,storage_root):
        self.python=Path(python);self.root=Path(storage_root).resolve();self.lock=threading.RLock();self.timeout_seconds=15
        self.process=None;self.metadata={}
        if not self.python.is_absolute() or not self.python.is_file() or not self.root.is_dir():raise DocumentFailure('OCR_NOT_CONFIGURED')
        self._start()
        atexit.register(self.close)

    def _start(self):
        env={'PATH':os.defpath,'LANG':'C.UTF-8','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'1'}
        try:
            self.process=subprocess.Popen([str(self.python),str(Path(__file__).with_name('rapidocr_runtime.py')),str(self.root)],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1,env=env)
        except OSError:raise DocumentFailure('OCR_NOT_CONFIGURED') from None
        try:
            data=self._read(15);validate_handshake(data)
            self.metadata={k:data[k] for k in ('packages','models','providers','cold_initialization_seconds','memory_peak_kib')}
        except DocumentFailure:self.close();raise
        except (OSError,ValueError):self.close();raise DocumentFailure('OCR_NOT_CONFIGURED') from None

    def _read(self,timeout):
        deadline=time.monotonic()+timeout
        response=bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout,selectors.EVENT_READ)
            while b'\n' not in response:
                remaining=deadline-time.monotonic()
                if remaining<=0 or not selector.select(remaining):
                    self.close();raise DocumentFailure('OCR_TIMEOUT',retryable=True)
                chunk=os.read(self.process.stdout.fileno(),min(65536,2*1024*1024+1-len(response)))
                if not chunk:self.close();raise DocumentFailure('OCR_RESPONSE_INVALID')
                response.extend(chunk)
                if len(response)>2*1024*1024:self.close();raise DocumentFailure('OCR_RESPONSE_INVALID')
        try:
            data=json.loads(response)
            if not isinstance(data,dict):raise ValueError()
            return data
        except (ValueError,UnicodeError):self.close();raise DocumentFailure('OCR_RESPONSE_INVALID') from None

    def recognize(self,path,transform):
        with self.lock:
            deadline=time.monotonic()+min(30,self.timeout_seconds)
            path=Path(path)
            if path.is_symlink() or not path.resolve().is_relative_to(self.root) or not path.is_file():raise DocumentFailure('OCR_SOURCE_SCOPE_INVALID')
            if self.process.poll() is not None:self._start()
            try:
                self.process.stdin.write(json.dumps({'path':str(path.resolve())})+'\n');self.process.stdin.flush()
                data=self._read(max(0,deadline-time.monotonic()))
            except OSError:self.close();raise DocumentFailure('OCR_FAILED') from None
            if data.get('failure'):raise DocumentFailure('OCR_FAILED')
            spans=mapped_spans(data,transform)
            from app.extraction.layout import table_retry_regions
            retries=[];elapsed=data.get('seconds',0)
            width,height=transform['derived_dimensions']
            for region in table_retry_regions({'spans':spans}):
                crop=region['crop'];pixels=[math.floor(crop['x1']*width),math.floor(crop['y1']*height),math.ceil(crop['x2']*width),math.ceil(crop['y2']*height)]
                if (pixels[2]-pixels[0])*(pixels[3]-pixels[1])*4>4000000:
                    retries.append({'field':region['field'],'status':'CROP_LIMIT'});continue
                if deadline-time.monotonic()<.1:
                    retries.append({'field':region['field'],'status':'TIME_BUDGET'});break
                try:
                    self.process.stdin.write(json.dumps({'path':str(path.resolve()),'crop':pixels})+'\n');self.process.stdin.flush()
                    retried=self._read(max(0,deadline-time.monotonic()))
                except OSError:self.close();raise DocumentFailure('OCR_FAILED') from None
                if retried.get('failure'):raise DocumentFailure('OCR_FAILED')
                actual=missing_cell_read(mapped_spans(retried,transform),region)
                elapsed+=retried.get('seconds',0)
                retries.append({'field':region['field'],'crop_extents_pixels':pixels,'scale':2,'seconds':retried.get('seconds'),
                    'status':'MEASURED_CELL_READ' if actual else 'UNRESOLVED'})
                if actual:spans=spans+(actual|{'origin':'bounded-cpu-row-retry'},)
                data=retried
            self.metadata.update(last_seconds=elapsed,memory_peak_kib=data.get('memory_peak_kib'),
                geometry_retry_version='missing-numeric-cell-v1',row_retries=retries)
            return OCRPage('\n'.join(s['text'] for s in spans),spans,'RAPIDOCR_CPU',self.version)

    def close(self):
        with self.lock:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
            if self.process:
                for stream in (self.process.stdin,self.process.stdout):
                    if stream:
                        try:stream.close()
                        except OSError:pass


def resident(python,storage_root):
    key=(str(Path(python).absolute()),str(Path(storage_root).resolve()))
    with _cache_lock:
        if key not in _instances:
            if len(_instances)>=4:
                _,old=_instances.popitem();old.close()
            _instances[key]=CPUOCR(python,storage_root)
        return _instances[key]


class FallbackOCR:
    """Only real independently configured OCR can be a fallback."""
    def __init__(self,primary,fallback):
        self.primary=primary;self.fallback=fallback;self.timeout_seconds=15;self.version=primary.version;self.metadata={}
    def recognize(self,path,transform):
        deadline=time.monotonic()+self.timeout_seconds
        self.primary.timeout_seconds=self.timeout_seconds
        try:
            result=self.primary.recognize(path,transform);self.metadata=dict(self.primary.metadata);self.version=result.version;return result
        except DocumentFailure as error:
            if not self.fallback:raise
            remaining=deadline-time.monotonic()
            if remaining<=0:raise DocumentFailure('OCR_TIMEOUT',retryable=True) from None
            self.fallback.timeout_seconds=remaining
            result=self.fallback.recognize(path,transform)
            self.version=result.version;self.metadata={'candidate_failure':error.code,'fallback':'TESSERACT'}
            return result
