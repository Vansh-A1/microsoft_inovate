"""Provider-independent observations, never finance decisions or normalization.

All nested contracts are frozen. Candidate text is unverified and separate from
raw observations; uncertain fields cannot acquire a chosen candidate. Page/bbox
semantics come from EvidenceReference, not another coordinate implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from enum import Enum
import hashlib
import json
import re
from uuid import UUID

from app.domain.evidence import BoundingBox, EvidenceKind, EvidenceReference


SCHEMA_VERSION = "extraction-v1"
MAX_HEADER_FIELDS = 64
MAX_LINE_ITEMS = 200
MAX_ROW_FIELDS = 16


class ExtractionObservationState(Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    ILLEGIBLE = "ILLEGIBLE"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_APPLICABLE = "NOT_APPLICABLE"

    def __bool__(self):
        raise TypeError("compare observation states explicitly")


class ExtractionStatus(Enum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"

    def __bool__(self):
        raise TypeError("compare extraction status explicitly")


class DocumentSourceType(Enum):
    VENDOR_INVOICE = "VENDOR_INVOICE"
    EMPLOYEE_RECEIPT = "EMPLOYEE_RECEIPT"


def _text(name, value, optional=False):
    if value is None and optional:
        return
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text")
    if not value.strip():
        raise ValueError(f"{name} must not be blank")


def _uuid(name, value):
    if not isinstance(value, UUID):
        raise TypeError(f"{name} must be a UUID")
    if value.int == 0:
        raise ValueError(f"{name} must not be nil")


def _positive_int(name, value):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if value < 1:
        raise ValueError(f"{name} must be positive/one-based")


def _tuple(name, value, kind, maximum):
    if not isinstance(value, tuple) or not all(isinstance(item, kind) for item in value):
        raise TypeError(f"{name} must be a tuple of {kind.__name__}")
    if len(value) > maximum:
        raise ValueError(f"{name} exceeds the contract bound {maximum}")


def _unique(name, values):
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {name}")


def to_data(value):
    """JSON-safe projection; amount candidates remain text, not numeric values."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return format(value, "f")
    if is_dataclass(value):
        return {field.name: to_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [to_data(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class VersionMetadata:
    name: str
    version: str

    def __post_init__(self):
        _text("name", self.name)
        _text("version", self.version)


@dataclass(frozen=True, slots=True)
class DocumentPage:
    page: int
    available_text: str | None = None
    artifact_ref: str | None = None
    declared_rotation_degrees: int | None = None

    def __post_init__(self):
        _positive_int("page", self.page)
        if self.available_text is not None and not isinstance(self.available_text, str):
            raise TypeError("available_text must be text or None")
        _text("artifact_ref", self.artifact_ref, optional=True)
        if self.declared_rotation_degrees is not None:
            if type(self.declared_rotation_degrees) is not int or self.declared_rotation_degrees not in {0, 90, 180, 270}:
                raise ValueError("declared rotation must be 0/90/180/270 metadata")


@dataclass(frozen=True, slots=True)
class DocumentBundle:
    document_id: UUID
    document_version: int
    tenant_id: UUID
    legal_entity_id: UUID
    source_type: DocumentSourceType
    pages: tuple[DocumentPage, ...]
    synthetic: bool = False
    source_artifact_ref: str | None = None
    metadata: tuple[VersionMetadata, ...] = ()

    def __post_init__(self):
        for name in ("document_id", "tenant_id", "legal_entity_id"):
            _uuid(name, getattr(self, name))
        _positive_int("document_version", self.document_version)
        if not isinstance(self.source_type, DocumentSourceType):
            raise TypeError("source_type must be DocumentSourceType")
        _tuple("pages", self.pages, DocumentPage, 30)
        if not self.pages:
            raise ValueError("at least one page reference is required")
        numbers = [p.page for p in self.pages]
        _unique("page", numbers)
        if numbers != sorted(numbers):
            raise ValueError("pages must be ordered")
        if type(self.synthetic) is not bool:
            raise TypeError("synthetic must be bool")
        _text("source_artifact_ref", self.source_artifact_ref, optional=True)
        _tuple("metadata", self.metadata, VersionMetadata, 32)
        _unique("metadata name", [m.name for m in self.metadata])

    def digest(self):
        payload = json.dumps(to_data(self), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class FieldObservation:
    """Observed text and unverified candidate; diagnostics are uncalibrated notes."""

    field_path: str
    state: ExtractionObservationState
    raw_value: str | None = None
    parsed_candidate: str | None = None
    source: EvidenceReference | None = None
    diagnostic_note: str | None = None

    def __post_init__(self):
        _text("field_path", self.field_path)
        if re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*", self.field_path) is None:
            raise ValueError("field_path must be a simple named observation path")
        forbidden = {"decision", "screening_decision", "eligibility", "vendor_approved", "expense_reimbursable", "budget_sufficient", "bank_change_approved"}
        if set(self.field_path.split(".")) & forbidden:
            raise ValueError("finance decisions are not extraction observations")
        if not isinstance(self.state, ExtractionObservationState):
            raise TypeError("state must be ExtractionObservationState")
        _text("raw_value", self.raw_value, optional=True)
        _text("parsed_candidate", self.parsed_candidate, optional=True)
        _text("diagnostic_note", self.diagnostic_note, optional=True)
        if self.state is ExtractionObservationState.PRESENT and self.raw_value is None:
            raise ValueError("PRESENT requires observed text")
        if self.state is ExtractionObservationState.AMBIGUOUS and self.raw_value is None:
            raise ValueError("AMBIGUOUS requires the ambiguous observation")
        if self.state is not ExtractionObservationState.PRESENT and self.parsed_candidate is not None:
            raise ValueError("uncertainty cannot become a chosen parsed candidate")
        if self.state is ExtractionObservationState.MISSING and self.raw_value is not None:
            raise ValueError("MISSING cannot contain an invented raw value")
        if self.source is not None:
            if not isinstance(self.source, EvidenceReference):
                raise TypeError("source must be EvidenceReference")
            if self.source.kind is not EvidenceKind.DOCUMENT_FIELD or self.source.document_id != self.source.record_id:
                raise ValueError("source must identify its DOCUMENT_FIELD record/document")

    @property
    def page(self):
        return self.source.page if self.source is not None else None

    @property
    def bbox(self):
        return self.source.bbox if self.source is not None else None


@dataclass(frozen=True, slots=True)
class LineItemObservation:
    row_index: int
    fields: tuple[FieldObservation, ...]

    def __post_init__(self):
        _positive_int("row_index", self.row_index)
        if self.row_index > MAX_LINE_ITEMS:
            raise ValueError("row_index exceeds the bounded representation")
        _tuple("fields", self.fields, FieldObservation, MAX_ROW_FIELDS)
        if not self.fields:
            raise ValueError("a row must have explicit observations")
        _unique("row field", [f.field_path for f in self.fields])


@dataclass(frozen=True, slots=True)
class AdapterMetadata:
    adapter_id: str
    adapter_version: str
    provider_id: str
    model_id: str | None = None
    prompt_template_version: str | None = None
    runtime_versions: tuple[VersionMetadata, ...] = ()

    def __post_init__(self):
        for name in ("adapter_id", "adapter_version", "provider_id"):
            _text(name, getattr(self, name))
        _text("model_id", self.model_id, optional=True)
        _text("prompt_template_version", self.prompt_template_version, optional=True)
        _tuple("runtime_versions", self.runtime_versions, VersionMetadata, 32)
        _unique("runtime package", [v.name for v in self.runtime_versions])


@dataclass(frozen=True, slots=True)
class AdapterCapabilities:
    page_locators: bool
    bounding_boxes: bool
    line_items: bool
    visual_input: bool

    def __post_init__(self):
        if any(type(getattr(self, f.name)) is not bool for f in fields(self)):
            raise TypeError("capabilities must be explicit bool values")
        if self.bounding_boxes and not self.page_locators:
            raise ValueError("bounding boxes require page locators")


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    run_id: UUID
    document_id: UUID
    document_version: int
    tenant_id: UUID
    legal_entity_id: UUID
    schema_version: str
    metadata: AdapterMetadata
    status: ExtractionStatus
    header_fields: tuple[FieldObservation, ...]
    line_items: tuple[LineItemObservation, ...] = ()
    elapsed_ms: Decimal | None = None
    raw_artifact_ref: str | None = None
    failure_code: str | None = None

    def __post_init__(self):
        for name in ("run_id", "document_id", "tenant_id", "legal_entity_id"):
            _uuid(name, getattr(self, name))
        _positive_int("document_version", self.document_version)
        _text("schema_version", self.schema_version)
        if not isinstance(self.metadata, AdapterMetadata):
            raise TypeError("metadata must be AdapterMetadata")
        if not isinstance(self.status, ExtractionStatus):
            raise TypeError("status must be ExtractionStatus, never a finance/rule state")
        _tuple("header_fields", self.header_fields, FieldObservation, MAX_HEADER_FIELDS)
        _tuple("line_items", self.line_items, LineItemObservation, MAX_LINE_ITEMS)
        _unique("header field", [f.field_path for f in self.header_fields])
        _unique("row index", [r.row_index for r in self.line_items])
        if [r.row_index for r in self.line_items] != sorted(r.row_index for r in self.line_items):
            raise ValueError("rows must be ordered")
        if self.elapsed_ms is not None:
            if not isinstance(self.elapsed_ms, Decimal):
                raise TypeError("elapsed_ms must be Decimal or None")
            if not self.elapsed_ms.is_finite() or self.elapsed_ms < 0:
                raise ValueError("elapsed_ms must be finite and nonnegative")
        _text("raw_artifact_ref", self.raw_artifact_ref, optional=True)
        _text("failure_code", self.failure_code, optional=True)
        if self.status in {ExtractionStatus.FAILED, ExtractionStatus.UNSUPPORTED} and self.failure_code is None:
            raise ValueError("failed/unsupported extraction requires a failure code")
        for observation in self.observations():
            source = observation.source
            if source is not None and (source.record_id != self.document_id or source.record_version != self.document_version or source.tenant_id != self.tenant_id or source.legal_entity_id != self.legal_entity_id):
                raise ValueError("observation source document/version/scope mismatch")

    def observations(self):
        return self.header_fields + tuple(f for row in self.line_items for f in row.fields)

    def validate_binding(self, bundle, schema_version):
        if not isinstance(bundle, DocumentBundle):
            raise TypeError("bundle must be DocumentBundle")
        if any(getattr(self, name) != getattr(bundle, name) for name in ("document_id", "document_version", "tenant_id", "legal_entity_id")) or self.schema_version != schema_version:
            raise ValueError("result/input document/version/scope/schema mismatch")
        pages = {p.page for p in bundle.pages}
        if any(f.page is not None and f.page not in pages for f in self.observations()):
            raise ValueError("observation page is not in the document bundle")


def _source_from_data(data):
    if data is None:
        return None
    values = dict(data)
    values["kind"] = EvidenceKind(values["kind"])
    for name in ("record_id", "tenant_id", "legal_entity_id", "document_id", "snapshot_id"):
        if values.get(name) is not None:
            values[name] = UUID(values[name])
    if values.get("bbox") is not None:
        values["bbox"] = BoundingBox(**values["bbox"])
    return EvidenceReference(**values)


def observation_from_data(data):
    values = dict(data)
    values["state"] = ExtractionObservationState(values["state"])
    values["source"] = _source_from_data(values.get("source"))
    return FieldObservation(**values)


def row_from_data(data):
    values = dict(data)
    values["fields"] = tuple(observation_from_data(f) for f in values["fields"])
    return LineItemObservation(**values)


def bundle_from_data(data):
    values = dict(data)
    for name in ("document_id", "tenant_id", "legal_entity_id"):
        values[name] = UUID(values[name])
    values["source_type"] = DocumentSourceType(values["source_type"])
    values["pages"] = tuple(DocumentPage(**p) for p in values["pages"])
    values["metadata"] = tuple(VersionMetadata(**v) for v in values.get("metadata", []))
    return DocumentBundle(**values)


def result_from_data(data):
    values = dict(data)
    for name in ("run_id", "document_id", "tenant_id", "legal_entity_id"):
        values[name] = UUID(values[name])
    metadata = dict(values["metadata"])
    metadata["runtime_versions"] = tuple(VersionMetadata(**v) for v in metadata.get("runtime_versions", []))
    values["metadata"] = AdapterMetadata(**metadata)
    values["status"] = ExtractionStatus(values["status"])
    values["header_fields"] = tuple(observation_from_data(f) for f in values["header_fields"])
    values["line_items"] = tuple(row_from_data(r) for r in values.get("line_items", []))
    if values.get("elapsed_ms") is not None:
        if not isinstance(values["elapsed_ms"], str):
            raise TypeError("serialized elapsed_ms must be decimal text")
        values["elapsed_ms"] = Decimal(values["elapsed_ms"])
    return ExtractionResult(**values)
