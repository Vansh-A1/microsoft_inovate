"""Immutable Phase-5 intelligence facts. No training script can activate a model."""
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, Integer, Uuid, DateTime, UniqueConstraint, CheckConstraint, ForeignKeyConstraint, Index, event
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models import Base, Scoped, Identified, J, scoped, fk, forbid_mutation


class FeatureSchema(Scoped, Identified, Base):
    __tablename__='feature_schemas'
    version:Mapped[str]=mapped_column(String(40))
    content:Mapped[dict]=mapped_column(J)
    content_digest:Mapped[str]=mapped_column(String(64))
    __table_args__=scoped(UniqueConstraint('tenant_id','legal_entity_id','version'))


class RiskHistorySource(Scoped, Identified, Base):
    __tablename__='risk_history_sources'
    reference_id:Mapped[UUID]=mapped_column(Uuid)
    reference_version:Mapped[int]=mapped_column(Integer)
    object_id:Mapped[UUID]=mapped_column(Uuid)
    facts:Mapped[dict]=mapped_column(J)
    source_digest:Mapped[str]=mapped_column(String(64))
    __table_args__=scoped(fk('reference_records','reference_id',version='reference_version'),
        UniqueConstraint('tenant_id','legal_entity_id','reference_id','reference_version'),
        Index('ix_risk_history_cutoff','tenant_id','legal_entity_id','created_at'))


class FeatureSnapshot(Scoped, Identified, Base):
    __tablename__='feature_snapshots'
    evaluation_id:Mapped[UUID]=mapped_column(Uuid)
    schema_id:Mapped[UUID]=mapped_column(Uuid)
    content:Mapped[dict]=mapped_column(J)
    content_digest:Mapped[str]=mapped_column(String(64))
    __table_args__=scoped(fk('evaluations','evaluation_id'),fk('feature_schemas','schema_id'),
        UniqueConstraint('tenant_id','legal_entity_id','evaluation_id'))


class FeedbackLabel(Scoped, Identified, Base):
    __tablename__='feedback_labels'
    evaluation_id:Mapped[UUID]=mapped_column(Uuid)
    review_case_id:Mapped[UUID]=mapped_column(Uuid)
    review_action_id:Mapped[UUID]=mapped_column(Uuid)
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    taxonomy:Mapped[str]=mapped_column(String(40))
    label:Mapped[str]=mapped_column(String(40))
    quality:Mapped[str]=mapped_column(String(16))
    reason:Mapped[str]=mapped_column(String(500))
    evidence:Mapped[list]=mapped_column(J)
    supersedes_id:Mapped[UUID|None]=mapped_column(Uuid)
    __table_args__=scoped(fk('evaluations','evaluation_id'),fk('review_cases','review_case_id'),
        fk('review_actions','review_action_id'),fk('feedback_labels','supersedes_id'),
        CheckConstraint("quality IN ('FINAL','PROVISIONAL')"),
        CheckConstraint("label IN ('CLEAN_CONFIRMED','DUPLICATE_CONFIRMED','POLICY_EXCEPTION','DOCUMENT_CORRECTION_ONLY','DISTINCT_CONFIRMED','INSUFFICIENT_INFORMATION')"),
        Index('ix_feedback_evaluation','tenant_id','legal_entity_id','evaluation_id','created_at'))


class AuditSample(Scoped, Identified, Base):
    __tablename__='risk_audit_samples'
    evaluation_id:Mapped[UUID]=mapped_column(Uuid)
    review_case_id:Mapped[UUID]=mapped_column(Uuid)
    campaign:Mapped[str]=mapped_column(String(80))
    rate:Mapped[str]=mapped_column(String(20))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    __table_args__=scoped(fk('evaluations','evaluation_id'),fk('review_cases','review_case_id'),
        UniqueConstraint('tenant_id','legal_entity_id','evaluation_id'))


class DatasetVersion(Scoped, Identified, Base):
    __tablename__='risk_datasets'
    schema_id:Mapped[UUID]=mapped_column(Uuid)
    manifest:Mapped[dict]=mapped_column(J)
    content_digest:Mapped[str]=mapped_column(String(64))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    __table_args__=scoped(fk('feature_schemas','schema_id'),UniqueConstraint('tenant_id','legal_entity_id','content_digest'))


