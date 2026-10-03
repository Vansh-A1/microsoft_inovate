"""Phase-4 immutable workflow and operational facts; existing projections retained."""
from uuid import UUID
from sqlalchemy import String, Integer, Uuid, UniqueConstraint, CheckConstraint, event
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models import Base, Scoped, Identified, J, scoped, fk, forbid_mutation


class ReviewAction(Scoped, Identified, Base):
    __tablename__ = 'review_actions'
    review_case_id: Mapped[UUID] = mapped_column(Uuid)
    review_version: Mapped[int] = mapped_column(Integer)
    transaction_version: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    action: Mapped[str] = mapped_column(String(40))
    reason_code: Mapped[str] = mapped_column(String(80))
    comment: Mapped[str] = mapped_column(String(500))
    evidence: Mapped[list] = mapped_column(J)
    details: Mapped[dict] = mapped_column(J)
    __table_args__ = scoped(fk('review_cases','review_case_id'),
        UniqueConstraint('tenant_id','legal_entity_id','review_case_id','review_version'),
        CheckConstraint('review_version > 1 AND transaction_version > 0'))


class OperationRecord(Scoped, Identified, Base):
    __tablename__ = 'operation_records'
    operation_key: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(32))
    object_id: Mapped[UUID] = mapped_column(Uuid)
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    details: Mapped[dict] = mapped_column(J)
    __table_args__ = scoped(UniqueConstraint('tenant_id','legal_entity_id','operation_key'))


for model in (ReviewAction, OperationRecord):
    event.listen(model,'before_update',forbid_mutation)
    event.listen(model,'before_delete',forbid_mutation)
