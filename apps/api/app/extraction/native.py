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
    metadata=AdapterMetadata('native-label-parser','6','NATIVE_TEXT',prompt_template_version='labeled-header-table-layout-v6')
    capabilities=AdapterCapabilities(True,True,True,False)

    def __init__(self, page_details=()):
        self.details={p['page']:p for p in page_details}
        self.diagnostics=[]

    def extract(self,bundle,schema_version):
        if schema_version != SCHEMA_VERSION: raise ValueError('Unsupported schema')
        seen={k:[] for k in HEADER_FIELDS};rows=[]
        for page in bundle.pages:
            from app.extraction.layout import printed_layout
            candidates,layout_rows,notes=printed_layout(self.details.get(page.page,{}))
            layout_fields={field for field,raw,bbox in candidates}
            table=False
            spans=self.details.get(page.page,{}).get('spans',[])
            for line in (page.available_text or '').splitlines():
                line=line.strip()
                if not line:continue
                match=re.fullmatch(r'([^:]{1,40}):\s*(.{1,1000})',line)
                if match and match[1].casefold() in LABELS:
                    field=LABELS[match[1].casefold()];raw=match[2].strip()
                    # PyMuPDF sorted text may flatten independent columns into
                    # one line. Measured label regions own that page's mapping.
                    if field in layout_fields:table=False;continue
                    from app.extraction.layout import key,HEADER_ALIASES
                    if key(raw) in HEADER_ALIASES:
                        self.diagnostics.append('HEADER_ASSOCIATION_UNCERTAIN');table=False;continue
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
            self.diagnostics.extend(notes)
            for field,raw,bbox in candidates:
                if field not in seen:continue
                seen[field].append(FieldObservation(field,State.PRESENT,raw,source=source(bundle,page.page,field,bbox,raw),
                    diagnostic_note='Printed label/value association from measured text regions; not yet human confirmed.'))
            for cells in layout_rows:
                if len(rows)>=200:self.diagnostics.append('TABLE_ROW_LIMIT');break
                rows.append(LineItemObservation(len(rows)+1,tuple(FieldObservation(field,State.PRESENT if raw is not None else State.MISSING,raw,
                    source=source(bundle,page.page,field,bbox,raw),
                    diagnostic_note='Printed column association from measured cell text regions.' if raw is not None else
                        f'SOURCE_CELL_UNREAD: no value independently read for {field} on page {page.page}; absent versus illegible requires source review. No field box is asserted.')
                    for field,raw,bbox in cells)))
        headers=[]
        for field,candidates in seen.items():
            distinct=list(dict.fromkeys(f.raw_value for f in candidates))
            if not candidates: headers.append(FieldObservation(field,State.MISSING))
            elif len(distinct)==1: headers.append(candidates[0])
            else:
                headers.append(FieldObservation(field,State.AMBIGUOUS,' | '.join(distinct),source=candidates[0].source,
                    diagnostic_note='Conflicting repeated labels across document pages; no value chosen.'))
                if field in ('invoice_number','receipt_number'):self.diagnostics.append('SEGMENTATION_UNCERTAIN')
        # A missing column must remain a reviewable observation, not disappear
        # and let a demo/business template appear to supply the source fact.
        rows=[replace(row,fields=row.fields+tuple(FieldObservation(field,State.MISSING,
            diagnostic_note='No independently read item column established this fact; source review is required.')
            for field in ROW_FIELDS if field not in {f.field_path for f in row.fields})) for row in rows]
        return result(bundle,self.metadata,headers,rows)


