"""Measured OCR layout alignment; original pixels and source boxes never change.

Four orthogonal candidates use independently printed headers/tables, not model
confidence, fixture identities, declared source rotations or finance outcomes.
Small global deskew uses actual text quadrilaterals. This is layout geometry,
not image resampling or perspective reconstruction. Unknown/tied cases abstain.
"""
import math
import re
from statistics import median
from app.extraction.layout import printed_layout

VERSION='measured-ocr-layout-alignment-v1'


def affine(width,height,degrees):
    radians=math.radians(degrees);c=math.cos(radians);s=math.sin(radians)
    points=[(c*x-s*y,s*x+c*y) for x in (0,width) for y in (0,height)]
    ox=min(x for x,y in points);oy=min(y for x,y in points)
    return {'matrix':[c,-s,-ox,s,c,-oy],
        'source_dimensions':[width,height],
        'layout_dimensions':[max(x for x,y in points)-ox,max(y for x,y in points)-oy]}


def point(x,y,transform,inverse=False):
    a,b,c,d,e,f=transform['matrix']
    if inverse:
        determinant=a*e-b*d
        if not math.isfinite(determinant) or abs(determinant-1)>1e-6:raise ValueError('Rigid measured transform required')
        return ((e*(x-c)-b*(y-f))/determinant,(-d*(x-c)+a*(y-f))/determinant)
    return a*x+b*y+c,d*x+e*y+f


def aligned_spans(spans,transform):
    width,height=transform['layout_dimensions'];out=[]
    for span in spans:
        polygon=span.get('polygon_layout_pixels')
        if polygon is None:raise ValueError('Measured polygon required')
        pts=[point(x,y,transform) for x,y in polygon]
        box={'x1':min(x for x,y in pts)/width,'x2':max(x for x,y in pts)/width,
             'y1':min(y for x,y in pts)/height,'y2':max(y for x,y in pts)/height}
        if any(not math.isfinite(v) or not -1e-6<=v<=1+1e-6 for v in box.values()):raise ValueError('Geometry outside source canvas')
        box={k:min(1,max(0,v)) for k,v in box.items()}
        # Original bbox/polygon are immutable measured evidence; only layout changes.
        out.append(span|{'layout_bbox':box,'layout_axis_pixels':[max(x for x,y in pts)-min(x for x,y in pts),max(y for x,y in pts)-min(y for x,y in pts)]})
    return tuple(out)


def crop_pixels(crop,transform):
    """Back-project context extents, not field boxes, onto the stored preview."""
    width,height=transform['layout_dimensions'];sw,sh=transform['source_dimensions']
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in crop.values()):raise ValueError('Bounded layout crop required')
    pts=[point(x*width,y*height,transform,True) for x in (crop['x1'],crop['x2']) for y in (crop['y1'],crop['y2'])]
    bounds=[max(0,math.floor(min(x for x,y in pts))),max(0,math.floor(min(y for x,y in pts))),
        min(sw,math.ceil(max(x for x,y in pts))),min(sh,math.ceil(max(y for x,y in pts)))]
    if not bounds[0]<bounds[2] or not bounds[1]<bounds[3]:raise ValueError('Empty source crop')
    return bounds


def residual_angle(spans):
    angles=[]
    for span in spans:
        q=span.get('polygon_layout_pixels')
        if q is None:continue
        edges=[(math.hypot(b[0]-a[0],b[1]-a[1]),a,b) for a,b in ((q[0],q[1]),(q[1],q[2]))]
        long,short=sorted(edges,key=lambda edge:edge[0],reverse=True)
        if long[0]<35 or long[0]<short[0]*2:continue
        _,a,b=long;angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
        angles.append((angle+45)%90-45)
    if len(angles)<5:return 0,{'deskew_status':'INSUFFICIENT_MEASURED_BASELINES','baseline_count':len(angles)}
    center=median(angles);support=[a for a in angles if abs(a-center)<=2]
    if len(support)<5 or len(support)/len(angles)<.7 or abs(center)>8:
        return 0,{'deskew_status':'MIXED_OR_UNSUPPORTED_BASELINES','baseline_count':len(angles),'support_count':len(support)}
    angle=median(support)
    return angle if abs(angle)>=.25 else 0,{'deskew_status':'MEASURED_GLOBAL_BASELINES','baseline_count':len(angles),'support_count':len(support),'residual_clockwise_degrees':angle}


