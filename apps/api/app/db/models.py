"""Bounded Phase-1 relational model; immutable facts plus mutable projections."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKeyConstraint,
    Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, Uuid, event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.core.serialization import utcnow

J = JSON().with_variant(JSONB(), 'postgresql')


class Base(DeclarativeBase):
    pass


class Scoped:
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    legal_entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)


class Identified:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


def scoped(*extra):
    return (UniqueConstraint('tenant_id', 'legal_entity_id', 'id'),
        ForeignKeyConstraint(['tenant_id', 'legal_entity_id'], ['legal_entities.tenant_id', 'legal_entities.id']), *extra)


def fk(target, name, *, version=None):
    ours = ['tenant_id', 'legal_entity_id', name]
    theirs = [f'{target}.tenant_id', f'{target}.legal_entity_id', f'{target}.id']
    if version:
        ours.append(version)
        theirs.append(f'{target}.version')
    return ForeignKeyConstraint(ours, theirs)


class Tenant(Base):
    __tablename__ = 'tenants'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    audit_sequence: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    audit_hash: Mapped[str] = mapped_column(String(64), default='0' * 64, nullable=False)


class LegalEntity(Base):
    __tablename__ = 'legal_entities'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid)
    name: Mapped[str] = mapped_column(String(160))
    currency: Mapped[str] = mapped_column(String(3))
    timezone: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint('tenant_id', 'id'), ForeignKeyConstraint(['tenant_id'], ['tenants.id']))


class ReferenceRecord(Scoped, Base):
    __tablename__ = 'reference_records'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(48), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    payload: Mapped[dict] = mapped_column(J, nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    currency: Mapped[str | None] = mapped_column(String(3))
    business_date: Mapped[datetime | None] = mapped_column(Date)
    party_id: Mapped[UUID | None] = mapped_column(Uuid)
    number_key: Mapped[str | None] = mapped_column(String(160))
    effective_from: Mapped[datetime | None] = mapped_column(Date)
    effective_to: Mapped[datetime | None] = mapped_column(Date)
    __table_args__ = (
        UniqueConstraint('tenant_id', 'legal_entity_id', 'id', 'version'),
        ForeignKeyConstraint(['tenant_id', 'legal_entity_id'], ['legal_entities.tenant_id', 'legal_entities.id']),
        CheckConstraint('version > 0'),
        Index('ix_reference_kind_scope', 'tenant_id', 'legal_entity_id', 'kind'),
        Index('ix_history_exact', 'tenant_id', 'legal_entity_id', 'kind', 'party_id', 'number_key', 'currency', 'amount', 'business_date'),
    )


class ReferenceLink(Scoped, Identified, Base):
    __tablename__ = 'reference_links'
    child_id: Mapped[UUID] = mapped_column(Uuid)
    child_version: Mapped[int] = mapped_column(Integer)
    parent_id: Mapped[UUID] = mapped_column(Uuid)
    parent_version: Mapped[int] = mapped_column(Integer)
    relationship: Mapped[str] = mapped_column(String(48))
    __table_args__ = scoped(fk('reference_records', 'child_id', version='child_version'),
        fk('reference_records', 'parent_id', version='parent_version'),
        UniqueConstraint('tenant_id', 'legal_entity_id', 'child_id', 'child_version', 'parent_id', 'parent_version', 'relationship'))


class ReferenceSnapshot(Scoped, Identified, Base):
    __tablename__ = 'reference_snapshots'
    content_digest: Mapped[str] = mapped_column(String(64))
    manifest: Mapped[dict] = mapped_column(J)
    __table_args__ = scoped(UniqueConstraint('tenant_id', 'legal_entity_id', 'content_digest'))


class SnapshotMember(Scoped, Identified, Base):
    __tablename__ = 'snapshot_members'
    snapshot_id: Mapped[UUID] = mapped_column(Uuid)
    record_id: Mapped[UUID] = mapped_column(Uuid)
    record_version: Mapped[int] = mapped_column(Integer)
    __table_args__ = scoped(fk('reference_snapshots', 'snapshot_id'),
        fk('reference_records', 'record_id', version='record_version'),
        UniqueConstraint('tenant_id', 'legal_entity_id', 'snapshot_id', 'record_id', 'record_version'))


class Transaction(Scoped, Identified, Base):
    __tablename__ = 'transactions'
    branch: Mapped[str] = mapped_column(String(32))
    latest_version: Mapped[int] = mapped_column(Integer, default=1)
    row_version: Mapped[int] = mapped_column(Integer, default=1)
    processing_state: Mapped[str] = mapped_column(String(32), default='RECEIVED')
    latest_evaluation_id: Mapped[UUID | None] = mapped_column(Uuid)
    decision: Mapped[str | None] = mapped_column(String(8))
    eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = scoped(CheckConstraint("branch IN ('VENDOR_INVOICE','EMPLOYEE_EXPENSE')"),
        CheckConstraint('latest_version > 0 AND row_version > 0'),
        CheckConstraint("decision IS NULL OR decision IN ('PASS','REVIEW','HOLD')"),
        CheckConstraint("NOT eligible OR (decision IS NOT NULL AND decision = 'PASS' AND processing_state = 'COMPLETED')"),
        Index('ix_transaction_scope_created', 'tenant_id', 'legal_entity_id', 'created_at', 'id'))


class TransactionVersion(Scoped, Identified, Base):
    __tablename__ = 'transaction_versions'
    transaction_id: Mapped[UUID] = mapped_column(Uuid)
    version: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(32), default='canonical-p1-v1')
    normalizer_version: Mapped[str] = mapped_column(String(32), default='structured-p1-v1')
    payload: Mapped[dict] = mapped_column(J)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    currency: Mapped[str | None] = mapped_column(String(3))
    business_date: Mapped[datetime | None] = mapped_column(Date)
    party_id: Mapped[UUID | None] = mapped_column(Uuid)
    number_key: Mapped[str | None] = mapped_column(String(160))
    content_digest: Mapped[str] = mapped_column(String(64))
    author_id: Mapped[UUID] = mapped_column(Uuid)
    change_reason: Mapped[str] = mapped_column(String(500))
    __table_args__ = scoped(fk('transactions', 'transaction_id'),
        UniqueConstraint('tenant_id', 'legal_entity_id', 'transaction_id', 'version'),
        CheckConstraint('version > 0'),
        Index('ix_transaction_exact', 'tenant_id', 'legal_entity_id', 'party_id', 'number_key', 'currency', 'total_amount', 'business_date'))


class ApprovalRecord(Scoped, Identified, Base):
    __tablename__ = 'approval_records'
    transaction_id: Mapped[UUID] = mapped_column(Uuid)
    transaction_version: Mapped[int] = mapped_column(Integer)
    policy_id: Mapped[UUID] = mapped_column(Uuid)
    policy_version: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    role: Mapped[str] = mapped_column(String(32))
    sequence: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(16))
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = scoped(
        ForeignKeyConstraint(['tenant_id','legal_entity_id','transaction_id','transaction_version'],
            ['transaction_versions.tenant_id','transaction_versions.legal_entity_id','transaction_versions.transaction_id','transaction_versions.version']),
        fk('reference_records', 'policy_id', version='policy_version'), CheckConstraint('sequence > 0'))


class Evaluation(Scoped, Identified, Base):
    __tablename__ = 'evaluations'
    transaction_id: Mapped[UUID] = mapped_column(Uuid)
    transaction_version: Mapped[int] = mapped_column(Integer)
    reference_snapshot_id: Mapped[UUID] = mapped_column(Uuid)
    ruleset_version: Mapped[str] = mapped_column(String(32))
    decision_policy_version: Mapped[str] = mapped_column(String(32))
    evaluation_mode: Mapped[str] = mapped_column(String(32), default='RULES_ONLY')
    completeness: Mapped[str] = mapped_column(String(16))
    decision: Mapped[str] = mapped_column(String(8))
    eligible: Mapped[bool] = mapped_column(Boolean)
    input_digest: Mapped[str] = mapped_column(String(64))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    supersedes_id: Mapped[UUID | None] = mapped_column(Uuid)
    __table_args__ = scoped(
        ForeignKeyConstraint(['tenant_id','legal_entity_id','transaction_id','transaction_version'],
            ['transaction_versions.tenant_id','transaction_versions.legal_entity_id','transaction_versions.transaction_id','transaction_versions.version']),
        fk('reference_snapshots','reference_snapshot_id'), fk('evaluations','supersedes_id'),
        CheckConstraint("decision IN ('PASS','REVIEW','HOLD')"),
        CheckConstraint("completeness IN ('COMPLETE','INCOMPLETE')"),
        CheckConstraint("evaluation_mode = 'RULES_ONLY'"),
        CheckConstraint("NOT eligible OR (decision = 'PASS' AND completeness = 'COMPLETE')"))


class EvaluationInput(Scoped, Identified, Base):
    __tablename__ = 'evaluation_inputs'
    evaluation_id: Mapped[UUID] = mapped_column(Uuid)
    encoded: Mapped[str] = mapped_column(Text)
    content_digest: Mapped[str] = mapped_column(String(64))
    __table_args__ = scoped(fk('evaluations','evaluation_id'), UniqueConstraint('tenant_id','legal_entity_id','evaluation_id'))


class RuleResultRow(Scoped, Identified, Base):
    __tablename__ = 'rule_results'
    evaluation_id: Mapped[UUID] = mapped_column(Uuid)
    rule_id: Mapped[str] = mapped_column(String(32))
    rule_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24))
    decision_effect: Mapped[str] = mapped_column(String(8))
    result: Mapped[dict] = mapped_column(J)
    __table_args__ = scoped(fk('evaluations','evaluation_id'),
        UniqueConstraint('tenant_id','legal_entity_id','evaluation_id','rule_id'),
        CheckConstraint("status IN ('PASS','FAIL','UNKNOWN','NOT_APPLICABLE','ERROR')"),
        CheckConstraint("decision_effect IN ('NONE','REVIEW','HOLD')"))


class EvidenceObject(Scoped, Identified, Base):
    __tablename__ = 'evidence_objects'
    evaluation_id: Mapped[UUID] = mapped_column(Uuid)
    rule_result_id: Mapped[UUID] = mapped_column(Uuid)
    reference: Mapped[dict] = mapped_column(J)
    __table_args__ = scoped(fk('evaluations','evaluation_id'), fk('rule_results','rule_result_id'))


class ReviewCase(Scoped, Identified, Base):
    __tablename__ = 'review_cases'
    evaluation_id: Mapped[UUID] = mapped_column(Uuid)
    transaction_id: Mapped[UUID] = mapped_column(Uuid)
    decision: Mapped[str] = mapped_column(String(8))
    branch: Mapped[str] = mapped_column(String(32))
    reasons: Mapped[list] = mapped_column(J)
    state: Mapped[str] = mapped_column(String(24), default='OPEN')
    __table_args__ = scoped(fk('evaluations','evaluation_id'), fk('transactions','transaction_id'),
        UniqueConstraint('tenant_id','legal_entity_id','evaluation_id'),
        CheckConstraint("decision IN ('REVIEW','HOLD')"),
        Index('ix_review_queue', 'tenant_id','legal_entity_id','state','decision','created_at'))


class Report(Scoped, Identified, Base):
    __tablename__ = 'reports'
    evaluation_id: Mapped[UUID] = mapped_column(Uuid)
    content: Mapped[dict] = mapped_column(J)
    html: Mapped[str] = mapped_column(Text)
    content_digest: Mapped[str] = mapped_column(String(64))
    __table_args__ = scoped(fk('evaluations','evaluation_id'), UniqueConstraint('tenant_id','legal_entity_id','evaluation_id'))


class AuditEvent(Scoped, Identified, Base):
    __tablename__ = 'audit_events'
    sequence: Mapped[int] = mapped_column(BigInteger)
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    action: Mapped[str] = mapped_column(String(64))
    object_id: Mapped[UUID] = mapped_column(Uuid)
    object_version: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(500))
    correlation_id: Mapped[str] = mapped_column(String(80))
    previous_hash: Mapped[str] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(J)
    __table_args__ = scoped(UniqueConstraint('tenant_id','sequence'), Index('ix_audit_scope_object','tenant_id','legal_entity_id','object_id','sequence'))


class Job(Scoped, Identified, Base):
    __tablename__ = 'jobs'
    transaction_id: Mapped[UUID] = mapped_column(Uuid)
    transaction_version: Mapped[int] = mapped_column(Integer)
    snapshot_id: Mapped[UUID] = mapped_column(Uuid)
    stage: Mapped[str] = mapped_column(String(32), default='EVALUATE')
    stage_version: Mapped[str] = mapped_column(String(32))
    stage_key: Mapped[str] = mapped_column(String(64))
    generation: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String(32), default='QUEUED')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    maximum_attempts: Mapped[int] = mapped_column(Integer, default=3)
    lease_owner: Mapped[UUID | None] = mapped_column(Uuid)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_error: Mapped[str | None] = mapped_column(String(64))
    result_evaluation_id: Mapped[UUID | None] = mapped_column(Uuid)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    __table_args__ = scoped(fk('transactions','transaction_id'), fk('reference_snapshots','snapshot_id'),
        fk('evaluations','result_evaluation_id'), UniqueConstraint('tenant_id','legal_entity_id','stage_key'),
        CheckConstraint("state IN ('QUEUED','RUNNING','RETRYABLE','SUCCEEDED','FAILED','CANCELLED','STALE')"),
        CheckConstraint('attempts >= 0 AND maximum_attempts > 0'),
        Index('ix_job_lease','tenant_id','legal_entity_id','state','available_at','lease_until'))


class OutboxEvent(Scoped, Identified, Base):
    __tablename__ = 'outbox_events'
    job_id: Mapped[UUID] = mapped_column(Uuid)
    event_type: Mapped[str] = mapped_column(String(48))
    schema_version: Mapped[str] = mapped_column(String(24), default='event-p1-v1')
    aggregate_id: Mapped[UUID] = mapped_column(Uuid)
    aggregate_version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(J)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = scoped(fk('jobs','job_id'), UniqueConstraint('tenant_id','legal_entity_id','job_id','event_type'))


class IdempotencyRecord(Scoped, Identified, Base):
    __tablename__ = 'idempotency_records'
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    endpoint: Mapped[str] = mapped_column(String(160))
    key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_status: Mapped[int] = mapped_column(Integer)
    response: Mapped[dict] = mapped_column(J)
    __table_args__ = scoped(UniqueConstraint('tenant_id','legal_entity_id','actor_id','endpoint','key'))


class ImportBatch(Scoped, Identified, Base):
    __tablename__ = 'import_batches'
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    filename: Mapped[str] = mapped_column(String(160))
    format: Mapped[str] = mapped_column(String(8))
    object_key: Mapped[str] = mapped_column(String(200))
    content_digest: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), default='PREVIEWED')
    row_count: Mapped[int] = mapped_column(Integer)
    __table_args__ = scoped(CheckConstraint("state IN ('PREVIEWED','COMMITTED')"))


class ImportRow(Scoped, Identified, Base):
    __tablename__ = 'import_rows'
    batch_id: Mapped[UUID] = mapped_column(Uuid)
    sheet: Mapped[str] = mapped_column(String(160))
    row_number: Mapped[int] = mapped_column(Integer)
    raw_values: Mapped[dict] = mapped_column(J)
    row_digest: Mapped[str] = mapped_column(String(64))
    canonical_payload: Mapped[dict | None] = mapped_column(J)
    validation_errors: Mapped[list] = mapped_column(J)
    transaction_id: Mapped[UUID | None] = mapped_column(Uuid)
    __table_args__ = scoped(fk('import_batches','batch_id'), fk('transactions','transaction_id'),
        UniqueConstraint('tenant_id','legal_entity_id','batch_id','sheet','row_number'), CheckConstraint('row_number > 0'))


class CapacityReservation(Scoped, Identified, Base):
    __tablename__ = 'capacity_reservations'
    transaction_id: Mapped[UUID] = mapped_column(Uuid)
    transaction_version: Mapped[int] = mapped_column(Integer)
    evaluation_id: Mapped[UUID] = mapped_column(Uuid)
    reference_id: Mapped[UUID] = mapped_column(Uuid)
    reference_version: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(24))
    amount: Mapped[Decimal] = mapped_column(Numeric(20,6))
    quantity: Mapped[Decimal] = mapped_column(Numeric(24,8), default=Decimal('0'))
    currency: Mapped[str] = mapped_column(String(3))
    state: Mapped[str] = mapped_column(String(16), default='ACTIVE')
    __table_args__ = scoped(fk('transactions','transaction_id'), fk('evaluations','evaluation_id'),
        fk('reference_records','reference_id',version='reference_version'),
        UniqueConstraint('tenant_id','legal_entity_id','evaluation_id','reference_id','kind'),
        CheckConstraint("kind IN ('BUDGET','PO_LINE','GRN_LINE')"),
        CheckConstraint('amount >= 0 AND quantity >= 0'),
        CheckConstraint("state IN ('ACTIVE','RELEASED')"),
        Index('ix_capacity_active','tenant_id','legal_entity_id','reference_id','kind','state'))


IMMUTABLE = [ReferenceRecord, ReferenceLink, ReferenceSnapshot, SnapshotMember,
    TransactionVersion, ApprovalRecord, Evaluation, EvaluationInput, RuleResultRow, EvidenceObject, Report, AuditEvent, IdempotencyRecord]


def forbid_mutation(mapper, connection, target):
    raise ValueError('Immutable financial fact: append a new version instead.')


for kind in IMMUTABLE:
    event.listen(kind, 'before_update', forbid_mutation)
    event.listen(kind, 'before_delete', forbid_mutation)

# Register additive Phase-2 tables for Alembic without weakening Phase-1 models.
from app.db import document_models  # noqa: E402,F401
from app.db import finance_models  # noqa: E402,F401