def reconcile(primary,other):
    """Critical disagreement never resolves according to finance arithmetic."""
    if any(getattr(primary,k)!=getattr(other,k) for k in ('document_id','document_version','tenant_id','legal_entity_id','schema_version')):
        raise ValueError('Provider binding disagreement')
    by={f.field_path:f for f in other.header_fields}
    currency=None
    a_currency=next((f for f in primary.header_fields if f.field_path=='currency' and f.state is State.PRESENT),None)
    b_currency=by.get('currency')
    if a_currency and b_currency and b_currency.state is State.PRESENT:
        from app.documents.normalizer import normalize_currency,NormalizationError
        try:
            a_unit=normalize_currency(a_currency.raw_value);b_unit=normalize_currency(b_currency.raw_value)
            if a_unit==b_unit:currency=a_unit
        except NormalizationError:pass
    def same_literal(a,b):
        if a.raw_value==b.raw_value:return True
        name=a.field_path.split('.')[-1]
        if name in ('quantity','tax_rate') or (currency and (name.endswith('_amount') or name in ('unit_price','amount'))):
            from app.documents.normalizer import normalize_money,normalized_value,NormalizationError
            from decimal import Decimal
            try:
                if name in ('quantity','tax_rate'):
                    return Decimal(normalized_value(name,a.raw_value)[0])==Decimal(normalized_value(name,b.raw_value)[0])
                return Decimal(normalize_money(a.raw_value,currency))==Decimal(normalize_money(b.raw_value,currency))
            except NormalizationError:return False
        return False
    headers=[]
    for a in primary.header_fields:
        b=by.get(a.field_path)
        if b is None:headers.append(a);continue
        if a.state is State.PRESENT and b.state is State.PRESENT and not same_literal(a,b):
            headers.append(FieldObservation(a.field_path,State.AMBIGUOUS,f'{a.raw_value} | {b.raw_value}',source=a.source,
                diagnostic_note='Provider disagreement; both candidates retained.'))
        elif a.state is State.MISSING:headers.append(b)
        elif a.state is State.PRESENT and b.state in (State.AMBIGUOUS,State.ILLEGIBLE):
            headers.append(FieldObservation(a.field_path,State.AMBIGUOUS,f'{a.raw_value} | {b.raw_value or b.state.value}',source=a.source,
                diagnostic_note='Independent provider cannot corroborate critical observation.'))
        elif a.state is State.PRESENT and b.state is State.PRESENT and a.raw_value!=b.raw_value:
            headers.append(replace(a,diagnostic_note=f'Equivalent Decimal amount with agreed explicit currency; alternate provider literal: {b.raw_value}'))
        else:headers.append(a)
    primary_names={f.field_path for f in primary.header_fields}
    headers.extend(f for f in other.header_fields if f.field_path not in primary_names)
    rows=primary.line_items
    if primary.line_items and other.line_items:
        if len(primary.line_items)!=len(other.line_items):
            # Keep the larger candidate set visible, without asserting that its
            # coverage is correct. The worker retains both provider outputs.
            rows=primary.line_items if len(primary.line_items)>=len(other.line_items) else other.line_items
            rows=tuple(replace(r,fields=tuple(replace(f,state=State.AMBIGUOUS if f.raw_value is not None else f.state,
                diagnostic_note='ROW_ASSOCIATION_UNCONFIRMED: provider row-count disagreement; inspect source rows before using candidates.')
                for f in r.fields)) for r in rows)
        else:
            combined=[]
            for a_row,b_row in zip(primary.line_items,other.line_items):
                other_fields={f.field_path:f for f in b_row.fields};fields=[]
                for a in a_row.fields:
                    b=other_fields.get(a.field_path)
                    if b is not None and ((a.state is State.PRESENT and b.state is State.PRESENT and not same_literal(a,b)) or
                        (a.state is State.PRESENT and b.state in (State.AMBIGUOUS,State.ILLEGIBLE))):
                        fields.append(FieldObservation(a.field_path,State.AMBIGUOUS,a.raw_value or 'unresolved',source=a.source,diagnostic_note='Provider table field disagreement.'))
                    elif a.state is State.MISSING and b is not None:fields.append(b)
                    else:fields.append(a)
                names={f.field_path for f in fields};fields.extend(f for f in b_row.fields if f.field_path not in names)
                combined.append(replace(a_row,fields=tuple(fields)))
            rows=tuple(combined)
    elif not rows:rows=other.line_items
    return replace(primary,header_fields=tuple(headers),line_items=rows,status=ExtractionStatus.PARTIAL)
