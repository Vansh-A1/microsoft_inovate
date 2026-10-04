"""Conservative measured grid-row crops; never fabricate field boxes.

Only one full-width, regularly spaced ruled table is supported. A crop is used
only when its measured row count agrees with the real model's inventory. Each
composite retains separate header/row extents back to the stored page preview.
"""
import base64
import hashlib
from io import BytesIO
from PIL import Image

VERSION='ruled-table-crops-v1'


def row_crops(content,maximum_rows=200):
    import cv2,numpy as np
    cv2.setNumThreads(1)
    with Image.open(BytesIO(content)) as decoded:
        if max(decoded.size)>3000 or decoded.width*decoded.height>9_000_000:return []
        image=decoded.convert('RGB')
    gray=np.asarray(image.convert('L'))
    mask=cv2.threshold(gray,210,255,cv2.THRESH_BINARY_INV)[1]
    # Odd width keeps the morphology anchor centered on the original pixels.
    lines=cv2.morphologyEx(mask,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(max(31,(image.width//3)|1),1)))
    contours,_=cv2.findContours(lines,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    rects=sorted([cv2.boundingRect(c) for c in contours if cv2.boundingRect(c)[2]>=image.width*.65 and cv2.boundingRect(c)[3]<=6],key=lambda b:b[1])
    if not 3<=len(rects)<=maximum_rows+2:return []
    gaps=[b[1]-a[1] for a,b in zip(rects,rects[1:])]
    if min(gaps)<12 or max(gaps)>min(gaps)*1.6:return []
    if max(b[0] for b in rects)-min(b[0] for b in rects)>image.width*.03:return []
    if max(b[2] for b in rects)-min(b[2] for b in rects)>image.width*.03:return []
    x1=min(b[0] for b in rects);x2=max(b[0]+b[2] for b in rects)
    header=(x1,rects[0][1],x2,rects[1][1]+rects[1][3]);out=[]
    for a,b in zip(rects[1:-1],rects[2:]):
        extent=(x1,a[1],x2,b[1]+b[3]);heading=image.crop(header);row=image.crop(extent)
        composite=Image.new('RGB',(heading.width,heading.height+row.height+8),'white')
        composite.paste(heading,(0,0));composite.paste(row,(0,heading.height+8))
        output=BytesIO();composite.save(output,format='PNG');png=output.getvalue()
        out.append((png,{'version':VERSION,'preview_dimensions':list(image.size),'derived_dimensions':list(composite.size),
            'header_extent_pixels':list(header),'row_extent_pixels':list(extent),'header_offset_pixels':[0,0],
            'row_offset_pixels':[0,heading.height+8],'rotation':0,'scale':[1,1],'sha256':hashlib.sha256(png).hexdigest(),
            'field_bbox':None}))
    return out
