"""Replaceable bounded CPU OCR. Word confidence is diagnostic, never eligibility."""
from dataclasses import dataclass
from io import StringIO
import csv
import os
from pathlib import Path
import subprocess
import re
from typing import Protocol
from app.documents.processor import DocumentFailure


@dataclass(frozen=True)
class OCRPage:
    text: str
    spans: tuple[dict,...]
    provider: str
    version: str


class OCRAdapter(Protocol):
    def recognize(self,path,transform) -> OCRPage: ...


class UnconfiguredOCRAdapter:
    def recognize(self,path,transform):raise DocumentFailure('OCR_NOT_CONFIGURED')


class FixtureOCRAdapter:
    def __init__(self,page):self.page=page
    def recognize(self,path,transform):return self.page


def original_box(box,orientation):
    """Exact inverse EXIF orientation on normalized pixel edges."""
    def point(u,v):
        return {1:(u,v),2:(1-u,v),3:(1-u,1-v),4:(u,1-v),5:(v,u),6:(v,1-u),7:(1-v,1-u),8:(1-v,u)}[orientation]
    points=[point(x,y) for x in (box['x1'],box['x2']) for y in (box['y1'],box['y2'])]
    return {'x1':min(x for x,y in points),'y1':min(y for x,y in points),'x2':max(x for x,y in points),'y2':max(y for x,y in points)}


class TesseractOCRAdapter:
    def __init__(self,executable,data_directory,library_directory=None,timeout_seconds=15):
        self.executable=str(Path(executable).resolve());self.data_directory=str(Path(data_directory).resolve())
        self.library_directory=library_directory;self.timeout_seconds=min(30,timeout_seconds)
        if not Path(self.executable).is_file() or not Path(self.data_directory,'eng.traineddata').is_file():raise DocumentFailure('OCR_NOT_CONFIGURED')
        env={'PATH':os.defpath,'LANG':'C.UTF-8','OMP_THREAD_LIMIT':'1'}
        if library_directory:env['LD_LIBRARY_PATH']=str(Path(library_directory).resolve())
        try:
            checked=subprocess.run([self.executable,'--version'],capture_output=True,env=env,timeout=3,check=True)
            match=re.match(rb'tesseract ([0-9.]+)',checked.stdout)
            if not match:raise ValueError()
            self.version=match[1].decode('ascii')
        except (subprocess.SubprocessError,ValueError,OSError):raise DocumentFailure('OCR_NOT_CONFIGURED') from None

    def recognize(self,path,transform):
        env={'PATH':os.defpath,'LANG':'C.UTF-8','OMP_THREAD_LIMIT':'1'}
        if self.library_directory:env['LD_LIBRARY_PATH']=str(Path(self.library_directory).resolve())
        try:
            process=subprocess.run([self.executable,str(Path(path).resolve()),'stdout','--tessdata-dir',self.data_directory,
                '-l','eng','--psm','6','tsv'],capture_output=True,env=env,timeout=self.timeout_seconds,check=False)
        except subprocess.TimeoutExpired:raise DocumentFailure('OCR_TIMEOUT',retryable=True) from None
        if process.returncode or len(process.stdout)>2*1024*1024:raise DocumentFailure('OCR_FAILED')
        groups={};width,height=transform['derived_dimensions']
        try:
            for word in csv.DictReader(StringIO(process.stdout.decode('utf-8')),delimiter='\t'):
                if word['level']!='5' or not word.get('text','').strip():continue
                key=tuple(word[k] for k in ('block_num','par_num','line_num'))
                x,y,w,h=[int(word[k]) for k in ('left','top','width','height')]
                if x<0 or y<0 or w<0 or h<0 or x+w>width or y+h>height:raise ValueError()
                groups.setdefault(key,[]).append((word['text'],x,y,w,h))
                if sum(len(v) for v in groups.values())>20000:raise ValueError()
            spans=[]
            for words in groups.values():
                text=' '.join(w[0] for w in words)
                bbox={'x1':min(w[1] for w in words)/width,'y1':min(w[2] for w in words)/height,
                    'x2':max(w[1]+w[3] for w in words)/width,'y2':max(w[2]+w[4] for w in words)/height}
                bbox=original_box(bbox,transform.get('exif_orientation',1))
                spans.append({'text':text,'bbox':bbox})
            return OCRPage('\n'.join(s['text'] for s in spans),tuple(spans),'TESSERACT',self.version)
        except (ValueError,KeyError,UnicodeError):raise DocumentFailure('OCR_RESPONSE_INVALID') from None
