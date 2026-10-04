#!/usr/bin/env python3
"""Lawful fictional corpus, immutable splits and actual local extraction metrics.

No source truth enters the extraction input or model prompt. Holdout families
are reserved before tuning; they are not representative customer invoices.
All dates, names, addresses and prices are invented fixture facts, not policy.
"""
import argparse
import base64
from dataclasses import replace
from decimal import Decimal
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/api'))
CORPUS=ROOT/'data/clearledger_challenge'


def freeze():
    from reportlab.pdfgen import canvas
    import pymupdf
    from PIL import Image
    manifest=CORPUS/'manifest.json'
    if manifest.exists(): return manifest
    CORPUS.mkdir(parents=True,exist_ok=True)
    # Each holdout layout family differs from the tuning page geometry. Truth
    # is retained for post-extraction scoring only. Never tune on holdout output.
    designs=[
        ('t01','tuning','side',False,1),
        ('t02','tuning','stacked',False,1),
        ('t03','tuning','wrapped',False,1),
        ('t04','tuning','grid',True,1),
        ('t05','tuning','sparse',True,1),
        ('t06','tuning','corrupt',False,1),
        ('h01','holdout','landscape',False,1),
        ('h02','holdout','continuation',False,3),
        ('h03','holdout','cards',True,1),
        ('h04','holdout','wrapped_scan',True,1),
        ('h05','holdout','conflicting',False,2),
        ('h06','holdout','ambiguous',False,1),
    ]
    cases=[]
    for number,(identifier,split,layout,scan,pages) in enumerate(designs,1):
        if layout=='corrupt':
            path=CORPUS/(identifier+'.pdf');path.write_bytes(b'%PDF-1.7\nnot a valid object tree\n')
            case={'id':identifier,'split':split,'layout':layout,'source_type':'VENDOR_INVOICE',
                  'path':path.name,'expected_failure':'CORRUPT_DOCUMENT','headers':{},'rows':[],'absent':[],'abstain':[]}
        else:
            wide=layout=='landscape';width,height=(842,595) if wide else (612,792)
            buf=BytesIO();c=canvas.Canvas(buf,pagesize=(width,height),invariant=1)
            font='Times-Roman' if split=='holdout' else 'Helvetica'
            currency='EUR' if wide else ('USD' if layout=='cards' else 'INR')
            ambiguous=layout in ('ambiguous','sparse')
            if ambiguous:currency='$'
            invoice='CL-FICTION-'+str(number)
            date='03/04/2026' if ambiguous else ('17 Sep 2026' if wide else '2026-09-17')
            rows=[{'description':'Notebook cases','quantity':'2','unit_price':'75.00','amount':'150.00'},
                  {'description':'Archive folders','quantity':'1','unit_price':'50.00','amount':'50.00'}]
            if layout in ('wrapped','wrapped_scan'):rows[0]['description']='Notebook cases recycled paper'
            if layout=='continuation': rows=[{'description':text,'quantity':'1','unit_price':'50.00','amount':'50.00'} for text in ('Index dividers','Card holders','Paper wallets')]
            subtotal=sum(Decimal(row['amount']) for row in rows)
            tax=subtotal*Decimal('0.18');total=subtotal+tax
            truth={'vendor_name':'Fictional Willow Office Ltd','invoice_number':invoice,'invoice_date':date,
                   'currency':currency,'subtotal_amount':format(subtotal,'.2f'),'tax_amount':format(tax,'.2f'),'total_amount':format(total,'.2f')}
            base=[('Supplier','vendor_name'),('Invoice number','invoice_number'),('Invoice date','invoice_date'),
                  ('Currency','currency'),('Subtotal','subtotal_amount'),('Tax','tax_amount'),('Total','total_amount')]
            if layout=='grid':base=[('Vendor','vendor_name'),('Invoice #','invoice_number'),('Invoice date','invoice_date'),
                                     ('Currency','currency'),('Subtotal','subtotal_amount'),('Sales tax','tax_amount'),('Total','total_amount')]
            if wide:base=[('Seller','vendor_name'),('Invoice ID','invoice_number'),('Issue date','invoice_date'),
                          ('Currency','currency'),('Sub total','subtotal_amount'),('Sales tax','tax_amount'),('Grand total','total_amount')]
            for page in range(pages):
                c.setFont(font,15);c.drawString(32,height-30,'FICTIONAL INVOICE · LOCAL BENCHMARK')
                c.setFont(font,10)
                if layout!='continuation' or page==0:
                    for i,(label,field) in enumerate(base):
                        value=truth[field]
                        if layout=='conflicting' and page==1 and field=='invoice_number':value+='-SECOND'
                        if layout in ('stacked','cards'):
                            column=i%2;row=i//2;x=32+column*290;y=height-78-row*53
                            c.setFont(font,9);c.drawString(x,y,label+':')
                            c.setFont(font,11);c.drawString(x,y-18,value)
                        elif wide:
                            x=32+(i%3)*270;y=height-72-(i//3)*42
                            c.drawString(x,y,label+':');c.drawString(x+92,y,value)
                        else:
                            x=32+(i%2)*290;y=height-70-(i//2)*24
                            c.drawString(x,y,label+':');c.drawString(x+110,y,value)
                    if not ambiguous:
                        # Explicitly printed accounting semantics. No absent zero
                        # is treated as printed, no invoice-derived policy.
                        extras=[('Tax basis','EXCLUSIVE'),('Discount','0.00'),('Shipping','0.00'),('Other charges','0.00')]
                        y=height-285 if layout in ('stacked','cards') else height-183
                        for i,(label,value) in enumerate(extras):c.drawString(32,y-i*17,label+': '+value)
                top=height-390 if layout in ('stacked','cards') else (height-300 if not wide else height-245)
                positions=[32,310,385,490] if not wide else [32,440,570,730]
                headers=['Description','Qty','Unit price','Amount']
                if layout=='continuation':positions=[32,155,270,400];headers=['Amount','Qty','Description','Unit price']
                c.setFont(font,10)
                for x,label in zip(positions,headers):c.drawString(x,top,label)
                page_rows=rows[page:page+1] if layout=='continuation' else rows
                for ri,row in enumerate(page_rows):
                    y=top-28-ri*45
                    values=[row[k] for k in ('description','quantity','unit_price','amount')]
                    if layout=='continuation':values=[row[k] for k in ('amount','quantity','description','unit_price')]
                    if layout in ('wrapped','wrapped_scan') and ri==0:values[0]='Notebook cases'
                    for x,value in zip(positions,values):c.drawString(x,y,value)
                    if layout in ('wrapped','wrapped_scan') and ri==0:c.drawString(positions[0],y-14,'recycled paper')
                if layout=='grid':
                    c.setLineWidth(.6)
                    for y in (top+14,top-13,top-58,top-103):c.line(30,y,580,y)
                    for x in (30,295,372,477,580):c.line(x,top+14,x,top-103)
                c.setFont(font,8);c.drawString(32,28,f'Invented lawful fixture; no customer data or business policy. Page {page+1}/{pages}.')
                c.showPage()
            c.save();path=CORPUS/(identifier+('.png' if scan else '.pdf'))
            if scan:
                with pymupdf.open(stream=buf.getvalue(),filetype='pdf') as pdf:
                    pix=pdf[0].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6),alpha=False)
                    im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                    if layout=='sparse':im=im.convert('L')
                    im.save(path,format='PNG')
            else:path.write_bytes(buf.getvalue())
            case={'id':identifier,'split':split,'layout':layout,'source_type':'VENDOR_INVOICE','path':path.name,
                  'headers':truth,'rows':rows if layout!='conflicting' else rows*2,
                  'absent':['payment_account_token','po_reference']+(['tax_basis','document_discount_amount','shipping_amount','other_charges_amount'] if ambiguous else []),
                  'abstain':['currency','invoice_date'] if ambiguous else [],
                  'normalized':{} if ambiguous else {'currency':currency,'invoice_date':'2026-09-17','total_amount':format(total,'.2f')}}
            if layout=='conflicting':
                case['headers'].pop('invoice_number');case['abstain']=['invoice_number'];case['required_diagnostics']=['SEGMENTATION_UNCERTAIN']
        case['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();cases.append(case)
    manifest.write_text(json.dumps({'version':'clearledger-challenge-v1','created_before_tuning_commit':'88f3559094a83408147157c618a20271e19208b1',
        'provenance':'Generated locally by this script with ReportLab/PyMuPDF/Pillow; all source facts invented. No downloaded or private invoices.',
        'limitations':'Six tuning and six reserved layout families, not an independently sourced customer accuracy benchmark. Holdout expectations never enter inference.',
        'cases':cases},indent=2)+'\n')
    return manifest


def run(label,split,force_vlm=False,only=None,rapid=False,production_rapid=False):
    from app.core.config import Settings
    from app.core.identity import Identity
    from app.db.models import Base
    from app.documents.processor import DocumentProcessor
    from app.integrations.storage import LocalStorage
    from app.services.document_worker import extract
    from app.domain.extraction import to_data
    from app.documents.normalizer import Normalizer,validate_draft
    manifest=freeze();settings=Settings.load();providers=settings.document_providers
    os.environ[providers.gateway_token_env]=(ROOT/'runtime/inference/gateway.key').read_text().strip()
    if force_vlm:providers=replace(providers,ocr_executable=None,ocr_data_directory=None,ocr_library_directory=None,ocr_backend='TESSERACT',ocr_python=None)
    elif production_rapid:providers=replace(providers,ocr_backend='RAPIDOCR_CPU_EXPERIMENTAL',ocr_python=str(ROOT/'runtime/ocr-rapid/.venv/bin/python'))
    identity=Identity(uuid4(),uuid4(),uuid4(),frozenset({'FINANCE_REVIEWER'}),'Fictional challenge validation')
    candidate_ocr=None
    if rapid:
        from rapidocr_candidate import RapidCandidate
        from app.services import document_worker
        candidate_ocr=RapidCandidate()
        # Experimental adapter injection; the actual production pipeline is
        # reused, but default application configuration is never changed.
        document_worker.TesseractOCRAdapter=lambda *a,**kw:candidate_ocr
    storage=LocalStorage(ROOT/'runtime/clearledger/challenge-storage');results=[]
    output=ROOT/'runtime/clearledger'/('challenge-'+label+'-'+split+('.force-vlm' if force_vlm else '')+'.json')
    if output.exists():raise RuntimeError('Benchmark output already exists; use a fresh label')
    git=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    code_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [ROOT/'apps/api/app/extraction'/n for n in ('layout.py','native.py','typellm.py','cpu_ocr.py','rapidocr_runtime.py')]+[ROOT/'apps/api/app/services/document_worker.py'] if p.is_file()}
    for case in json.loads(manifest.read_text())['cases']:
        if case['split']!=split or only and case['id']!=only:continue
        source=manifest.parent/case['path']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=case['sha256']:raise RuntimeError('Frozen source changed')
        samples=[];stop=threading.Event()
        def monitor():
            while not stop.is_set():
                try:samples.append(int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True,timeout=2).strip().splitlines()[0]))
                except (OSError,ValueError,subprocess.SubprocessError):pass
                stop.wait(.25)
        thread=threading.Thread(target=monitor,daemon=True);thread.start();started=time.monotonic()
        data={'id':case['id'],'split':split,'source_sha256':case['sha256']}
        try:
            pages=DocumentProcessor().process(source)['pages'];data['preprocess_seconds']=round(time.monotonic()-started,3)
            for page in pages:page['preview_key'],_=storage.put(identity,base64.b64decode(page.pop('preview_base64')),maximum=settings.document_limits.maximum_derived_bytes)
            result,diagnostics,routing=extract({'id':uuid4(),'source_type':case['source_type']},identity,pages,storage,providers)
            if candidate_ocr:
                result=replace(result,metadata=replace(result.metadata,adapter_id='experimental-rapidocr-'+result.metadata.adapter_id,
                    model_id=candidate_ocr.version if result.metadata.provider_id=='LOCAL_OCR' else result.metadata.model_id,
                    runtime_versions=result.metadata.runtime_versions+(__import__('app.domain.extraction',fromlist=['VersionMetadata']).VersionMetadata('ocr_candidate',candidate_ocr.version),)))
            observed=to_data(result)
            observations=[o|{'id':str(uuid4())} for o in observed['header_fields']]
            observations += [o|{'id':str(uuid4()),'field_path':f'lines.{row["row_index"]-1}.{o["field_path"]}'} for row in observed['line_items'] for o in row['fields']]
            candidate,traces,findings=Normalizer().normalize(observations)
            findings+=validate_draft(candidate,traces,case['source_type'],diagnostics)
            by={o['field_path']:o for o in observed['header_fields']}
            header={k:by.get(k,{}).get('raw_value')==v and by.get(k,{}).get('state')=='PRESENT' for k,v in case['headers'].items()}
            rows=[];unsupported_rows=[];unsupported_canonical=[]
            for i,expected in enumerate(case['rows']):
                actual={o['field_path']:o for o in observed['line_items'][i]['fields']} if i<len(observed['line_items']) else {}
                rows.extend(actual.get(k,{}).get('raw_value')==v and actual.get(k,{}).get('state')=='PRESENT' for k,v in expected.items())
                unsupported_rows.extend({'row':i+1,'field':k,'raw':o.get('raw_value')} for k,o in actual.items() if k not in expected and o.get('state')=='PRESENT')
                unsupported_canonical.extend({'row':i+1,'field':k,'value':candidate.get(f'lines.{i}.{k}')} for k in actual if k not in expected and candidate.get(f'lines.{i}.{k}') is not None)
            absent={k:by.get(k,{}).get('state')=='MISSING' and by.get(k,{}).get('raw_value') is None for k in case['absent']}
            abstain={k:candidate.get(k) is None for k in case['abstain']}
            unsupported={k:by.get(k,{}).get('raw_value') for k in case['absent'] if by.get(k,{}).get('state')=='PRESENT'}
            data.update(observed=observed,candidate=candidate,traces=traces,findings=findings,routing=routing,diagnostics=diagnostics,
                header_checks=header,row_matches=sum(rows),row_checked=len(rows),expected_rows=len(case['rows']),actual_rows=len(observed['line_items']),
                absent_checks=absent,abstention_checks=abstain,unsupported_present=unsupported,unsupported_row_present=unsupported_rows,
                unsupported_row_canonical=unsupported_canonical,
                normalized_checks={k:candidate.get(k)==v for k,v in case.get('normalized',{}).items()},
                diagnostic_checks={k:k in diagnostics for k in case.get('required_diagnostics',[])},
                source_located=sum(bool(o.get('source')) for o in observations if o['state']=='PRESENT'),
                present_observations=sum(o['state']=='PRESENT' for o in observations),
                state='NEEDS_INPUT' if findings else 'READY',finance_decision=None)
        except Exception as error:data['failure']=getattr(error,'code',type(error).__name__)
        finally:stop.set();thread.join(timeout=3)
        data.update(seconds=round(time.monotonic()-started,3),peak_whole_device_memory_mib=max(samples) if samples else None)
        if case.get('expected_failure'):data['failure_expected']=data.get('failure')==case['expected_failure']
        results.append(data)
        output.write_text(json.dumps({'version':'clearledger-challenge-run-v1','label':label,'code_commit':git,'code_sha256':code_hashes,'split':split,
            'temperature':'Resident model; first request after idle then sequential requests. Not cold weight loading.',
            'force_vlm':force_vlm,'ocr_candidate':None if not candidate_ocr else {'startup':candidate_ocr.startup,'metrics':candidate_ocr.metrics},
            'limitations':'Pipeline timing excludes upload/database queue/UI and candidate OCR startup, which is reported separately. VRAM is whole device including resident weights and other processes. No accuracy claim beyond these fictional sources.',
            'cases':results},indent=2)+'\n')
        # Baseline holdout results remain sealed until tuning is complete.
        if split=='holdout' and label=='baseline':print(json.dumps({'id':case['id'],'baseline_sealed':True}),flush=True)
        else:print(json.dumps({k:v for k,v in data.items() if k not in ('observed','candidate','traces','findings','routing','diagnostics')}),flush=True)
    if candidate_ocr:candidate_ocr.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',action='store_true');parser.add_argument('--label',default='baseline')
    parser.add_argument('--split',choices=['tuning','holdout'],default='tuning');parser.add_argument('--force-vlm',action='store_true')
    parser.add_argument('--case')
    parser.add_argument('--rapid-candidate',action='store_true')
    parser.add_argument('--rapid-production',action='store_true')
    args=parser.parse_args();os.umask(0o077)
    if args.freeze:print(freeze())
    else:run(args.label,args.split,args.force_vlm,args.case,args.rapid_candidate,args.rapid_production)
