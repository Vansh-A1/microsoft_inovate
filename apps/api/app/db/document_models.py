"""Additive scoped document facts and queue; existing finance-job FKs stay intact."""
from datetime import datetime
from uuid import UUID
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column
from app.core.serialization import utcnow
from app.db.models import Base, Scoped, Identified, J, scoped, fk, forbid_mutation


def document_fk(): return fk('document_versions','document_id',version='document_version')
def transaction_fk():
    return ForeignKeyConstraint(['tenant_id','legal_entity_id','transaction_id','transaction_version'],
        ['transaction_versions.tenant_id','transaction_versions.legal_entity_id','transaction_versions.transaction_id','transaction_versions.version'])


class Document(Scoped, Identified, Base):
    __tablename__ = 'documents'
    source_type: Mapped[str] = mapped_column(String(32))
    display_name: Mapped[str] = mapped_column(String(160))
    state: Mapped[str] = mapped_column(String(32), default='AWAITING_UPLOAD')
    last_error: Mapped[str | None] = mapped_column(String(64))
    last_successful_stage: Mapped[str | None] = mapped_column(String(32))
    generation: Mapped[int] = mapped_column(Integer, default=1)
    segmentation_state: Mapped[str] = mapped_column(String(32), default='UNCONFIRMED')
    __table_args__ = scoped(CheckConstraint("source_type IN ('VENDOR_INVOICE','EMPLOYEE_RECEIPT','SUPPORTING_DOCUMENT')"),
        CheckConstraint("state IN ('AWAITING_UPLOAD','UPLOADED','QUEUED','PROCESSING','QUARANTINED','NEEDS_INPUT','DEPENDENCY_UNAVAILABLE','FAILED_RETRYABLE','FAILED_FINAL','READY')"))


class UploadSession(Scoped, Identified, Base):
    __tablename__ = 'upload_sessions'
    document_id: Mapped[UUID] = mapped_column(Uuid)
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    correlation_id: Mapped[str] = mapped_column(String(64))
    declared_mime: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(32), default='OPEN')
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    storage_key: Mapped[str | None] = mapped_column(String(128))
    sha256: Mapped[str | None] = mapped_column(String(64))
    byte_size: Mapped[int | None] = mapped_column(Integer)
    __table_args__ = scoped(fk('documents','document_id'), CheckConstraint("state IN ('OPEN','UPLOADED','FINALIZED','QUARANTINED','EXPIRED')"))


class DocumentVersion(Scoped, Base):
    __tablename__ = 'document_versions'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    upload_id: Mapped[UUID] = mapped_column(Uuid)
    storage_key: Mapped[str] = mapped_column(String(128))
    storage_version: Mapped[int] = mapped_column(Integer, default=1)
    sha256: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    detected_mime: Mapped[str] = mapped_column(String(64))
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    correlation_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (ForeignKeyConstraint(['tenant_id','legal_entity_id'], ['legal_entities.tenant_id','legal_entities.id']), fk('documents','id'),fk('upload_sessions','upload_id'),
        UniqueConstraint('tenant_id','legal_entity_id','id','version'),
        UniqueConstraint('tenant_id','legal_entity_id','upload_id'),CheckConstraint('version > 0 AND byte_size > 0'))


class DocumentPage(Scoped, Identified, Base):
    __tablename__ = 'document_pages'
    document_id: Mapped[UUID] = mapped_column(Uuid)
    document_version: Mapped[int] = mapped_column(Integer)
    page: Mapped[int] = mapped_column(Integer)
    processor_version: Mapped[str] = mapped_column(String(32))
    preview_key: Mapped[str] = mapped_column(String(128))
    page_sha256: Mapped[str] = mapped_column(String(64))
    native_text: Mapped[str] = mapped_column(Text)
    spans: Mapped[list] = mapped_column(J)
    transform: Mapped[dict] = mapped_column(J)
    quality: Mapped[dict] = mapped_column(J)
    route: Mapped[str] = mapped_column(String(32))
    __table_args__ = scoped(document_fk(),CheckConstraint('page >= 1 AND page <= 30'),
        UniqueConstraint('tenant_id','legal_entity_id','document_id','document_version','processor_version','page'))


class DocumentJob(Scoped, Identified, Base):
    __tablename__ = 'document_jobs'
    document_id: Mapped[UUID] = mapped_column(Uuid)
    document_version: Mapped[int] = mapped_column(Integer)
    generation: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String(32))
    stage_version: Mapped[str] = mapped_column(String(32))
    stage_key: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(32), default='QUEUED')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    maximum_attempts: Mapped[int] = mapped_column(Integer, default=3)
    lease_owner: Mapped[UUID | None] = mapped_column(Uuid)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    correlation_id: Mapped[str] = mapped_column(String(64))
    last_error: Mapped[str | None] = mapped_column(String(64))
    result_metadata: Mapped[dict] = mapped_column(J, default=dict)
    __table_args__ = scoped(document_fk(),UniqueConstraint('tenant_id','legal_entity_id','stage_key'),
        CheckConstraint("stage IN ('PREPROCESS','EXTRACT','NORMALIZE','VALIDATE','FINALIZE')"),
        CheckConstraint("state IN ('QUEUED','RUNNING','RETRYABLE','SUCCEEDED','FAILED','STALE')"),
        CheckConstraint('attempts >= 0 AND maximum_attempts > 0'))


