"""Source identity and conservative model-row association, never value dedup."""
from dataclasses import replace
import hashlib
import json
from app.domain.extraction import ExtractionObservationState as State

PREFIX='ROW_ASSOCIATION_UNCONFIRMED:'


def source_rows(result):
    out=[]
    for row in result.line_items:
        sources=[f.source for f in row.fields if f.source and f.bbox]
        pages={s.page for s in sources}
        if not sources or len(pages)!=1:continue
        box={axis:(min if axis.endswith('1') else max)(getattr(s.bbox,axis) for s in sources) for axis in ('x1','y1','x2','y2')}
        identity=[str(result.document_id),result.document_version,str(result.tenant_id),str(result.legal_entity_id),next(iter(pages)),box]
        out.append({'row':row.row_index,'page':next(iter(pages)),'row_extent':box,
            'identity':hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest(),
            'method':'MEASURED_ROW_REGIONS','unread_fields':[f.field_path for f in row.fields if f.state is State.MISSING and
                (f.diagnostic_note or '').startswith('SOURCE_CELL_UNREAD:')]})
    return out


def region_identity(bundle,page,trace):
    """Equal crop bytes alone are not identity: equal printed rows can be real."""
    if trace.get('version')!='ruled-table-crops-v1':return None
    extent=trace.get('row_extent_pixels');dimensions=trace.get('preview_dimensions')
    if not isinstance(extent,list) or len(extent)!=4 or not isinstance(dimensions,list) or len(dimensions)!=2:return None
    if any(type(v) is not int for v in extent+dimensions):return None
    x1,y1,x2,y2=extent;width,height=dimensions
    if not 0<=x1<x2<=width or not 0<=y1<y2<=height:return None
    identity=[str(bundle.document_id),bundle.document_version,str(bundle.tenant_id),str(bundle.legal_entity_id),page.page,page.artifact_ref,extent]
    return hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()


def fingerprint(row):
    present={f.field_path:f.raw_value for f in row.fields if f.state is State.PRESENT}
    if 'description' not in present or len(set(present)&{'quantity','unit_price','amount','net_amount','gross_amount'})<2:return None
    return tuple(sorted(present.items()))


def quarantine(row,reason):
    return replace(row,fields=tuple(replace(f,state=State.AMBIGUOUS if f.state is State.PRESENT else f.state,
        diagnostic_note=PREFIX+' '+reason) for f in row.fields))
