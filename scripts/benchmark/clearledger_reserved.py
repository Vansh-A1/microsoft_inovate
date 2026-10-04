#!/usr/bin/env python3
"""Fresh fictional reserved variants for CL-06; truth never enters extraction.

Freeze once before tuning. Previous h01/h04 are spent regression layouts.
This remains a small synthetic layout benchmark, not customer accuracy evidence.
"""
import argparse
from decimal import Decimal
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import clearledger_challenge as harness

ROOT=harness.ROOT
CORPUS=ROOT/'data/clearledger_reserved'


def freeze():
    from reportlab.pdfgen import canvas
    import pymupdf
    from PIL import Image
    manifest=CORPUS/'manifest.json'
    if manifest.exists():return manifest
    CORPUS.mkdir(parents=True,exist_ok=True)
    variants=[('r01',False,'landscape','Helvetica',False),
              ('r02',False,'unknown_header','Courier',False),
              ('r03',False,'continuation','Times-Roman',False),
              ('r04',True,'wrapped','Times-Roman',False),
              ('r05',True,'wrapped','Helvetica',False),
              ('r06',True,'wrapped','Courier',True),
              ('r07',True,'missing_quantity','Times-Roman',False),
              ('r08',False,'conflicting','Helvetica',False)]
    cases=[]
    for index,(identifier,scan,layout,font,ambiguous) in enumerate(variants,1):
        width,height=(900,640) if layout=='landscape' else (660,840)
        out=BytesIO();c=canvas.Canvas(out,pagesize=(width,height),invariant=1)
        rows=[{'description':'Felt document sleeves','quantity':'3','unit_price':'24.50','amount':'73.50'},
              {'description':'Desk index tabs','quantity':'1','unit_price':'19.25','amount':'19.25'},
              {'description':'Binder spines','quantity':'4','unit_price':'6.75','amount':'27.00'}]
        if layout=='wrapped':rows[0]['description']+=' assorted colors'
        subtotal=sum(Decimal(r['amount']) for r in rows);tax=Decimal('0.00');total=subtotal
        currency='$' if ambiguous else ('EUR' if index%2 else 'INR')
        date='04/05/2026' if ambiguous else '2026-10-02'
        truth={'vendor_name':'Fictional Harbor Stationery Co','invoice_number':f'RS-{index:03d}',
               'invoice_date':date,'currency':currency,'subtotal_amount':str(subtotal),
               'tax_amount':str(tax),'total_amount':str(total)}
        labels=[('Supplier','vendor_name'),('Invoice number','invoice_number'),('Invoice date','invoice_date'),
                ('Currency','currency'),('Subtotal','subtotal_amount'),('Tax','tax_amount'),('Total','total_amount')]
        if layout=='landscape':labels[:3]=[('Seller','vendor_name'),('Invoice ID','invoice_number'),('Issue date','invoice_date')]
        if layout=='unknown_header':labels[0]=('Trading entity','vendor_name')
        pages=3 if layout=='continuation' else (2 if layout=='conflicting' else 1)
        for page in range(pages):
            c.setFont(font,13);c.drawString(40,height-35,'FICTIONAL RESERVED INVOICE')
            c.setFont(font,10)
            if layout!='continuation' or page==0:
                for i,(label,field) in enumerate(labels):
                    if layout=='landscape':x=40+(i%3)*280;y=height-80-(i//3)*37
                    else:x=40+(i%2)*325;y=height-80-(i//2)*27
                    value=truth[field]+('-B' if layout=='conflicting' and page==1 and field=='invoice_number' else '')
                    c.drawString(x,y,label+':');c.drawString(x+115,y,value)
                for i,(label,value) in enumerate([('Discount','0.00'),('Shipping','0.00'),('Other charges','0.00')]):
                    c.drawString(40,height-220-i*18,label+': '+value)
                # No tax basis is printed; extraction must not invent it.
            top=height-345
            positions=[40,344,425,545] if width==660 else [40,462,606,775]
            keys=['description','quantity','unit_price','amount'];headings=['Description','Qty','Unit price','Amount']
            if layout=='continuation':keys=['amount','description','quantity','unit_price'];headings=['Amount','Description','Qty','Unit price'];positions=[40,150,450,540]
            for x,label in zip(positions,headings):c.drawString(x,top,label)
            page_rows=rows[page:page+1] if layout=='continuation' else rows
            for ri,row in enumerate(page_rows):
                y=top-33-ri*55
                for x,key in zip(positions,keys):
                    if layout=='missing_quantity' and ri==1 and key=='quantity':continue
                    value='Felt document sleeves' if layout=='wrapped' and ri==0 and key=='description' else row[key]
                    c.drawString(x,y,value)
                if layout=='wrapped' and ri==0:c.drawString(positions[0],y-16,'assorted colors')
            c.setFont(font,8);c.drawString(40,30,f'Invented lawful source; no customer data. Page {page+1}/{pages}.')
            c.showPage()
        c.save();path=CORPUS/(identifier+('.png' if scan else '.pdf'))
        if scan:
            with pymupdf.open(stream=out.getvalue(),filetype='pdf') as pdf:
                pix=pdf[0].get_pixmap(matrix=pymupdf.Matrix(1.45,1.45),alpha=False)
                im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                if ambiguous:im=im.convert('L')
                im.save(path)
        else:path.write_bytes(out.getvalue())
        checked_rows=[dict(r) for r in rows]*(2 if layout=='conflicting' else 1)
        if layout=='missing_quantity':checked_rows[1].pop('quantity')
        abstain=['currency','invoice_date'] if ambiguous else []
        if layout=='missing_quantity':abstain+=['lines.1.quantity'];checked_rows=[]
        diagnostics=[]
        if layout=='conflicting':truth.pop('invoice_number');abstain+=['invoice_number'];diagnostics=['SEGMENTATION_UNCERTAIN']
        cases.append({'id':identifier,'split':'holdout','layout':layout,'source_type':'VENDOR_INVOICE','path':path.name,
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'headers':truth,'rows':checked_rows,
                      'absent':['po_reference','payment_account_token','tax_basis'],'abstain':abstain,
                      'required_diagnostics':diagnostics,
                      'normalized':{} if ambiguous else {'currency':currency,'invoice_date':'2026-10-02','total_amount':str(total)}})
    manifest.write_text(json.dumps({'version':'clearledger-reserved-v1',
        'created_before_tuning_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'provenance':'Original CC0 fictional ReportLab/PyMuPDF/Pillow sources; no downloads/private data.',
        'limitations':'Eight synthetic variants reserved before CL-06 tuning. Shared vocabulary, no customer distribution or supervised truth.',
        'cases':cases},indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',action='store_true');parser.add_argument('--label',required=False,default='baseline')
    parser.add_argument('--case',choices=[f'r{i:02d}' for i in range(1,9)])
    args=parser.parse_args();os.umask(0o077)
    harness.freeze=freeze;harness.CORPUS=CORPUS
    if args.freeze:print(freeze())
    else:harness.run('reserved-'+args.label,'holdout',only=args.case,production_rapid=True)
