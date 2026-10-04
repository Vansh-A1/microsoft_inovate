#!/usr/bin/env python3
"""Frozen fictional row-identity variants; scoring truth never enters inference."""
import argparse
from decimal import Decimal
import hashlib
from io import BytesIO
import json
import os
import subprocess
import clearledger_challenge as harness

ROOT=harness.ROOT
CORPUS=ROOT/'data/clearledger_row_identity'


def freeze():
    from reportlab.pdfgen import canvas
    import pymupdf
    from PIL import Image
    manifest=CORPUS/'manifest.json'
    if manifest.exists():return manifest
    CORPUS.mkdir(parents=True,exist_ok=True);cases=[]
    variants=[('q01',True,'blank_quantity','Times-Roman'),('q02',False,'blank_quantity','Helvetica'),
              ('q03',True,'identical_items','Courier'),('q04',False,'multi_page','Times-Roman'),
              ('q05',True,'blank_price','Helvetica'),('q06',False,'two_blank_cells','Courier')]
    for number,(identifier,scan,layout,font) in enumerate(variants,1):
        width,height=690,880;out=BytesIO();c=canvas.Canvas(out,pagesize=(width,height),invariant=1)
        rows=[{'description':'Canvas file pouches','quantity':'2','unit_price':'31.00','amount':'62.00'},
              {'description':'Blue record labels','quantity':'3','unit_price':'12.50','amount':'37.50'},
              {'description':'Canvas file pouches','quantity':'2','unit_price':'31.00','amount':'62.00'}]
        if layout in ('identical_items','multi_page'):rows=[dict(rows[0]) for _ in range(3)]
        if layout=='blank_quantity':rows[1].pop('quantity')
        if layout=='blank_price':rows[1].pop('unit_price')
        if layout=='two_blank_cells':rows[1].pop('quantity');rows[1].pop('unit_price')
        subtotal=sum(Decimal(r['amount']) for r in rows)
        headers={'vendor_name':'Fictional Juniper Paper Works','invoice_number':f'ROW-{number:03d}',
                 'invoice_date':'2026-10-03','currency':'INR','subtotal_amount':str(subtotal),
                 'tax_amount':'0.00','total_amount':str(subtotal)}
        pages=3 if layout=='multi_page' else 1
        for page in range(pages):
            c.setFont(font,13);c.drawString(45,height-35,'FICTIONAL ROW IDENTITY INVOICE')
            c.setFont(font,10)
            if page==0:
                for i,(label,field) in enumerate([('Supplier','vendor_name'),('Invoice number','invoice_number'),
                    ('Invoice date','invoice_date'),('Currency','currency'),('Subtotal','subtotal_amount'),('Tax','tax_amount'),('Total','total_amount')]):
                    x=45+(i%2)*345;y=height-82-(i//2)*26
                    c.drawString(x,y,label+':');c.drawString(x+110,y,headers[field])
            top=height-350;positions=[45,356,450,570];fields=['description','quantity','unit_price','amount']
            for x,text in zip(positions,['Description','Qty','Unit price','Amount']):c.drawString(x,top,text)
            visible=rows[page:page+1] if layout=='multi_page' else rows
            for index,row in enumerate(visible):
                for x,field in zip(positions,fields):
                    if field in row:c.drawString(x,top-34-index*57,row[field])
            c.setFont(font,8);c.drawString(45,30,f'Original invented lawful fixture. Separate printed rows; page {page+1}/{pages}.')
            c.showPage()
        c.save();path=CORPUS/(identifier+('.png' if scan else '.pdf'))
        if scan:
            with pymupdf.open(stream=out.getvalue(),filetype='pdf') as pdf:
                pix=pdf[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
                Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(path)
        else:path.write_bytes(out.getvalue())
        abstain=[]
        if 'quantity' not in rows[1]:abstain.append('lines.1.quantity')
        if 'unit_price' not in rows[1]:abstain.append('lines.1.unit_price')
        cases.append({'id':identifier,'split':'holdout','layout':layout,'source_type':'VENDOR_INVOICE',
            'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'headers':headers,'rows':rows,
            'absent':['po_reference','payment_account_token','tax_basis'],'abstain':abstain,
            'normalized':{'currency':'INR','invoice_date':'2026-10-03','total_amount':str(subtotal)}})
    manifest.write_text(json.dumps({'version':'clearledger-row-identity-v1',
        'created_before_tuning_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'provenance':'Original CC0 fictional ReportLab/PyMuPDF/Pillow sources; no customer data or downloads.',
        'limitations':'Six reserved synthetic variants, not representative customer accuracy. Legitimate equal-valued rows have separate source positions/pages.',
        'cases':cases},indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--label',default='baseline');parser.add_argument('--case',choices=[f'q{i:02d}' for i in range(1,7)])
    args=parser.parse_args();os.umask(0o077);harness.freeze=freeze;harness.CORPUS=CORPUS
    if args.freeze:print(freeze())
    else:harness.run('rows-'+args.label,'holdout',only=args.case,production_rapid=True)
