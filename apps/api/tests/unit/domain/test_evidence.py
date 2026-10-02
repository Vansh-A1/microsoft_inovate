"""Truthful references, structural scope, and source-coordinate validation."""

from dataclasses import FrozenInstanceError
from decimal import Decimal
from uuid import UUID

import pytest

from app.domain.evidence import BoundingBox, EvidenceKind, EvidenceReference, ImportCellLocator


TENANT = UUID("10000000-0000-4000-8000-000000000001")
ENTITY = UUID("20000000-0000-4000-8000-000000000001")
TRANSACTION = UUID("30000000-0000-4000-8000-000000000001")
DOCUMENT = UUID("40000000-0000-4000-8000-000000000001")
POLICY = UUID("50000000-0000-4000-8000-000000000001")
SNAPSHOT = UUID("60000000-0000-4000-8000-000000000001")


def reference(**overrides):
    values = dict(kind=EvidenceKind.TRANSACTION, record_id=TRANSACTION,
                  record_version=1, tenant_id=TENANT, legal_entity_id=ENTITY)
    values.update(overrides)
    return EvidenceReference(**values)


def test_exact_evidence_kind_vocabulary():
    assert {kind.value for kind in EvidenceKind} == {
        "DOCUMENT_FIELD", "IMPORT_CELL", "TRANSACTION", "PO_LINE", "GRN_LINE",
        "CONTRACT", "POLICY_CLAUSE", "MASTER_RECORD", "APPROVAL", "BUDGET_LEDGER",
        "HISTORICAL_AGGREGATE",
    }


@pytest.mark.parametrize("kind", list(EvidenceKind))
def test_references_do_not_require_document_coordinates(kind):
    locator = ImportCellLocator(SNAPSHOT, "Claims", 7, "amount") if kind is EvidenceKind.IMPORT_CELL else None
    evidence = reference(kind=kind, import_cell=locator)
    assert evidence.record_id == TRANSACTION
    assert evidence.tenant_id == TENANT and evidence.legal_entity_id == ENTITY
    assert evidence.bbox is None and evidence.page is None
    assert evidence.coordinate_system is None


def test_document_field_cites_original_page_and_optional_verified_box():
    bbox = BoundingBox(0.7, 0.8, 0.95, 0.85)
    evidence = reference(kind=EvidenceKind.DOCUMENT_FIELD, record_id=DOCUMENT,
                         document_id=DOCUMENT, page=1, bbox=bbox,
                         field_path="total", observed_value="INR 118,000.00")
    assert evidence.page == 1 and evidence.bbox == bbox
    assert evidence.coordinate_system == "normalized_original_page"


def test_page_only_evidence_does_not_manufacture_box():
    evidence = reference(kind=EvidenceKind.DOCUMENT_FIELD, document_id=DOCUMENT,
                         page=1, bbox=None, field_path="total")
    assert evidence.bbox is None and evidence.coordinate_system is None


@pytest.mark.parametrize("coordinates", [(0, 0, 1, 1), (0, 0, 0, 0), (1, 1, 1, 1), (0.1, 0.2, 0.3, 0.4)])
def test_normalized_boundary_boxes_are_valid(coordinates):
    assert BoundingBox(*coordinates).x1 == coordinates[0]


@pytest.mark.parametrize("coordinates", [
    (-0.01, 0, 1, 1), (0, -0.01, 1, 1), (0, 0, 1.01, 1), (0, 0, 1, 1.01),
    (0.8, 0, 0.2, 1), (0, 0.8, 1, 0.2), (float("nan"), 0, 1, 1),
    (0, 0, float("inf"), 1), (0, 0, 10**1000, 1),
])
def test_out_of_bounds_reversed_or_nonfinite_boxes_are_rejected(coordinates):
    with pytest.raises(ValueError):
        BoundingBox(*coordinates)


@pytest.mark.parametrize("coordinate", [True, None, "0.1", Decimal("0.1")])
def test_coordinates_are_positions_without_scalar_coercion(coordinate):
    with pytest.raises(TypeError, match="numeric coordinate"):
        BoundingBox(coordinate, 0, 1, 1)


@pytest.mark.parametrize("page", [0, -1])
def test_pages_are_one_based(page):
    with pytest.raises(ValueError, match="one-based"):
        reference(document_id=DOCUMENT, page=page)


@pytest.mark.parametrize("page", [True, False, 1.0, "1"])
def test_page_type_is_explicit(page):
    with pytest.raises(TypeError, match="page"):
        reference(document_id=DOCUMENT, page=page)


