from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from uuid import UUID

import pytest

from app.domain.evidence import BoundingBox, EvidenceKind
from app.domain.extraction import (
    AdapterCapabilities, AdapterMetadata, DocumentPage, DocumentSourceType,
    ExtractionObservationState as State, ExtractionStatus, FieldObservation,
    LineItemObservation, VersionMetadata, bundle_from_data, observation_from_data,
    result_from_data, row_from_data, to_data,
)
from app.domain.states import RuleStatus, ScreeningDecision
from app.extraction.base import ExtractionAdapter


def test_protocol_and_round_trip(dataset, adapter, result):
    assert isinstance(adapter, ExtractionAdapter)
    assert bundle_from_data(to_data(dataset.cases[0].bundle)) == dataset.cases[0].bundle
    assert result_from_data(to_data(result)) == result
    result.validate_binding(dataset.cases[0].bundle, dataset.schema_version)


@pytest.mark.parametrize("target,attribute,value", [
    ("result", "schema_version", "other"),
    ("metadata", "provider_id", "other"),
    ("field", "raw_value", "other"),
    ("row", "row_index", 2),
    ("bundle", "document_version", 2),
    ("page", "available_text", "other"),
    ("source", "page", 2),
])
def test_nested_immutability(target, attribute, value, dataset, result):
    objects = dict(result=result, metadata=result.metadata, field=result.header_fields[0],
        row=result.line_items[0], bundle=dataset.cases[0].bundle,
        page=dataset.cases[0].bundle.pages[0], source=result.header_fields[0].source)
    with pytest.raises(FrozenInstanceError):
        setattr(objects[target], attribute, value)


@pytest.mark.parametrize("state,raw", [
    (State.PRESENT, "1180.00"), (State.MISSING, None),
    (State.ILLEGIBLE, "[obscured]"), (State.AMBIGUOUS, "03/04/2026"),
    (State.NOT_APPLICABLE, None),
])
def test_explicit_states_and_optional_quality(state, raw):
    observation = FieldObservation("total", state, raw)
    assert observation.state is state
    assert observation.parsed_candidate is None
    assert observation.source is None and observation.bbox is None and observation.page is None
    assert observation.diagnostic_note is None
    assert "confidence" not in {f.name for f in fields(observation)}
    with pytest.raises(TypeError):
        bool(state)


@pytest.mark.parametrize("state", [State.MISSING, State.ILLEGIBLE, State.AMBIGUOUS, State.NOT_APPLICABLE])
def test_uncertainty_rejects_guessed_candidates(state):
    with pytest.raises(ValueError):
        FieldObservation("total", state, None if state is State.MISSING else "unclear", "0")


@pytest.mark.parametrize("state", ["PRESENT", "PASS", None, RuleStatus.UNKNOWN, ScreeningDecision.PASS])
def test_invalid_or_financial_observation_states(state):
    with pytest.raises(TypeError):
        FieldObservation("total", state, "0")


@pytest.mark.parametrize("changes", [
    dict(state=State.PRESENT, raw_value=None),
    dict(state=State.AMBIGUOUS, raw_value=None),
    dict(state=State.MISSING, raw_value="0"),
    dict(raw_value=0), dict(parsed_candidate=1.2), dict(parsed_candidate=False),
    dict(diagnostic_note=0.99), dict(field_path="lines[0].total"),
    dict(field_path="decision"), dict(field_path="vendor_approved"),
])
def test_invalid_observation_values(changes):
    values = dict(field_path="total", state=State.PRESENT, raw_value="0")
    values.update(changes)
    with pytest.raises((TypeError, ValueError)):
        FieldObservation(**values)


def test_raw_candidate_distinction(result):
    total = next(f for f in result.header_fields if f.field_path == "total")
    assert total.raw_value == "INR 1,18,000.00"
    assert total.parsed_candidate == "118000.00"
    assert total.source.observed_value == total.raw_value
    assert isinstance(total.parsed_candidate, str)


@pytest.mark.parametrize("changes", [
    dict(adapter_id=""), dict(adapter_version=" "), dict(provider_id=None),
    dict(model_id=""), dict(prompt_template_version=""),
    dict(runtime_versions=[VersionMetadata("python", "3.13.11")]),
    dict(runtime_versions=(VersionMetadata("python", "3.13.11"), VersionMetadata("python", "other"))),
])
def test_required_version_metadata(changes, result):
    with pytest.raises((TypeError, ValueError)):
        replace(result.metadata, **changes)


def test_optional_real_runtime_metadata(result):
    metadata = AdapterMetadata("future", "v1", "local", model_id="model@revision",
        prompt_template_version="template-v1", runtime_versions=(VersionMetadata("python", "3.13.11"),))
    changed = replace(result, metadata=metadata, elapsed_ms=Decimal("12.50"), raw_artifact_ref="local:response.json")
    assert result_from_data(to_data(changed)) == changed
    assert to_data(changed)["elapsed_ms"] == "12.50"


