"""Conservative actual-text parser for explicit labels and pipe-delimited tables.

Unrecognized layouts retain missing/ambiguous observations for human review.
No golden answers, finance decisions or execution of document instructions.
"""
from dataclasses import replace
from uuid import uuid4
import re
from app.domain.extraction import AdapterMetadata, AdapterCapabilities, ExtractionResult, FieldObservation, LineItemObservation, SCHEMA_VERSION
from app.domain.extraction import ExtractionObservationState as State, ExtractionStatus
from app.domain.evidence import EvidenceReference, EvidenceKind, BoundingBox

LABELS={'supplier':'vendor_name','vendor':'vendor_name','merchant':'merchant_name',
    'invoice number':'invoice_number','invoice no':'invoice_number','receipt number':'receipt_number',
    'invoice date':'invoice_date','expense date':'expense_date','date':'invoice_date','due date':'due_date',
    'po reference':'po_reference','purchase order':'po_reference','currency':'currency','subtotal':'subtotal_amount',
    'discount':'document_discount_amount','tax':'tax_amount','shipping':'shipping_amount',
    'other charges':'other_charges_amount','total':'total_amount','grand total':'total_amount',
    'payment terms':'payment_terms','payment account token':'payment_account_token','tax basis':'tax_basis',
    'category':'category','local timezone':'local_timezone','receipt type':'receipt_type'}
HEADER_FIELDS=tuple(dict.fromkeys(LABELS.values()))
ROW_FIELDS=('description','quantity','unit_price','discount_amount','net_amount','tax_rate','tax_amount','gross_amount','uom')
TABLE_HEADERS=('description','quantity','unit price','discount','net','tax rate','tax','gross','uom')


def source(bundle,page,field,bbox=None,raw=None):
    return EvidenceReference(EvidenceKind.DOCUMENT_FIELD,bundle.document_id,bundle.document_version,
        bundle.tenant_id,bundle.legal_entity_id,field_path=field,document_id=bundle.document_id,page=page,
        bbox=BoundingBox(**bbox) if bbox else None,observed_value=raw)


def result(bundle,metadata,headers,rows=(),failure=None):
    status=ExtractionStatus.FAILED if failure else (ExtractionStatus.COMPLETED if all(f.state is State.PRESENT for f in headers) else ExtractionStatus.PARTIAL)
    out=ExtractionResult(uuid4(),bundle.document_id,bundle.document_version,bundle.tenant_id,bundle.legal_entity_id,
        SCHEMA_VERSION,metadata,status,tuple(headers),tuple(rows),failure_code=failure)
    out.validate_binding(bundle,SCHEMA_VERSION);return out


class NativeTextExtractionAdapter:
    metadata=AdapterMetadata('native-label-parser','1','NATIVE_TEXT',prompt_template_version='labeled-header-table-v1')
    capabilities=AdapterCapabilities(True,True,True,False)

    def __init__(self, page_details=()):
        self.details={p['page']:p for p in page_details}
        self.diagnostics=[]

    def extract(self,bundle,schema_version):
        if schema_version != SCHEMA_VERSION: raise ValueError('Unsupported schema')
        seen={k:[] for k in HEADER_FIELDS};rows=[]
        for page in bundle.pages:
            table=False
            spans=self.details.get(page.page,{}).get('spans',[])
            for line in (page.available_text or '').splitlines():
                line=line.strip()
                if not line:continue
                match=re.fullmatch(r'([^:]{1,40}):\s*(.{1,1000})',line)
                if match and match[1].casefold() in LABELS:
                    field=LABELS[match[1].casefold()];raw=match[2].strip()
                    matching=[s for s in spans if s['text'].strip()==line]
                    bbox=matching[0].get('bbox') if len(matching)==1 else None
                    seen[field].append(FieldObservation(field,State.PRESENT,raw,source=source(bundle,page.page,field,bbox,raw),
                        diagnostic_note='Native text span includes printed label and value.' if bbox else 'Page-level text evidence; exact box unavailable.'))
                    table=False;continue
                values=[v.strip() for v in line.split('|')]
                if tuple(v.casefold() for v in values)==TABLE_HEADERS:
                    table=True;continue  # repeated table headers never become rows
                if table and len(values)==len(ROW_FIELDS) and all(values):
                    if len(rows)>=200:
                        self.diagnostics.append('TABLE_ROW_LIMIT');break
                    row_no=len(rows)+1
                    rows.append(LineItemObservation(row_no,tuple(FieldObservation(k,State.PRESENT,v,
                        source=source(bundle,page.page,k,None,v),diagnostic_note='Row-level page evidence; no cell box inferred.') for k,v in zip(ROW_FIELDS,values))))
                elif table and '|' in line:
                    self.diagnostics.append('TABLE_COVERAGE_UNCERTAIN');table=False
                elif table and line.startswith('SYNTHETIC - Page'): table=False
        headers=[]
        for field,candidates in seen.items():
            distinct=list(dict.fromkeys(f.raw_value for f in candidates))
            if not candidates: headers.append(FieldObservation(field,State.MISSING))
            elif len(distinct)==1: headers.append(candidates[0])
            else:
                headers.append(FieldObservation(field,State.AMBIGUOUS,' | '.join(distinct),source=candidates[0].source,
                    diagnostic_note='Conflicting repeated labels across document pages; no value chosen.'))
                if field in ('invoice_number','receipt_number'):self.diagnostics.append('SEGMENTATION_UNCERTAIN')
        return result(bundle,self.metadata,headers,rows)


def reconcile(primary,other):
    """Critical disagreement never resolves according to finance arithmetic."""
    if any(getattr(primary,k)!=getattr(other,k) for k in ('document_id','document_version','tenant_id','legal_entity_id','schema_version')):
        raise ValueError('Provider binding disagreement')
    by={f.field_path:f for f in other.header_fields}
    headers=[]
    for a in primary.header_fields:
        b=by.get(a.field_path)
        if b is None:headers.append(a);continue
        if a.state is State.PRESENT and b.state is State.PRESENT and a.raw_value!=b.raw_value:
            headers.append(FieldObservation(a.field_path,State.AMBIGUOUS,f'{a.raw_value} | {b.raw_value}',source=a.source,
                diagnostic_note='Provider disagreement; both candidates retained.'))
        elif a.state is not State.PRESENT and b.state is State.PRESENT and a.state is State.MISSING:headers.append(b)
        elif a.state is State.PRESENT and b.state in (State.AMBIGUOUS,State.ILLEGIBLE):
            headers.append(FieldObservation(a.field_path,State.AMBIGUOUS,f'{a.raw_value} | {b.raw_value or b.state.value}',source=a.source,
                diagnostic_note='Independent provider cannot corroborate critical observation.'))
        else:headers.append(a)
    rows=primary.line_items
    if primary.line_items and other.line_items and [tuple(f.raw_value for f in r.fields) for r in rows]!=[tuple(f.raw_value for f in r.fields) for r in other.line_items]:
        rows=tuple(replace(r,fields=tuple(FieldObservation(f.field_path,State.AMBIGUOUS,f.raw_value or 'unresolved',source=f.source,
            diagnostic_note='Provider table disagreement.') for f in r.fields)) for r in rows)
    elif not rows:rows=other.line_items
    return replace(primary,header_fields=tuple(headers),line_items=rows,status=ExtractionStatus.PARTIAL)
