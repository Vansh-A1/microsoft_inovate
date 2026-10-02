"""Immutable source references from spec section 13.1, without persistence.

UUIDs and versions are validated structurally; existence, ownership, authorized
resolution, and original-page transform accuracy require later services. Missing
evidence cites an existing transaction/policy plus a search snapshot, never a
fabricated ID for an absent approval or matched record.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from uuid import UUID


class EvidenceKind(Enum):
    DOCUMENT_FIELD = "DOCUMENT_FIELD"
    IMPORT_CELL = "IMPORT_CELL"
    TRANSACTION = "TRANSACTION"
    PO_LINE = "PO_LINE"
    GRN_LINE = "GRN_LINE"
    CONTRACT = "CONTRACT"
    POLICY_CLAUSE = "POLICY_CLAUSE"
    MASTER_RECORD = "MASTER_RECORD"
    APPROVAL = "APPROVAL"
    BUDGET_LEDGER = "BUDGET_LEDGER"
    HISTORICAL_AGGREGATE = "HISTORICAL_AGGREGATE"


def _require_uuid(name: str, value: UUID) -> None:
    if not isinstance(value, UUID):
        raise TypeError(f"{name} must be a UUID, not a display/business number")
    if value.int == 0:
        raise ValueError(f"{name} must not be a nil UUID placeholder")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, not bool or float")
    if value < 1:
        raise ValueError(f"{name} must be one-based/positive")


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Normalized x1/y1/x2/y2 in original-page orientation.

    Coordinate floats are dimensionless positions, never financial amounts.
    Equal edges are allowed by the specified inclusive bounds.
    """

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        for name in ("x1", "y1", "x2", "y2"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a numeric coordinate")
            if not 0 <= value <= 1 or not math.isfinite(value):
                raise ValueError(f"{name} must be finite and in [0, 1]")
        if self.x1 > self.x2 or self.y1 > self.y2:
            raise ValueError("bounding box edges must satisfy x1 <= x2 and y1 <= y2")


@dataclass(frozen=True, slots=True)
class ImportCellLocator:
    """Original import batch/sheet/one-based row/column identifier; no importer."""

    batch_id: UUID
    sheet: str
    row: int
    column: str

    def __post_init__(self) -> None:
        _require_uuid("batch_id", self.batch_id)
        _require_text("sheet", self.sheet)
        _require_positive_int("row", self.row)
        _require_text("column", self.column)


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """A scoped existing record/version with optional source locators.

    IDs must already be UUID values; no invoice-number matching or identity
    invention occurs here. Text versions support policy/master tags; numeric
    versions are positive. observed_value is optional text for a raw/redacted
    representation, not an implicit numeric value or a rule-status substitute.
    """

    kind: EvidenceKind
    record_id: UUID
    record_version: int | str
    tenant_id: UUID
    legal_entity_id: UUID
    field_path: str | None = None
    document_id: UUID | None = None
    page: int | None = None
    bbox: BoundingBox | None = None
    snapshot_id: UUID | None = None
    observed_value: str | None = None
    import_cell: ImportCellLocator | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EvidenceKind):
            raise TypeError("kind must be an EvidenceKind")
        for name in ("record_id", "tenant_id", "legal_entity_id"):
            _require_uuid(name, getattr(self, name))
        for name in ("document_id", "snapshot_id"):
            value = getattr(self, name)
            if value is not None:
                _require_uuid(name, value)
        if isinstance(self.record_version, str):
            _require_text("record_version", self.record_version)
        else:
            _require_positive_int("record_version", self.record_version)
        if self.field_path is not None:
            _require_text("field_path", self.field_path)
        if self.observed_value is not None and not isinstance(self.observed_value, str):
            raise TypeError("observed_value must be text or None; do not infer money or booleans")
        if self.page is not None:
            _require_positive_int("page", self.page)
            if self.document_id is None:
                raise ValueError("a page locator requires document_id")
        if self.bbox is not None:
            if not isinstance(self.bbox, BoundingBox):
                raise TypeError("bbox must be a BoundingBox or None")
            if self.document_id is None or self.page is None:
                raise ValueError("a bounding box requires document_id and one-based page")
        if self.import_cell is not None and not isinstance(self.import_cell, ImportCellLocator):
            raise TypeError("import_cell must be an ImportCellLocator or None")
        if self.kind is EvidenceKind.IMPORT_CELL and self.import_cell is None:
            raise ValueError("IMPORT_CELL requires batch, sheet, row, and column provenance")

    @property
    def coordinate_system(self) -> str | None:
        """No coordinates are inferred when bbox is absent."""
        return "normalized_original_page" if self.bbox is not None else None
