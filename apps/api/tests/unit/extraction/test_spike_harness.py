from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
import shutil

import pytest

from app.domain.extraction import (
    AdapterCapabilities, ExtractionObservationState as State, ExtractionStatus,
)
from app.domain.states import ScreeningDecision
from app.extraction.spike import CRITICAL_FIELDS, load_dataset, load_fixture_adapter, read_json, run_spike


class ChangedAdapter:
    """A provider-shaped test double; mutate exactly one actual response."""

    def __init__(self, fixture, case_id, change, capabilities=None):
        self.fixture = fixture
        self.metadata = fixture.metadata
        self.capabilities = capabilities if capabilities is not None else fixture.capabilities
        self.case_id = case_id
        self.change = change

    def extract(self, document_bundle, schema_version):
        result = self.fixture.extract(document_bundle, schema_version)
        return self.change(result) if document_bundle.document_id == self.case_id else result


def change_header(result, name, **changes):
    return replace(result, header_fields=tuple(replace(f, **changes) if f.field_path == name else f for f in result.header_fields))


def test_all_cases_and_independent_critical_metrics(dataset, adapter):
    report = run_spike(dataset, adapter)
    aggregate = report["aggregate"]
    assert len(report["cases"]) == 10
    assert aggregate["documents_attempted"] == aggregate["extractions_completed"] == 10
    assert aggregate["failed_or_unsupported"] == 0
    assert aggregate["status_counts"]["COMPLETED"] == 10
    assert set(aggregate["critical_fields"]) == set(CRITICAL_FIELDS)
    for metrics in aggregate["critical_fields"].values():
        assert metrics["observation_exact"] == dict(matched=10, expected=10, ratio="1")
    assert aggregate["state_correct"] == dict(matched=130, expected=130, ratio="1")
    assert aggregate["abstention_correct"] == dict(matched=7, expected=7, ratio="1")
    assert aggregate["row_coverage"] == dict(matched=12, expected=12, ratio="1")
    assert aggregate["row_fields_exact"] == dict(matched=48, expected=48, ratio="1")
    assert aggregate["unexpected_rows"] == 0
    assert report["execution_timestamp"] is None
    assert report["adapter"]["model_id"] is None
    assert report["dataset_version"] == "extraction-spike-v1"
    assert report["schema_version"] == "extraction-v1"
    assert report["manifest_digest"] == dataset.manifest_digest


def test_deterministic_comparison_and_decimal_context(dataset, adapter):
    first = json.dumps(run_spike(dataset, adapter), sort_keys=True)
    with localcontext() as ctx:
        ctx.prec = 2
        assert json.dumps(run_spike(dataset, adapter), sort_keys=True) == first


@pytest.mark.parametrize("name", CRITICAL_FIELDS)
def test_wrong_critical_value_is_detected_independently(name, dataset, adapter):
    wrong = ChangedAdapter(adapter, dataset.cases[0].bundle.document_id, lambda r: change_header(r, name, raw_value="wrong"))
    metrics = run_spike(dataset, wrong)["aggregate"]["critical_fields"]
    assert metrics[name]["raw_exact"] == dict(matched=9, expected=10, ratio="0.9")
    assert metrics[name]["observation_exact"]["matched"] == 9
    for other in CRITICAL_FIELDS:
        if other != name:
            assert metrics[other]["observation_exact"]["matched"] == 10


@pytest.mark.parametrize("index,name,raw,candidate", [
    (3, "total", "600.00", "600.00"),
    (8, "total", "1180.00", "1180.00"),
    (5, "document_date", "03/04/2026", "2026-04-03"),
    (7, "po_reference", "DEMO-PO", "DEMO-PO"),
])
def test_guessed_uncertain_value_counts_as_wrong(index, name, raw, candidate, dataset, adapter):
    guessed = ChangedAdapter(adapter, dataset.cases[index].bundle.document_id,
        lambda r: change_header(r, name, state=State.PRESENT, raw_value=raw, parsed_candidate=candidate))
    report = run_spike(dataset, guessed)
    assert report["aggregate"]["abstention_correct"] == dict(matched=6, expected=7, ratio="0.8571428571428571428571428571")
    assert report["cases"][index]["comparisons"][f"header.{name}"]["state_correct"] is False


def test_absent_observation_is_not_correct_explicit_missing(dataset, adapter):
    wrong = ChangedAdapter(adapter, dataset.cases[7].bundle.document_id,
        lambda r: replace(r, header_fields=tuple(f for f in r.header_fields if f.field_path != "po_reference")))
    report = run_spike(dataset, wrong)
    assert report["cases"][7]["comparisons"]["header.po_reference"]["observation_exact"] is False
    assert report["aggregate"]["abstention_correct"]["matched"] == 6


