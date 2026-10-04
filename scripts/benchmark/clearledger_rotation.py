#!/usr/bin/env python3
"""Frozen original fictional rotation families; truth is post-output scoring only."""
import argparse
from decimal import Decimal
import hashlib
from io import BytesIO
import json
import math
import os
from pathlib import Path
import subprocess
import clearledger_challenge as harness

ROOT=harness.ROOT
CORPUS=ROOT/'data/clearledger_rotation'


def freeze():
    from reportlab.pdfgen import canvas
    import pymupdf
    from PIL import Image
    target=CORPUS/'manifest.json'
    if target.exists():return target
    CORPUS.mkdir(parents=True,exist_ok=True)
    definitions=[('development','tuning',(900,620),'Helvetica',[
        {'description':'Cork shelf pads','quantity':'3','unit_price':'14.25','amount':'42.75'},
        {'description':'Metal label clips','quantity':'8','unit_price':'2.50','amount':'20.00'},
        {'description':'Archive sleeves','quantity':'2','unit_price':'9.75','amount':'19.50'}]),
        ('reserved_landscape','holdout',(920,660),'Courier',[
        {'description':'Canvas desk rails','quantity':'4','unit_price':'16.50','amount':'66.00'},
        {'description':'Ink label ribbons','quantity':'6','unit_price':'7.25','amount':'43.50'},
        {'description':'Slate index boards','quantity':'3','unit_price':'11.00','amount':'33.00'}]),
        ('reserved_portrait','holdout',(740,940),'Times-Roman',[
        {'description':'Natural paper covers','quantity':'2','unit_price':'27.50','amount':'55.00'},
        {'description':'Braided file loops','amount':'18.75'},
        {'description':'Brass shelf markers','quantity':'5','unit_price':'3.25','amount':'16.25'}])]
    bases={};base_sources=[]
    for n,(family,split,size,font,rows) in enumerate(definitions,1):
        width,height=size;out=BytesIO();c=canvas.Canvas(out,pagesize=size,invariant=1)
        subtotal=sum(Decimal(r['amount']) for r in rows)
        truth={'vendor_name':f'Fictional Rotation Workshop {n}','invoice_number':f'ROT-2026-{n:03d}',
            'invoice_date':'2026-10-04','currency':'INR','subtotal_amount':format(subtotal,'.2f'),
            'tax_amount':'0.00','total_amount':format(subtotal,'.2f')}
        c.setFillColorRGB(.1,.2,.23);c.setFont(font,19);c.drawString(44,height-48,'FICTIONAL SUPPLY STATEMENT')
        c.setFillColorRGB(0,0,0);c.setFont(font,11)
        if family=='development':
            # Left identity panel beside a compact right table, unlike the old
            # two-column headers over a full-width table.
            for i,(label,field) in enumerate([('Supplier','vendor_name'),('Invoice number','invoice_number'),('Invoice date','invoice_date'),('Currency','currency')]):
                y=height-104-i*42;c.drawString(44,y,label+':');c.drawString(44,y-17,truth[field])
            positions=[410,650,710,810];top=height-122
            c.setStrokeColorRGB(.25,.4,.45);c.line(365,80,365,height-80)
            summary_x=620;summary_y=160
        elif family=='reserved_landscape':
            for i,(label,field) in enumerate([('Invoice number','invoice_number'),('Invoice date','invoice_date'),('Currency','currency')]):
                y=height-100-i*27;c.drawString(540,y,label+':');c.drawString(710,y,truth[field])
            c.drawString(44,height-110,'Supplier:');c.drawString(44,height-133,truth['vendor_name'])
            positions=[72,455,575,765];top=height-240;summary_x=610;summary_y=155
            c.setLineWidth(.8);c.rect(44,top-171,width-88,201)
        else:
            c.setLineWidth(.7);c.rect(32,54,width-64,height-120)
            for i,(label,field) in enumerate([('Supplier','vendor_name'),('Invoice number','invoice_number'),('Invoice date','invoice_date'),('Currency','currency')]):
                y=height-112-i*32;c.drawString(62,y,label+':');c.drawString(225,y,truth[field])
            positions=[62,370,470,610];top=height-330;summary_x=430;summary_y=220
        for x,label in zip(positions,['Description','Qty','Unit price','Amount']):c.drawString(x,top,label)
        for i,row in enumerate(rows):
            y=top-39-i*51
            for x,field in zip(positions,['description','quantity','unit_price','amount']):
                if field in row:c.drawString(x,y,row[field])
        for i,(label,field) in enumerate([('Subtotal','subtotal_amount'),('Tax','tax_amount'),('Total','total_amount')]):
            y=summary_y-i*27;c.drawString(summary_x,y,label+':');c.drawString(summary_x+120,y,truth[field])
        c.setFont(font,8);c.drawString(44,25,'Original invented CC0 fixture. No customer data, corporate policy or payment authority.')
        c.save();pdf=out.getvalue();path=CORPUS/(family+'.pdf');path.write_bytes(pdf)
        with pymupdf.open(stream=pdf,filetype='pdf') as doc:
            pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6),alpha=False)
            image=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        bases[family]=(image,truth,rows,split)
        base_sources.append({'family':family,'path':path.name,'sha256':hashlib.sha256(pdf).hexdigest()})
    variants=[('d01','development',0),('d02','development',6),('d03','development',90),
        ('r01','reserved_landscape',0),('r02','reserved_landscape',90),('r03','reserved_landscape',180),
        ('r04','reserved_landscape',270),('r05','reserved_landscape',4),
        ('r06','reserved_portrait',-5),('r07','reserved_portrait',90)]
    cases=[]
    for identifier,family,angle in variants:
        image,truth,rows,split=bases[family]
        derived=image.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC,fillcolor='white') if angle else image.copy()
        path=CORPUS/(identifier+'.png');derived.save(path)
        missing=[f'lines.{i}.{f}' for i,row in enumerate(rows) for f in ('quantity','unit_price') if f not in row]
        cases.append({'id':identifier,'split':split,'layout':family,'rotation_degrees_ccw':angle,
            'source_type':'VENDOR_INVOICE','path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'dimensions':list(derived.size),'headers':truth,'rows':rows,
            'absent':['tax_basis','document_discount_amount','shipping_amount','other_charges_amount','po_reference','payment_account_token'],
            'abstain':missing,'normalized':{'currency':'INR','invoice_date':'2026-10-04','total_amount':truth['total_amount']}})
    target.write_text(json.dumps({'version':'clearledger-rotation-truth-v1',
        'created_before_tuning_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'provenance':'Original CC0 fictional ReportLab/PyMuPDF/Pillow content, frozen before rotation implementation; no downloaded or private invoices.',
        'limitations':'Three development rotations of one family, seven reserved rotations of two NEW synthetic families. Rotations are correlated variants, not ten independent layouts or real-company accuracy. Expected rotations never enter extraction.',
        'base_sources':base_sources,'cases':cases},indent=2)+'\n')
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--label',default='baseline');parser.add_argument('--split',choices=['tuning','holdout'],default='tuning');parser.add_argument('--case');parser.add_argument('--cpu-only',action='store_true')
    args=parser.parse_args();os.umask(0o077);harness.freeze=freeze;harness.CORPUS=CORPUS
    if args.freeze:print(freeze())
    else:harness.run('rotation-'+args.label,args.split,only=args.case,production_rapid=True,cpu_only=args.cpu_only)
