"""Versioned document-source extension over unchanged Phase-1 calculations.

The approved Phase-2 source path needs physical evidence and HUMAN_VERIFIED
facts. Existing core ruleset, rule identities, arithmetic and structured behavior
are preserved. Only DOC-001 reconciliation on document-derived contexts uses this
extension; it cannot override any other mandatory result.
"""
from dataclasses import replace
from decimal import Decimal
import json
from uuid import UUID
from app.domain.evidence import EvidenceReference, EvidenceKind, BoundingBox
from app.rules.engine import evaluate, combine

DOCUMENT_RULE_VERSION='document-source-v1'


def evaluate_sources(context):
    baseline=evaluate(context);c=json.loads(context.encoded)
    if not any(l['role'] in ('INVOICE','RECEIPT') for l in c.get('document_sources',[])):return baseline
    p=c['transaction'];refs=c['references'];vendor=p['branch']=='VENDOR_INVOICE'
    documents=[r for r in refs.values() if r.get('verification')=='HUMAN_VERIFIED_DOCUMENT']
    known={r['_document_id']:r for r in documents}
    valid=c.get('document_source_validation') is True
    if vendor:
        doc=known.get(str(p.get('source_document_id')));master=refs.get(str(p.get('vendor_id')))
        facts=doc['facts'] if doc else {}
        valid=bool(valid and doc and master and facts.get('vendor_name')==master.get('legal_name') and
            all(facts.get(k)==p.get(k) for k in ('invoice_number','invoice_date','currency')) and
            facts.get('total_amount') is not None and p.get('total_amount') is not None and
            Decimal(facts['total_amount'])==Decimal(p['total_amount']))
    else:
        for item in p['items']:
            doc=known.get(str(item.get('source_document_id')));facts=doc['facts'] if doc else {}
            valid=bool(valid and doc and facts.get('readable') is True and facts.get('receipt_type')=='ITEMIZED' and
                all(facts.get(k)==item.get(k)==p.get(k) for k in ('currency','category','expense_date','local_timezone')) and
                facts.get('receipt_total_amount') is not None and item.get('receipt_total_amount') is not None and
                Decimal(facts['receipt_total_amount'])==Decimal(item['receipt_total_amount']))
        valid=bool(valid and p['items'] and not c.get('receipt_conflicts'))
    def physical(reference):
        record=next((r for r in documents if r['id']==str(reference.record_id)),None)
        if record is None or reference.kind is not EvidenceKind.DOCUMENT_FIELD:return reference
        field=reference.field_path
        locator=record.get('_field_sources',{}).get(field)
        # Aggregate facts have page-level provenance only; never borrow another field's box.
        if locator is None:locator={'page':record['source_verification']['first_page'],'bbox':None}
        did=UUID(record['_document_id'])
        return EvidenceReference(EvidenceKind.DOCUMENT_FIELD,did,record['_document_version'],reference.tenant_id,
            reference.legal_entity_id,field_path=field,document_id=did,page=locator.get('page'),
            bbox=BoundingBox(**locator['bbox']) if locator.get('bbox') else None,snapshot_id=reference.snapshot_id,
            observed_value=locator.get('observed_value'))
    results=[]
    for rule in baseline.results:
        rule=replace(rule,evidence=tuple(physical(e) for e in rule.evidence))
        if rule.rule_id=='DOC-001':
            field_evidence=[]
            for record in documents:
                for field in ('vendor_name','invoice_number','invoice_date','currency','total_amount','expense_date','receipt_number'):
                    locator=record.get('_field_sources',{}).get('facts.'+field)
                    if locator:
                        field_evidence.append(physical(EvidenceReference(EvidenceKind.DOCUMENT_FIELD,UUID(record['id']),record['version'],
                            UUID(c['tenant_id']),UUID(c['legal_entity_id']),field_path='facts.'+field,snapshot_id=UUID(c['snapshot_id']))))
            rule=replace(rule,version=DOCUMENT_RULE_VERSION,status='PASS' if valid else 'UNKNOWN',
                decision_effect='NONE' if valid else 'REVIEW',reason='Canonical facts reconcile with human-verified physical source revisions.' if valid else 'Physical source facts or current attachment verification remain unresolved.',
                observed={'document_ids':list(known),'source_validation':valid},expected='Verified consistent physical source facts',
                evidence=rule.evidence+tuple(field_evidence))
        results.append(rule)
    return combine(results)