class DocumentOutbox(Scoped, Identified, Base):
    __tablename__ = 'document_outbox'
    job_id: Mapped[UUID] = mapped_column(Uuid)
    event_type: Mapped[str] = mapped_column(String(48), default='DOCUMENT_STAGE_READY')
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = scoped(fk('document_jobs','job_id'),UniqueConstraint('tenant_id','legal_entity_id','job_id'))


class ExtractionRun(Scoped, Identified, Base):
    __tablename__ = 'extraction_runs'
    document_id: Mapped[UUID] = mapped_column(Uuid)
    document_version: Mapped[int] = mapped_column(Integer)
    job_id: Mapped[UUID] = mapped_column(Uuid)
    attempt: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    adapter: Mapped[str] = mapped_column(String(80))
    metadata_json: Mapped[dict] = mapped_column(J)
    result: Mapped[dict] = mapped_column(J)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = scoped(document_fk(),fk('document_jobs','job_id'),
        UniqueConstraint('tenant_id','legal_entity_id','job_id','attempt'))


class Observation(Scoped, Identified, Base):
    __tablename__ = 'field_observations'
    extraction_run_id: Mapped[UUID] = mapped_column(Uuid)
    field_path: Mapped[str] = mapped_column(String(160))
    state: Mapped[str] = mapped_column(String(32))
    raw_value: Mapped[str | None] = mapped_column(Text)
    parsed_candidate: Mapped[str | None] = mapped_column(Text)
    source: Mapped[dict | None] = mapped_column(J)
    diagnostic: Mapped[str | None] = mapped_column(Text)
    __table_args__ = scoped(fk('extraction_runs','extraction_run_id'),
        CheckConstraint("state IN ('PRESENT','MISSING','ILLEGIBLE','AMBIGUOUS','NOT_APPLICABLE')"),
        UniqueConstraint('tenant_id','legal_entity_id','extraction_run_id','field_path'))


class DocumentDraft(Scoped, Identified, Base):
    __tablename__ = 'document_drafts'
    document_id: Mapped[UUID] = mapped_column(Uuid)
    document_version: Mapped[int] = mapped_column(Integer)
    extraction_run_id: Mapped[UUID] = mapped_column(Uuid)
    normalizer_version: Mapped[str] = mapped_column(String(32))
    stage: Mapped[str] = mapped_column(String(32))
    candidate: Mapped[dict] = mapped_column(J)
    traces: Mapped[list] = mapped_column(J)
    findings: Mapped[list] = mapped_column(J)
    __table_args__ = scoped(document_fk(),fk('extraction_runs','extraction_run_id'),
        UniqueConstraint('tenant_id','legal_entity_id','extraction_run_id','stage','normalizer_version'))


class TransactionDocument(Scoped, Identified, Base):
    __tablename__ = 'transaction_documents'
    transaction_id: Mapped[UUID] = mapped_column(Uuid)
    transaction_version: Mapped[int] = mapped_column(Integer)
    document_id: Mapped[UUID] = mapped_column(Uuid)
    document_version: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(32))
    first_page: Mapped[int] = mapped_column(Integer)
    last_page: Mapped[int] = mapped_column(Integer)
    verification_id: Mapped[UUID | None] = mapped_column(Uuid)
    verification_version: Mapped[int | None] = mapped_column(Integer)
    draft_id: Mapped[UUID | None] = mapped_column(Uuid)
    __table_args__ = scoped(document_fk(),transaction_fk(),fk('reference_records','verification_id',version='verification_version'),
        fk('document_drafts','draft_id'),CheckConstraint('first_page >= 1 AND last_page >= first_page AND last_page <= 30'),
        CheckConstraint("role IN ('INVOICE','RECEIPT','PO','SUPPORT')"),
        UniqueConstraint('tenant_id','legal_entity_id','transaction_id','transaction_version','document_id'))


class SourceCorrection(Scoped, Identified, Base):
    __tablename__ = 'source_corrections'
    transaction_id: Mapped[UUID] = mapped_column(Uuid)
    transaction_version: Mapped[int] = mapped_column(Integer)
    document_id: Mapped[UUID] = mapped_column(Uuid)
    document_version: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    reason: Mapped[str] = mapped_column(String(500))
    changes: Mapped[list] = mapped_column(J)
    __table_args__ = scoped(document_fk(),transaction_fk())


class ImportCell(Scoped, Identified, Base):
    __tablename__ = 'import_cells'
    row_id: Mapped[UUID] = mapped_column(Uuid)
    batch_id: Mapped[UUID] = mapped_column(Uuid)
    sheet: Mapped[str] = mapped_column(String(160))
    row_number: Mapped[int] = mapped_column(Integer)
    column: Mapped[str] = mapped_column(String(160))
    field_path: Mapped[str] = mapped_column(String(160))
    raw_value: Mapped[str | None] = mapped_column(Text)
    parsed_value: Mapped[str | None] = mapped_column(Text)
    validation: Mapped[dict] = mapped_column(J)
    __table_args__ = scoped(fk('import_rows','row_id'),fk('import_batches','batch_id'),
        CheckConstraint('row_number > 0'),UniqueConstraint('tenant_id','legal_entity_id','row_id','column','field_path'))


DOCUMENT_IMMUTABLE = [DocumentVersion, DocumentPage, ExtractionRun, Observation, DocumentDraft, TransactionDocument, SourceCorrection, ImportCell]
for kind in DOCUMENT_IMMUTABLE:
    event.listen(kind, 'before_update', forbid_mutation)
    event.listen(kind, 'before_delete', forbid_mutation)