@pytest.mark.parametrize("locators", [dict(page=1), dict(bbox=BoundingBox(0, 0, 1, 1)), dict(document_id=DOCUMENT, bbox=BoundingBox(0, 0, 1, 1))])
def test_document_locators_cannot_omit_their_context(locators):
    with pytest.raises(ValueError, match="requires"):
        reference(**locators)


@pytest.mark.parametrize("field", ["record_id", "tenant_id", "legal_entity_id", "document_id", "snapshot_id"])
@pytest.mark.parametrize("invalid", ["INV-101", "10000000-0000-4000-8000-000000000001", True])
def test_ids_must_already_be_uuid_values(field, invalid):
    with pytest.raises(TypeError, match=field):
        reference(**{field: invalid})


@pytest.mark.parametrize("field", ["record_id", "tenant_id", "legal_entity_id", "document_id", "snapshot_id"])
def test_nil_id_is_not_a_missing_record_placeholder(field):
    with pytest.raises(ValueError, match="nil UUID"):
        reference(**{field: UUID(int=0)})


@pytest.mark.parametrize("version", [1, 2, "v1", "rules-2026-09"])
def test_numeric_and_text_record_versions_are_preserved(version):
    assert reference(record_version=version).record_version == version


@pytest.mark.parametrize("version", [0, -1, "", " "])
def test_empty_or_nonpositive_versions_are_rejected(version):
    with pytest.raises(ValueError):
        reference(record_version=version)


@pytest.mark.parametrize("version", [True, None, 1.0])
def test_versions_are_not_silently_coerced(version):
    with pytest.raises(TypeError):
        reference(record_version=version)


def test_missing_approval_cites_real_context_without_approval_id():
    current = reference(field_path="approvals", snapshot_id=SNAPSHOT,
                        observed_value="Required approval absent in the searched snapshot")
    requirement = reference(kind=EvidenceKind.POLICY_CLAUSE, record_id=POLICY,
                            record_version="v1", field_path="manager_approval")
    assert current.record_id == TRANSACTION and current.snapshot_id == SNAPSHOT
    assert requirement.record_id == POLICY
    assert all(item.kind is not EvidenceKind.APPROVAL for item in (current, requirement))


@pytest.mark.parametrize("representation", [None, "0", "false", "UNKNOWN", "[redacted]"])
def test_optional_observation_does_not_guess_a_value(representation):
    assert reference(observed_value=representation).observed_value is representation


@pytest.mark.parametrize("representation", [False, 0, Decimal("0"), [], {}])
def test_observation_requires_explicit_text(representation):
    with pytest.raises(TypeError, match="observed_value"):
        reference(observed_value=representation)


@pytest.mark.parametrize("invalid", ["", " ", False])
def test_field_path_cannot_be_blank_or_boolean(invalid):
    with pytest.raises((TypeError, ValueError)):
        reference(field_path=invalid)


def test_import_cell_retains_full_source_locator():
    cell = ImportCellLocator(SNAPSHOT, "Claims", 7, "amount")
    evidence = reference(kind=EvidenceKind.IMPORT_CELL, import_cell=cell)
    assert (cell.batch_id, cell.sheet, cell.row, cell.column) == (SNAPSHOT, "Claims", 7, "amount")
    assert evidence.import_cell == cell


@pytest.mark.parametrize("values", [dict(row=0), dict(row=True), dict(sheet=" "), dict(column=""), dict(batch_id="batch-1")])
def test_import_locator_is_validated(values):
    args = dict(batch_id=SNAPSHOT, sheet="Claims", row=7, column="amount")
    args.update(values)
    with pytest.raises((TypeError, ValueError)):
        ImportCellLocator(**args)


def test_import_evidence_cannot_omit_provenance():
    with pytest.raises(ValueError, match="batch, sheet, row, and column"):
        reference(kind=EvidenceKind.IMPORT_CELL)


@pytest.mark.parametrize("values", [dict(kind="TRANSACTION"), dict(bbox=[0, 0, 1, 1]), dict(import_cell={"row": 7})])
def test_nested_evidence_contracts_are_typed(values):
    with pytest.raises(TypeError):
        reference(**values)


@pytest.mark.parametrize("value,field,replacement", [
    (BoundingBox(0, 0, 1, 1), "x1", 0.5),
    (reference(), "record_id", POLICY),
    (ImportCellLocator(SNAPSHOT, "Claims", 7, "amount"), "row", 8),
])
def test_evidence_value_objects_are_immutable(value, field, replacement):
    with pytest.raises(FrozenInstanceError):
        setattr(value, field, replacement)
