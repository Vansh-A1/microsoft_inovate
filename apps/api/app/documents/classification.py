"""Conservative document-purpose suggestion; never a finance decision."""
from app.extraction.native import NativeTextExtractionAdapter
from app.domain.extraction import SCHEMA_VERSION

VERSION='document-purpose-v1'

def classify(bundle,details):
    adapter=NativeTextExtractionAdapter(details)
    observed=adapter.extract(bundle,SCHEMA_VERSION)
    by={f.field_path:f for f in observed.header_fields}
    present=lambda name:name in by and by[name].state.value=='PRESENT'
    invoice=present('invoice_number') and present('invoice_date')
    receipt=present('merchant_name') and present('expense_date')
    kind='VENDOR_INVOICE' if invoice and not receipt else 'EMPLOYEE_RECEIPT' if receipt and not invoice else None
    if 'SEGMENTATION_UNCERTAIN' in adapter.diagnostics:kind=None
    return {'version':VERSION,'state':'SUGGESTED' if kind else 'NEEDS_CONFIRMATION','source_type':kind,
        'evidence_pages':sorted({f.page for f in observed.header_fields if f.source and f.state.value=='PRESENT'}),
        'method':'PRINTED_LABELS','manual_source_verification_required':True}
