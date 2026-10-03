"""Phase-3 append-only control facts and current reference activation projections."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Numeric, String, UniqueConstraint, Uuid, event, ForeignKeyConstraint, func, inspect
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models import Base, Scoped, Identified, J, scoped, fk, forbid_mutation


def txfk():
    return ForeignKeyConstraint(['tenant_id','legal_entity_id','transaction_id','transaction_version'],['transaction_versions.tenant_id','transaction_versions.legal_entity_id','transaction_versions.transaction_id','transaction_versions.version'])

class ReferenceBatch(Scoped, Identified, Base):
    __tablename__='reference_batches'
    source_system:Mapped[str]=mapped_column(String(100))
    source_version:Mapped[str]=mapped_column(String(100))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    state:Mapped[str]=mapped_column(String(20),default='STAGED')
    records:Mapped[list]=mapped_column(J)
    validation:Mapped[list]=mapped_column(J,default=list)
    __table_args__=scoped(CheckConstraint("state IN ('STAGED','VALID','INVALID','ACTIVE','SUPERSEDED')"))

class ReferenceActivation(Scoped, Identified, Base):
    __tablename__='reference_activations'
    batch_id:Mapped[UUID]=mapped_column(Uuid)
    record_id:Mapped[UUID]=mapped_column(Uuid)
    record_version:Mapped[int]=mapped_column(Integer)
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    __table_args__=scoped(fk('reference_batches','batch_id'),fk('reference_records','record_id',version='record_version'),UniqueConstraint('tenant_id','legal_entity_id','record_id','record_version'))

class FinanceAllocation(Scoped, Identified, Base):
    __tablename__='finance_allocations'
    transaction_id:Mapped[UUID]=mapped_column(Uuid)
    transaction_version:Mapped[int]=mapped_column(Integer)
    evaluation_id:Mapped[UUID]=mapped_column(Uuid)
    kind:Mapped[str]=mapped_column(String(24))
    resource_id:Mapped[UUID]=mapped_column(Uuid)
    reference_id:Mapped[UUID|None]=mapped_column(Uuid)
    reference_version:Mapped[int|None]=mapped_column(Integer)
    amount:Mapped[Decimal]=mapped_column(Numeric(20,6))
    quantity:Mapped[Decimal]=mapped_column(Numeric(24,8))
    currency:Mapped[str]=mapped_column(String(3))
    metadata_json:Mapped[dict]=mapped_column(J)
    operation_key:Mapped[str]=mapped_column(String(64))
    __table_args__=scoped(txfk(),fk('evaluations','evaluation_id'),fk('reference_records','reference_id',version='reference_version'),CheckConstraint("kind IN ('BUDGET','PO_LINE','GRN_LINE','CONTRACT','SERVICE','RECEIPT')"),CheckConstraint('amount>=0 AND quantity>=0'),UniqueConstraint('tenant_id','legal_entity_id','operation_key'),Index('ix_finance_resource','tenant_id','legal_entity_id','kind','resource_id'))

class AllocationEvent(Scoped, Identified, Base):
    __tablename__='allocation_events'
    allocation_id:Mapped[UUID]=mapped_column(Uuid)
    action:Mapped[str]=mapped_column(String(20))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    reason:Mapped[str]=mapped_column(String(500))
    __table_args__=scoped(fk('finance_allocations','allocation_id'),CheckConstraint("action IN ('RESERVED','CONSUMED','RELEASED','REVERSED')"),UniqueConstraint('tenant_id','legal_entity_id','allocation_id','action'))

class BudgetEvent(Scoped, Identified, Base):
    __tablename__='budget_events'
    budget_id:Mapped[UUID]=mapped_column(Uuid)
    budget_version:Mapped[int]=mapped_column(Integer)
    allocation_id:Mapped[UUID|None]=mapped_column(Uuid)
    owner_id:Mapped[UUID|None]=mapped_column(Uuid)
    entry_type:Mapped[str]=mapped_column(String(24))
    amount:Mapped[Decimal]=mapped_column(Numeric(20,6))
    currency:Mapped[str]=mapped_column(String(3))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    reason:Mapped[str]=mapped_column(String(500))
    operation_key:Mapped[str]=mapped_column(String(64))
    metadata_json:Mapped[dict]=mapped_column(J)
    __table_args__=scoped(fk('reference_records','budget_id',version='budget_version'),fk('finance_allocations','allocation_id'),CheckConstraint("entry_type IN ('ALLOCATION','ADJUSTMENT','COMMITMENT','RESERVATION','CONSUMPTION','RELEASE','REVERSAL','COMMITMENT_TRANSFER')"),CheckConstraint('amount>=0'),UniqueConstraint('tenant_id','legal_entity_id','operation_key'),Index('ix_budget_ledger_scope','tenant_id','legal_entity_id','budget_id','created_at'))

class DuplicateComparison(Scoped, Identified, Base):
    __tablename__='duplicate_comparisons'
    transaction_id:Mapped[UUID]=mapped_column(Uuid)
    transaction_version:Mapped[int]=mapped_column(Integer)
    candidate_id:Mapped[UUID]=mapped_column(Uuid)
    candidate_version:Mapped[int]=mapped_column(Integer)
    candidate_type:Mapped[str]=mapped_column(String(20))
    classification:Mapped[str]=mapped_column(String(32))
    signals:Mapped[dict]=mapped_column(J)
    comparison_key:Mapped[str]=mapped_column(String(64))
    __table_args__=scoped(txfk(),CheckConstraint("classification IN ('EXACT_BYTES','STRONG_BUSINESS_MATCH','POSSIBLE_DUPLICATE','SHARED_RECEIPT_ALLOCATION','DISTINCT','UNRESOLVED')"),UniqueConstraint('tenant_id','legal_entity_id','comparison_key'),Index('ix_comparison_tx','tenant_id','legal_entity_id','transaction_id','transaction_version'))

class DuplicateResolution(Scoped, Identified, Base):
    __tablename__='duplicate_resolutions'
    comparison_id:Mapped[UUID]=mapped_column(Uuid)
    disposition:Mapped[str]=mapped_column(String(32))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    reason:Mapped[str]=mapped_column(String(500))
    evidence:Mapped[list]=mapped_column(J)
    __table_args__=scoped(fk('duplicate_comparisons','comparison_id'),CheckConstraint("disposition IN ('DISTINCT','CONFIRMED_DUPLICATE','SHARED_RECEIPT_ALLOCATION')"),UniqueConstraint('tenant_id','legal_entity_id','comparison_id'))

class ImageFingerprint(Scoped, Identified, Base):
    __tablename__='image_fingerprints'
    document_id:Mapped[UUID]=mapped_column(Uuid)
    document_version:Mapped[int]=mapped_column(Integer)
    page:Mapped[int]=mapped_column(Integer)
    hash_bits:Mapped[str]=mapped_column(String(16))
    metadata_json:Mapped[dict]=mapped_column(J)
    __table_args__=scoped(fk('document_versions','document_id',version='document_version'),CheckConstraint('page>0'),UniqueConstraint('tenant_id','legal_entity_id','document_id','document_version','page'),Index('ix_phash_scope','tenant_id','legal_entity_id','hash_bits'))

class FingerprintBand(Scoped, Identified, Base):
    __tablename__='fingerprint_bands'
    fingerprint_id:Mapped[UUID]=mapped_column(Uuid)
    band:Mapped[int]=mapped_column(Integer)
    bits:Mapped[str]=mapped_column(String(3))
    __table_args__=scoped(fk('image_fingerprints','fingerprint_id'),UniqueConstraint('tenant_id','legal_entity_id','fingerprint_id','band'),Index('ix_phash_band','tenant_id','legal_entity_id','band','bits'))

class ReceiptShare(Scoped, Identified, Base):
    __tablename__='receipt_shares'
    transaction_id:Mapped[UUID]=mapped_column(Uuid)
    transaction_version:Mapped[int]=mapped_column(Integer)
    document_id:Mapped[UUID]=mapped_column(Uuid)
    item_id:Mapped[UUID]=mapped_column(Uuid)
    employee_id:Mapped[UUID]=mapped_column(Uuid)
    amount:Mapped[Decimal]=mapped_column(Numeric(20,6))
    quantity:Mapped[Decimal]=mapped_column(Numeric(24,8))
    currency:Mapped[str]=mapped_column(String(3))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    reason:Mapped[str]=mapped_column(String(500))
    evidence:Mapped[list]=mapped_column(J)
    __table_args__=scoped(txfk(),CheckConstraint('amount>0 AND quantity>0'),UniqueConstraint('tenant_id','legal_entity_id','transaction_id','transaction_version','item_id'))

class ApprovalRequest(Scoped, Identified, Base):
    __tablename__='approval_requests'
    transaction_id:Mapped[UUID]=mapped_column(Uuid)
    transaction_version:Mapped[int]=mapped_column(Integer)
    policy_id:Mapped[UUID]=mapped_column(Uuid)
    policy_version:Mapped[int]=mapped_column(Integer)
    requirements:Mapped[list]=mapped_column(J)
    payload_digest:Mapped[str]=mapped_column(String(64))
    requirements_digest:Mapped[str]=mapped_column(String(64))
    __table_args__=scoped(txfk(),fk('reference_records','policy_id',version='policy_version'),UniqueConstraint('tenant_id','legal_entity_id','transaction_id','transaction_version','policy_id','policy_version','requirements_digest'))

class ApprovalAction(Scoped, Identified, Base):
    __tablename__='approval_actions'
    request_id:Mapped[UUID]=mapped_column(Uuid)
    sequence:Mapped[int]=mapped_column(Integer)
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    authority_id:Mapped[UUID|None]=mapped_column(Uuid)
    authority_version:Mapped[int|None]=mapped_column(Integer)
    delegation_id:Mapped[UUID|None]=mapped_column(Uuid)
    delegation_version:Mapped[int|None]=mapped_column(Integer)
    state:Mapped[str]=mapped_column(String(16))
    reason:Mapped[str]=mapped_column(String(500))
    __table_args__=scoped(fk('approval_requests','request_id'),fk('reference_records','authority_id',version='authority_version'),fk('reference_records','delegation_id',version='delegation_version'),CheckConstraint("state IN ('APPROVED','DECLINED','REJECTED')"),CheckConstraint('sequence>0'))

class Waiver(Scoped, Identified, Base):
    __tablename__='waivers'
    transaction_id:Mapped[UUID]=mapped_column(Uuid)
    transaction_version:Mapped[int]=mapped_column(Integer)
    rule_id:Mapped[str]=mapped_column(String(32))
    rule_version:Mapped[str]=mapped_column(String(32))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    policy_id:Mapped[UUID]=mapped_column(Uuid)
    policy_version:Mapped[int]=mapped_column(Integer)
    reason:Mapped[str]=mapped_column(String(500))
    evidence:Mapped[list]=mapped_column(J)
    expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    __table_args__=scoped(txfk(),fk('reference_records','policy_id',version='policy_version'),UniqueConstraint('tenant_id','legal_entity_id','transaction_id','transaction_version','rule_id'))

IMMUTABLE_FINANCE=[ReferenceActivation,FinanceAllocation,AllocationEvent,BudgetEvent,DuplicateComparison,DuplicateResolution,ImageFingerprint,FingerprintBand,ReceiptShare,ApprovalRequest,ApprovalAction,Waiver]
for cls in IMMUTABLE_FINANCE:
    event.listen(cls,'before_update',forbid_mutation)
    event.listen(cls,'before_delete',forbid_mutation)


def protect_batch_source(mapper,connection,target):
    if any(inspect(target).attrs[name].history.has_changes() for name in ('id','tenant_id','legal_entity_id','created_at','source_system','source_version','actor_id','records')):
        raise ValueError('Staged reference source facts are immutable.')

event.listen(ReferenceBatch,'before_update',protect_batch_source)
event.listen(ReferenceBatch,'before_delete',forbid_mutation)

# Ordinary scoped B-tree/expression indexes match the bounded retrieval predicates.
from app.db.models import TransactionVersion,ReferenceRecord
from app.db.document_models import DocumentVersion
for model,amount_column,prefix in ((TransactionVersion,'total_amount','transaction'),(ReferenceRecord,'amount','reference')):
    scope=[model.tenant_id,model.legal_entity_id]
    if model is ReferenceRecord:scope.append(model.kind)
    Index('ix_'+prefix+'_near_amount',*scope,model.party_id,model.currency,getattr(model,amount_column),model.business_date)
    Index('ix_'+prefix+'_aggressive_number',*scope,model.party_id,func.regexp_replace(model.number_key,'[^a-zA-Z0-9]','','g'))
for name,fields in (('merchant',('merchant',)),('po',('po_id',)),('contract',('contract_id','service_from')),('source',('source_document_id',))):
    Index('ix_transaction_'+name,*[TransactionVersion.tenant_id,TransactionVersion.legal_entity_id],*[TransactionVersion.payload[f].as_string() for f in fields],TransactionVersion.business_date)
Index('ix_document_original_sha',DocumentVersion.tenant_id,DocumentVersion.legal_entity_id,DocumentVersion.sha256)
