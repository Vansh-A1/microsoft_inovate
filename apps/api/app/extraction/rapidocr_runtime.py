#!/usr/bin/env python3
"""Opt-in CPU-only OCR over private stdio. No network listener or downloads.

Run only in the isolated pinned candidate environment. Models are bundled in the
verified wheel; explicit paths and blocked HTTP prevent runtime downloads.
"""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import resource
import sys
import time

started=time.monotonic()
import rapidocr
import requests
import urllib.request

def offline(*args,**kwargs):raise RuntimeError('Candidate OCR has no network access')
requests.sessions.Session.request=offline
urllib.request.urlopen=offline
if version('rapidocr')!='3.9.2' or version('onnxruntime')!='1.23.2':raise RuntimeError('Candidate package pin mismatch')
root=Path(rapidocr.__file__).resolve().parent
models=root/'models'
expected={'PP-OCRv6_det_small.onnx':'090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f',
          'PP-OCRv6_rec_small.onnx':'6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884',
          'ch_ppocr_mobile_v2.0_cls_mobile.onnx':'e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c'}
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in models.glob('*.onnx')}
if any(hashes.get(name)!=sha for name,sha in expected.items()):raise RuntimeError('Bundled model hash mismatch')
params={'Det.model_path':str(models/'PP-OCRv6_det_small.onnx'),
        'Rec.model_path':str(models/'PP-OCRv6_rec_small.onnx'),
        'Cls.model_path':str(models/'ch_ppocr_mobile_v2.0_cls_mobile.onnx'),
        'EngineConfig.onnxruntime.intra_op_num_threads':2,'EngineConfig.onnxruntime.inter_op_num_threads':1,
        'EngineConfig.onnxruntime.use_cuda':False,'Global.return_word_box':True,'Global.log_level':'critical'}
engine=rapidocr.RapidOCR(params=params)
providers={name:getattr(engine,name).session.session.get_providers() for name in ('text_det','text_cls','text_rec')}
if any(value!=['CPUExecutionProvider'] for value in providers.values()):raise RuntimeError('CPU provider required')
storage_root=Path(sys.argv[1]).resolve()
if not storage_root.is_dir():raise RuntimeError('Configured local storage root required')
print(json.dumps({'ready':True,'cold_initialization_seconds':time.monotonic()-started,
    'packages':{'rapidocr':version('rapidocr'),'onnxruntime':version('onnxruntime')},
    'models':hashes,'providers':providers,'memory_peak_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'engine':'CPU ONNX; 2 intra-op threads, 1 inter-op thread; network disabled'}),flush=True)
for line in sys.stdin:
    try:
        request=json.loads(line)
        path=Path(request['path']).resolve()
        if not path.is_relative_to(storage_root) or not path.is_file() or Path(request['path']).is_symlink():raise ValueError('Scoped derived image required')
        crop=request.get('crop');offset=(0,0);scale=1
        if crop is not None:
            from PIL import Image
            if not isinstance(crop,list) or len(crop)!=4 or any(isinstance(v,bool) or not isinstance(v,int) for v in crop):raise ValueError('Integer crop bounds required')
            with Image.open(path) as image:
                x1,y1,x2,y2=crop
                if not 0<=x1<x2<=image.width or not 0<=y1<y2<=image.height or (x2-x1)*(y2-y1)*4>4000000:raise ValueError('Bounded source crop required')
                scale=2;offset=(x1,y1)
                source=image.crop((x1,y1,x2,y2)).resize(((x2-x1)*scale,(y2-y1)*scale))
            # RapidOCR accepts a PIL image; no file/network side effects.
        else:source=str(path)
        start=time.monotonic();result=engine(source);spans=[]
        if result.boxes is not None:
            for box,text,score in zip(result.boxes,result.txts,result.scores):
                points=[[float(p[0])/scale+offset[0],float(p[1])/scale+offset[1]] for p in box.tolist()]
                xs=[p[0] for p in points];ys=[p[1] for p in points]
                spans.append({'text':text,'pixels':{'x1':min(xs),'y1':min(ys),'x2':max(xs),'y2':max(ys)},
                              'polygon_pixels':points,'score_diagnostic_only':float(score)})
        word_boxes=[]
        for word_line in result.word_results or ():
            for text,score,box in word_line:
                if box is not None:
                    points=box.tolist() if hasattr(box,'tolist') else box
                    word_boxes.append({'text':text,'score_diagnostic_only':float(score),
                        'polygon_pixels':[[float(p[0])/scale+offset[0],float(p[1])/scale+offset[1]] for p in points]})
        response={'spans':spans,'word_boxes':word_boxes,'seconds':time.monotonic()-start,
            'stage_seconds':result.elapse_list,'memory_peak_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        if len(json.dumps(response))>2*1024*1024:raise ValueError('Bounded OCR response required')
        print(json.dumps(response),flush=True)
    except Exception:print(json.dumps({'failure':'CANDIDATE_OCR_FAILED'}),flush=True)