def quality(spans):
    """Structural routing criteria only; never extraction confidence or PASS."""
    # Orthogonal ownership alone can look valid when an above/below label is
    # rotated into a left/right label. Measured long text axes must also be
    # horizontal in the chosen layout; this distinguishes 0/180 from 90/270.
    axes=[s['layout_axis_pixels'] for s in spans if len(s['text'])>=5 and 'layout_axis_pixels' in s and max(s['layout_axis_pixels'])>=2*min(s['layout_axis_pixels'])]
    if axes and sum(w>=h*2 for w,h in axes)<len(axes)*.7:return (0,0)
    headers,rows,_=printed_layout({'spans':spans})
    by={}
    for name,raw,_ in headers:by.setdefault(name,set()).add(raw)
    numeric=lambda raw:isinstance(raw,str) and bool(re.fullmatch(r'\s*(?:[A-Z]{3}\s*|[₹$€£¥]\s*)?-?[\d][\d.,]*(?:\s*[A-Z]{3}|\s*[₹$€£¥])?\s*',raw))
    count=0
    for name,values in by.items():
        if len(values)!=1:continue
        raw=next(iter(values))
        if name.endswith('_amount') and not numeric(raw):continue
        if name in ('invoice_date','expense_date','due_date') and not re.fullmatch(r'\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2} [A-Za-z]+ \d{4}',raw):continue
        count+=1
    cells=0
    for row in rows:
        fields={name:raw for name,raw,_ in row}
        if not fields.get('description') or not numeric(fields.get('amount') or fields.get('net_amount') or fields.get('gross_amount')):continue
        cells+=2+sum(numeric(fields.get(name)) for name in ('quantity','unit_price'))
    return count,cells


def align_layout(spans,width,height):
    base=affine(width,height,0)
    if not spans or any('polygon_layout_pixels' not in s for s in spans):
        return spans,base,{'version':VERSION,'status':'MEASURED_POLYGONS_UNAVAILABLE','image_bytes_transformed':False}
    angle,diagnostic=residual_angle(spans);candidates=[]
    for cardinal in (0,90,180,270):
        transform=affine(width,height,cardinal-angle)
        actual=aligned_spans(spans,transform);score=quality(actual)
        candidates.append((score,cardinal,actual,transform))
    candidates.sort(key=lambda c:c[0],reverse=True);best=candidates[0]
    sufficient=best[0][0]>=4 or best[0][0]>=2 and best[0][1]>=4
    if not sufficient or best[0]==candidates[1][0]:
        return spans,base,{'version':VERSION,'status':'ORIENTATION_UNRESOLVED','candidate_coverage':[{'clockwise_degrees':c[1],'printed_headers':c[0][0],'readable_core_cells':c[0][1]} for c in candidates],
            'image_bytes_transformed':False,**diagnostic}
    return best[2],best[3],{'version':VERSION,'status':'ALIGNED','clockwise_degrees':best[1],
        'layout_only_deskew_degrees':-angle,'transform':best[3],'printed_headers':best[0][0],
        'readable_core_cells':best[0][1],'image_bytes_transformed':False,**diagnostic}


def read_disagreements(first,second):
    """Retain contradictory text in corresponding measured source regions."""
    out=[]
    for a in first:
        for b in second:
            x=a['bbox'];y=b['bbox']
            overlap=max(0,min(x['x2'],y['x2'])-max(x['x1'],y['x1']))*max(0,min(x['y2'],y['y2'])-max(x['y1'],y['y1']))
            small=min((x['x2']-x['x1'])*(x['y2']-x['y1']),(y['x2']-y['x1'])*(y['y2']-y['y1']))
            # Different segmentation is not a conflicting read of the same cell.
            similar=min(x['x2']-x['x1'],y['x2']-y['x1'])>=max(x['x2']-x['x1'],y['x2']-y['x1'])*.7
            if similar and small>0 and overlap/small>=.75 and ' '.join(a['text'].split())!=' '.join(b['text'].split()):
                out.append({'bbox':y,'first_raw':a['text'],'second_raw':b['text']})
    return out
