"""Scope-filtered, version-pinned synthetic reference catalog."""
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
from uuid import UUID, uuid4
from sqlalchemy import insert, select
from app.core.config import ROOT
from app.core.serialization import digest
from app.db.models import Tenant, LegalEntity, ReferenceRecord, ReferenceLink, ReferenceSnapshot, SnapshotMember
from app.db.session import scope_query


def number_key(value):
    import unicodedata
    return unicodedata.normalize('NFKC', value).strip().casefold() if value else None


def seed_references(session, identity, *, source_root=None):
    # Server-side development seed only; no API accepts a source path. The
    # hackathon pack remaps fixture identities into a separate synthetic scope.
    root = source_root or ROOT / 'data/synthetic/reference'
    if not session.get(Tenant, identity.tenant_id):
        source = next(r for r in json.loads((root/'tenants.json').read_text())['records'] if r['id']==str(identity.tenant_id))
        session.add(Tenant(id=identity.tenant_id, name=source.get('name', 'Synthetic tenant')))
        session.flush()
    if not session.get(LegalEntity, identity.legal_entity_id):
        r = next(r for r in json.loads((root/'legal_entities.json').read_text())['records'] if r['id']==str(identity.legal_entity_id))
        session.add(LegalEntity(id=identity.legal_entity_id, tenant_id=identity.tenant_id, name=r.get('name','Synthetic entity'), currency=r.get('currency','INR'), timezone=r.get('timezone','Asia/Kolkata')))
        session.flush()
    def add(r, kind, parent=None):
        rid, version = UUID(r['id']), r['version']
        if session.get(ReferenceRecord, (rid, version)):
            return
        raw_amount=r.get('total_amount', r.get('requested_amount', r.get('amount')))
        raw_date=r.get('invoice_date', r.get('expense_date'))
        row=ReferenceRecord(**identity.scope(), id=rid, version=version, kind=kind, label=r.get('name',r.get('legal_name',r.get('code',r.get('policy_code',r.get('display_number',r.get('invoice_number',r['id'])))))), payload=r,
            amount=Decimal(raw_amount) if raw_amount is not None else None, currency=r.get('currency'), business_date=date.fromisoformat(raw_date) if raw_date else None,
            party_id=UUID(r['vendor_id'] if 'vendor_id' in r else r['employee_id']) if 'vendor_id' in r or 'employee_id' in r else None,
            number_key=number_key(r.get('invoice_number',r.get('claim_number'))), effective_from=date.fromisoformat(r['effective_from']) if r.get('effective_from') else None, effective_to=date.fromisoformat(r['effective_to']) if r.get('effective_to') else None)
        session.add(row);session.flush()
        if parent:
            session.add(ReferenceLink(**identity.scope(), child_id=rid, child_version=version, parent_id=UUID(parent['id']),parent_version=parent['version'],relationship=kind));session.flush()
        nested={'purchase_orders':('lines','po_lines'), 'goods_receipts':('lines','grn_lines'), 'budgets':('ledger','budget_ledger'), 'historical_transactions':('allocations','matching_allocations')}
        if kind in nested:
            key,child_kind=nested[kind]
            for child in r.get(key,[]):add(child,child_kind,r)
    for file in sorted(root.glob('*.json')):
        if file.stem in ('tenants','legal_entities'):continue
        for r in json.loads(file.read_text())['records']:
            if r['tenant_id']==str(identity.tenant_id) and r['legal_entity_id']==str(identity.legal_entity_id):add(r,file.stem)
    return snapshot(session,identity)


def snapshot(session,identity,business_day=None):
    from app.services.reference_imports import active_records
    rows=active_records(session,identity,business_day).values()
    return snapshot_records(session,identity,[(r.id,r.version) for r in rows])


def snapshot_records(session,identity,records):
    records=sorted(set(records),key=lambda r:(str(r[0]),r[1]))
    manifest=[{'id':str(rid),'version':version} for rid,version in records]
    hashed=digest(manifest)
    existing=session.scalar(scope_query(select(ReferenceSnapshot),ReferenceSnapshot,identity).where(ReferenceSnapshot.content_digest==hashed))
    if existing:return existing
    row=ReferenceSnapshot(**identity.scope(),id=uuid4(),content_digest=hashed,manifest={'records':manifest})
    session.add(row);session.flush()
    # Exact immutable membership is unchanged. Bounded inserts avoid constructing
    # and tracking one ORM object per member while retaining database constraints.
    for offset in range(0,len(records),500):
        session.execute(insert(SnapshotMember),[dict(**identity.scope(),snapshot_id=row.id,record_id=rid,record_version=version)
            for rid,version in records[offset:offset+500]])
    session.flush();return row


def pinned(session,identity,snapshot_id):
    query=select(ReferenceRecord).join(SnapshotMember, (SnapshotMember.record_id==ReferenceRecord.id)&(SnapshotMember.record_version==ReferenceRecord.version)&(SnapshotMember.tenant_id==ReferenceRecord.tenant_id)&(SnapshotMember.legal_entity_id==ReferenceRecord.legal_entity_id)).where(SnapshotMember.snapshot_id==snapshot_id,ReferenceRecord.kind.not_in(['historical_transactions','matching_allocations']))
    return {str(r.id):r.payload|{'_kind':r.kind} for r in session.scalars(scope_query(query,ReferenceRecord,identity))}