class TrainingRun(Scoped, Identified, Base):
    __tablename__='risk_training_runs'
    dataset_id:Mapped[UUID]=mapped_column(Uuid)
    schema_id:Mapped[UUID]=mapped_column(Uuid)
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    state:Mapped[str]=mapped_column(String(32))
    metadata_record:Mapped[dict]=mapped_column(J)
    __table_args__=scoped(fk('risk_datasets','dataset_id'),fk('feature_schemas','schema_id'),
        CheckConstraint("state IN ('SUPERVISED_DEFERRED','BASELINE_BUILT')"))


class ModelVersion(Scoped, Identified, Base):
    __tablename__='risk_models'
    algorithm:Mapped[str]=mapped_column(String(40))
    version:Mapped[str]=mapped_column(String(64))
    schema_id:Mapped[UUID]=mapped_column(Uuid)
    dataset_id:Mapped[UUID]=mapped_column(Uuid)
    training_run_id:Mapped[UUID]=mapped_column(Uuid)
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    artifact_key:Mapped[str]=mapped_column(String(240))
    artifact_sha256:Mapped[str]=mapped_column(String(64))
    metadata_record:Mapped[dict]=mapped_column(J)
    __table_args__=scoped(fk('feature_schemas','schema_id'),fk('risk_datasets','dataset_id'),fk('risk_training_runs','training_run_id'),
        UniqueConstraint('tenant_id','legal_entity_id','version'))


class ModelEvent(Scoped, Identified, Base):
    __tablename__='risk_model_events'
    model_id:Mapped[UUID]=mapped_column(Uuid)
    version:Mapped[int]=mapped_column(Integer)
    state:Mapped[str]=mapped_column(String(16))
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    reason:Mapped[str]=mapped_column(String(500))
    details:Mapped[dict]=mapped_column(J)
    __table_args__=scoped(fk('risk_models','model_id'),
        UniqueConstraint('tenant_id','legal_entity_id','model_id','version'),
        CheckConstraint("state IN ('CANDIDATE','EVALUATED','APPROVED','SHADOW','ACTIVE','RETIRED','REJECTED')"))


class RiskDeployment(Scoped, Identified, Base):
    __tablename__='risk_deployments'
    version:Mapped[int]=mapped_column(Integer)
    mode:Mapped[str]=mapped_column(String(32))
    model_id:Mapped[UUID|None]=mapped_column(Uuid)
    previous_id:Mapped[UUID|None]=mapped_column(Uuid)
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    threshold:Mapped[str]=mapped_column(String(20))
    reason:Mapped[str]=mapped_column(String(500))
    __table_args__=scoped(fk('risk_models','model_id'),fk('risk_deployments','previous_id'),
        UniqueConstraint('tenant_id','legal_entity_id','version'),
        CheckConstraint("mode IN ('RULES_ONLY','SHADOW','RULES_PLUS_ANOMALY','RULES_PLUS_MODEL')"))


class RiskScore(Scoped, Identified, Base):
    __tablename__='risk_scores'
    evaluation_id:Mapped[UUID]=mapped_column(Uuid)
    feature_snapshot_id:Mapped[UUID]=mapped_column(Uuid)
    deployment_id:Mapped[UUID|None]=mapped_column(Uuid)
    model_id:Mapped[UUID|None]=mapped_column(Uuid)
    content:Mapped[dict]=mapped_column(J)
    content_digest:Mapped[str]=mapped_column(String(64))
    __table_args__=scoped(fk('evaluations','evaluation_id'),fk('feature_snapshots','feature_snapshot_id'),
        fk('risk_deployments','deployment_id'),fk('risk_models','model_id'),
        UniqueConstraint('tenant_id','legal_entity_id','evaluation_id'))


class MonitoringSnapshot(Scoped, Identified, Base):
    __tablename__='risk_monitoring'
    dataset_id:Mapped[UUID|None]=mapped_column(Uuid)
    actor_id:Mapped[UUID]=mapped_column(Uuid)
    content:Mapped[dict]=mapped_column(J)
    content_digest:Mapped[str]=mapped_column(String(64))
    __table_args__=scoped(fk('risk_datasets','dataset_id'),UniqueConstraint('tenant_id','legal_entity_id','content_digest'))


MODELS=(FeatureSchema,RiskHistorySource,FeatureSnapshot,FeedbackLabel,AuditSample,DatasetVersion,TrainingRun,
        ModelVersion,ModelEvent,RiskDeployment,RiskScore,MonitoringSnapshot)
for model in MODELS:
    event.listen(model,'before_update',forbid_mutation)
    event.listen(model,'before_delete',forbid_mutation)