@pytest.mark.parametrize("changes", [
    dict(run_id="43000000-0000-0000-0000-000000000001"), dict(run_id=UUID(int=0)),
    dict(document_version=0), dict(document_version=True), dict(schema_version=""),
    dict(metadata=None), dict(header_fields=[]), dict(line_items=[]),
    dict(elapsed_ms=1.2), dict(elapsed_ms=Decimal("NaN")),
    dict(elapsed_ms=Decimal("-1")), dict(status=ScreeningDecision.PASS),
    dict(status=RuleStatus.PASS), dict(status="COMPLETED"),
    dict(status=ExtractionStatus.FAILED), dict(status=ExtractionStatus.UNSUPPORTED),
])
def test_result_invalid_metadata_or_financial_status(changes, result):
    with pytest.raises((TypeError, ValueError)):
        replace(result, **changes)


@pytest.mark.parametrize("status", list(ExtractionStatus))
def test_extraction_status_is_separate(status, result):
    changed = replace(result, status=status, failure_code="TEST_FAILURE" if status in {ExtractionStatus.FAILED, ExtractionStatus.UNSUPPORTED} else None)
    assert changed.status not in set(ScreeningDecision)
    assert changed.status not in set(RuleStatus)
    with pytest.raises(TypeError):
        bool(changed.status)


def test_page_only_and_existing_bbox(result):
    observed = result.header_fields[0]
    assert observed.source.kind is EvidenceKind.DOCUMENT_FIELD
    assert observed.page == 1 and observed.bbox is None
    assert observed.source.coordinate_system is None
    box = BoundingBox(0.1, 0.2, 0.8, 0.4)
    with_box = replace(observed, source=replace(observed.source, bbox=box))
    assert with_box.bbox is box
    assert with_box.source.coordinate_system == "normalized_original_page"
    assert observation_from_data(to_data(with_box)) == with_box
    with pytest.raises(ValueError):
        replace(observed.source, page=0)
    with pytest.raises(ValueError):
        BoundingBox(0, 0, 2, 1)


@pytest.mark.parametrize("source_changes", [
    dict(record_version=2), dict(tenant_id=UUID(int=12)),
    dict(legal_entity_id=UUID(int=13)),
])
def test_observation_scope_must_bind_result(source_changes, result):
    observed = result.header_fields[0]
    changed = replace(observed, source=replace(observed.source, **source_changes))
    with pytest.raises(ValueError):
        replace(result, header_fields=(changed,) + result.header_fields[1:])


def test_page_must_exist_in_input(result, dataset):
    observed = result.header_fields[0]
    changed = replace(observed, source=replace(observed.source, page=2))
    result = replace(result, header_fields=(changed,) + result.header_fields[1:])
    with pytest.raises(ValueError, match="page"):
        result.validate_binding(dataset.cases[0].bundle, dataset.schema_version)


@pytest.mark.parametrize("changes", [
    dict(pages=[]), dict(pages=()), dict(pages=(DocumentPage(1), DocumentPage(1))),
    dict(pages=(DocumentPage(2), DocumentPage(1))), dict(document_version=0),
    dict(source_type="VENDOR_INVOICE"), dict(synthetic="true"),
])
def test_document_input_rejects_invalid_structure(changes, dataset):
    with pytest.raises((TypeError, ValueError)):
        replace(dataset.cases[0].bundle, **changes)


def test_no_file_access_required_for_future_artifact_slots(dataset):
    bundle = replace(dataset.cases[0].bundle,
        source_artifact_ref="future:original.pdf", source_type=DocumentSourceType.VENDOR_INVOICE,
        pages=(DocumentPage(1, artifact_ref="future:page.png", declared_rotation_degrees=90),))
    assert bundle.pages[0].available_text is None
    assert bundle_from_data(to_data(bundle)) == bundle


def test_bounded_flat_rows_and_headers(result):
    field = result.header_fields[0]
    with pytest.raises(ValueError):
        replace(result, header_fields=(field, field))
    with pytest.raises(ValueError):
        replace(result, header_fields=tuple(replace(field, field_path=f"field_{i}") for i in range(65)))
    with pytest.raises(ValueError):
        LineItemObservation(1, tuple(replace(field, field_path=f"field_{i}") for i in range(17)))
    with pytest.raises(ValueError):
        LineItemObservation(201, (field,))
    with pytest.raises(TypeError):
        LineItemObservation(1, (result.line_items[0],))


def test_wire_contract_rejects_extra_decision_and_numeric_candidate(result):
    data = to_data(result)
    data["decision"] = "PASS"
    with pytest.raises(TypeError):
        result_from_data(data)
    data = to_data(result)
    data["header_fields"][0]["parsed_candidate"] = 118000.0
    with pytest.raises(TypeError):
        result_from_data(data)
    row = to_data(result.line_items[0])
    row["decision"] = "PASS"
    with pytest.raises(TypeError):
        row_from_data(row)


def test_capabilities_are_explicit():
    with pytest.raises(TypeError):
        AdapterCapabilities("yes", False, True, False)
    with pytest.raises(ValueError):
        AdapterCapabilities(False, True, True, False)