def test_missing_rows_and_wrong_item_values(dataset, adapter):
    wrong = ChangedAdapter(adapter, dataset.cases[1].bundle.document_id,
        lambda r: replace(r, line_items=r.line_items[:1]))
    report = run_spike(dataset, wrong)
    assert report["cases"][1]["missing_rows"] == [2, 3]
    assert report["cases"][1]["expected_rows"] == 3
    assert report["cases"][1]["observed_rows"] == 1
    assert report["aggregate"]["row_coverage"]["matched"] == 10
    assert report["aggregate"]["row_fields_exact"]["matched"] == 40
    wrong = ChangedAdapter(adapter, dataset.cases[1].bundle.document_id,
        lambda r: replace(r, line_items=(replace(r.line_items[0], fields=tuple(
            replace(f, raw_value="9999.00", parsed_candidate="9999.00") if f.field_path == "amount" else f
            for f in r.line_items[0].fields)),) + r.line_items[1:]))
    report = run_spike(dataset, wrong)
    assert report["aggregate"]["row_fields_exact"]["matched"] == 47
    assert report["aggregate"]["row_coverage"]["matched"] == 12


def test_extra_rows_are_not_hidden_by_full_coverage(dataset, adapter):
    wrong = ChangedAdapter(adapter, dataset.cases[0].bundle.document_id,
        lambda r: replace(r, line_items=r.line_items + (replace(r.line_items[0], row_index=2),)))
    report = run_spike(dataset, wrong)
    assert report["aggregate"]["row_coverage"]["ratio"] == "1"
    assert report["aggregate"]["unexpected_rows"] == 1
    assert report["cases"][0]["unexpected_rows"] == [2]


def test_unavailable_metrics_are_null_not_perfect(dataset, adapter):
    report = run_spike(dataset, adapter)
    aggregate = report["aggregate"]
    assert aggregate["bbox_availability"] == dict(available=0, expected=130, ratio=None)
    assert aggregate["adapter_latency_ms"] == dict(available_count=0, document_count=10, minimum=None, maximum=None, mean=None)
    assert aggregate["critical_fields"]["party_name"]["parsed_candidate_exact"] == dict(matched=0, expected=0, ratio=None)
    assert aggregate["critical_fields"]["currency"]["abstention_correct"] == dict(matched=0, expected=0, ratio=None)
    assert report["unsupported_capabilities"] == ["bounding_boxes", "visual_input"]
    assert aggregate["page_locator_availability"] == dict(available=130, expected=130, ratio="1")


def test_unsupported_and_partly_missing_page_locators(dataset, adapter):
    def no_sources(result):
        return replace(result, header_fields=tuple(replace(f, source=None) for f in result.header_fields),
            line_items=tuple(replace(row, fields=tuple(replace(f, source=None) for f in row.fields)) for row in result.line_items))
    class NoLocatorAdapter(ChangedAdapter):
        def extract(self, document_bundle, schema_version):
            return no_sources(self.fixture.extract(document_bundle, schema_version))
    changed = NoLocatorAdapter(adapter, None, None, AdapterCapabilities(False, False, True, False))
    report = run_spike(dataset, changed)
    assert report["aggregate"]["page_locator_availability"] == dict(available=0, expected=130, ratio=None)
    assert "page_locators" in report["unsupported_capabilities"]
    changed = ChangedAdapter(adapter, dataset.cases[0].bundle.document_id, no_sources)
    report = run_spike(dataset, changed)
    assert report["aggregate"]["page_locator_availability"]["available"] == 117
    assert report["aggregate"]["page_locator_availability"]["ratio"] == "0.9"


@pytest.mark.parametrize("status", [ExtractionStatus.FAILED, ExtractionStatus.UNSUPPORTED, ExtractionStatus.PARTIAL])
def test_status_and_missing_results_are_explicit(status, dataset, adapter):
    changed = ChangedAdapter(adapter, dataset.cases[0].bundle.document_id,
        lambda r: replace(r, status=status, header_fields=(), line_items=(), failure_code="TEST_CODE"))
    report = run_spike(dataset, changed)
    assert report["aggregate"]["extractions_completed"] == 9
    assert report["aggregate"]["status_counts"][status.value] == 1
    assert report["cases"][0]["failure_code"] == "TEST_CODE"
    assert report["aggregate"]["critical_fields"]["total"]["observation_exact"]["matched"] == 9
    assert report["aggregate"]["failed_or_unsupported"] == int(status is not ExtractionStatus.PARTIAL)


def test_exception_is_counted_without_logging_private_message(dataset, adapter):
    def timeout(result):
        raise TimeoutError("secret-provider-message must not appear")
    changed = ChangedAdapter(adapter, dataset.cases[0].bundle.document_id, timeout)
    report = run_spike(dataset, changed)
    assert report["aggregate"]["failed_or_unsupported"] == 1
    assert report["cases"][0]["failure_code"] == "TimeoutError"
    assert "secret-provider-message" not in json.dumps(report)


@pytest.mark.parametrize("kind", ["finance_result", "metadata_mismatch", "undeclared_locator"])
def test_bad_adapter_response_counts_as_error(kind, dataset, adapter):
    def invalid(result):
        if kind == "finance_result":
            return ScreeningDecision.PASS
        if kind == "metadata_mismatch":
            return replace(result, metadata=replace(result.metadata, adapter_version="wrong"))
        return result
    capabilities = AdapterCapabilities(False, False, True, False) if kind == "undeclared_locator" else None
    changed = ChangedAdapter(adapter, dataset.cases[0].bundle.document_id, invalid, capabilities)
    report = run_spike(dataset, changed)
    assert report["cases"][0]["extraction_status"] == "ADAPTER_ERROR"
    assert report["aggregate"]["critical_fields"]["total"]["observation_exact"]["matched"] == (0 if kind == "undeclared_locator" else 9)


def test_optional_latency_and_timestamp(dataset, adapter):
    changed = ChangedAdapter(adapter, dataset.cases[0].bundle.document_id, lambda r: replace(r, elapsed_ms=Decimal("12.50")))
    report = run_spike(dataset, changed, execution_timestamp=datetime(2026, 10, 2, tzinfo=timezone.utc))
    assert report["execution_timestamp"] == "2026-10-02T00:00:00+00:00"
    assert report["aggregate"]["adapter_latency_ms"] == dict(available_count=1, document_count=10, minimum="12.50", maximum="12.50", mean="12.50")
    with pytest.raises(ValueError):
        run_spike(dataset, adapter, execution_timestamp=datetime(2026, 10, 2))


def test_no_expected_rows_yields_no_row_score(dataset, adapter):
    class NoRowsAdapter(ChangedAdapter):
        def extract(self, document_bundle, schema_version):
            return replace(self.fixture.extract(document_bundle, schema_version), line_items=())
    no_rows = replace(dataset, cases=tuple(replace(c, expected_rows=()) for c in dataset.cases))
    report = run_spike(no_rows, NoRowsAdapter(adapter, None, None))
    assert report["aggregate"]["row_coverage"] == dict(matched=0, expected=0, ratio=None)
    assert report["aggregate"]["row_fields_exact"] == dict(matched=0, expected=0, ratio=None)


def test_structured_variations_and_checksum_scope(dataset, dataset_dir):
    assert len(dataset.cases) == len({c.variation for c in dataset.cases}) == 10
    assert len(dataset.cases[1].bundle.pages) == 2
    assert len(dataset.cases[1].expected_rows) == 3
    assert dataset.cases[4].bundle.pages[0].declared_rotation_degrees == 90
    assert {f.state for c in dataset.cases for f in c.expected_fields} == set(State)
    assert all(c.bundle.synthetic and c.bundle.source_artifact_ref is None for c in dataset.cases)
    assert all(p.artifact_ref is None for c in dataset.cases for p in c.bundle.pages)
    root = dataset_dir.parents[1]
    pinned = {}
    for line in (dataset_dir / "fixtures.sha256").read_text().splitlines():
        digest, path = line.split("  ", 1)
        assert path.startswith("data/extraction_spike/")
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest
        pinned[path] = digest
    assert len(pinned) == 11
    assert set(pinned) == {p.relative_to(root).as_posix() for p in dataset_dir.rglob("*.json")}
    assert load_dataset(dataset_dir) == dataset


@pytest.mark.parametrize("mutation", ["finance_state", "numeric_amount", "no_critical", "duplicate_case", "unsafe_path", "digest_mismatch", "wrong_scope"])
def test_malformed_dataset_or_response_is_rejected(mutation, dataset_dir, tmp_path):
    directory = tmp_path / "dataset"
    shutil.copytree(dataset_dir, directory)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    case = manifest["cases"][0]
    if mutation == "finance_state":
        case["expected_fields"][0]["state"] = "PASS"
    elif mutation == "numeric_amount":
        case["expected_fields"][0]["parsed_candidate"] = 1.25
    elif mutation == "no_critical":
        case["expected_fields"] = [f for f in case["expected_fields"] if f["field_path"] != "total"]
    elif mutation == "duplicate_case":
        manifest["cases"].append(case)
    elif mutation == "unsafe_path":
        case["response_path"] = "../other.json"
    else:
        response_path = directory / case["response_path"]
        response = json.loads(response_path.read_text())
        if mutation == "digest_mismatch":
            response["input_digest"] = "0" * 64
        else:
            response["result"]["document_version"] = 2
        response_path.write_text(json.dumps(response))
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises((ValueError, TypeError)):
        loaded = load_dataset(directory)
        load_fixture_adapter(directory, loaded)


@pytest.mark.parametrize("text", ['{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}'])
def test_duplicate_keys_and_nonfinite_json_are_rejected(text, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        read_json(path)
