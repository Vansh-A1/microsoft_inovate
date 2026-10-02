"""Structured synthetic dataset loader and provider-independent comparison.

This measures agreement with annotated observations, not finance eligibility or
visual/model accuracy. Fixture responses and expected observations are separate.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

from app.domain.extraction import (
    AdapterCapabilities, AdapterMetadata, DocumentBundle, ExtractionObservationState,
    ExtractionResult, ExtractionStatus, FieldObservation, LineItemObservation,
    SCHEMA_VERSION, bundle_from_data, observation_from_data, result_from_data,
    row_from_data, to_data,
)
from app.extraction.base import ExtractionAdapter
from app.extraction.fixture import FixtureExtractionAdapter, FixtureResponse


CRITICAL_FIELDS = ("total", "currency", "document_number", "document_date", "party_name")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _no_constant(value):
    raise ValueError(f"nonfinite JSON constant: {value}")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json, parse_constant=_no_constant)


@dataclass(frozen=True, slots=True)
class SpikeCase:
    case_id: str
    variation: str
    bundle: DocumentBundle
    expected_fields: tuple[FieldObservation, ...]
    expected_rows: tuple[LineItemObservation, ...]
    response_path: str

    def __post_init__(self):
        _require(isinstance(self.case_id, str) and bool(self.case_id.strip()), "case_id required")
        _require(isinstance(self.variation, str) and bool(self.variation.strip()), "variation required")
        _require(isinstance(self.bundle, DocumentBundle) and self.bundle.synthetic, "spike inputs must be synthetic DocumentBundle")
        _require(isinstance(self.expected_fields, tuple) and all(isinstance(f, FieldObservation) for f in self.expected_fields), "expected_fields must be typed tuple")
        _require(isinstance(self.expected_rows, tuple) and all(isinstance(r, LineItemObservation) for r in self.expected_rows), "expected_rows must be typed tuple")
        names = [f.field_path for f in self.expected_fields]
        _require(len(names) == len(set(names)) and set(CRITICAL_FIELDS) <= set(names), "unique ground truth with all critical fields required")
        indices = [r.row_index for r in self.expected_rows]
        _require(indices == list(range(1, len(indices) + 1)), "ground-truth rows must be contiguous and ordered")


@dataclass(frozen=True, slots=True)
class SpikeDataset:
    version: str
    schema_version: str
    manifest_digest: str
    cases: tuple[SpikeCase, ...]

    def __post_init__(self):
        _require(isinstance(self.version, str) and bool(self.version.strip()), "dataset version required")
        _require(self.schema_version == SCHEMA_VERSION, "unsupported spike schema")
        _require(isinstance(self.manifest_digest, str) and len(self.manifest_digest) == 64 and all(c in "0123456789abcdef" for c in self.manifest_digest), "manifest SHA-256 required")
        _require(isinstance(self.cases, tuple) and bool(self.cases) and all(isinstance(c, SpikeCase) for c in self.cases), "typed cases required")
        _require(len({c.case_id for c in self.cases}) == len(self.cases), "duplicate spike case_id")
        _require(len({(c.bundle.document_id, c.bundle.document_version) for c in self.cases}) == len(self.cases), "duplicate document revision")


def load_dataset(directory: Path) -> SpikeDataset:
    manifest = read_json(directory / "manifest.json")
    _require(manifest["synthetic"] is True, "manifest must declare synthetic data")
    _require(manifest["artifact_status"] == "STRUCTURED_ONLY_NO_VISUAL_ARTIFACTS", "visual testing must not be implied")
    _require(manifest["critical_fields"] == list(CRITICAL_FIELDS), "critical field catalog mismatch")
    cases = []
    for item in manifest["cases"]:
        _require(item["synthetic"] is True, "case must declare synthetic data")
        cases.append(SpikeCase(case_id=item["case_id"], variation=item["variation"],
            bundle=bundle_from_data(item["document_bundle"]),
            expected_fields=tuple(observation_from_data(f) for f in item["expected_fields"]),
            expected_rows=tuple(row_from_data(r) for r in item["expected_rows"]), response_path=item["response_path"]))
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return SpikeDataset(manifest["dataset_version"], manifest["schema_version"], digest, tuple(cases))


def load_fixture_adapter(directory: Path, dataset: SpikeDataset) -> FixtureExtractionAdapter:
    responses, paths = [], set()
    for case in dataset.cases:
        path = Path(case.response_path)
        _require(len(path.parts) == 2 and path.parent.as_posix() == "responses" and path.suffix == ".json", "unexpected/unsafe response path")
        absolute = (directory / path).resolve()
        _require(absolute.parent == (directory / "responses").resolve(), "response path escapes dataset")
        _require(path.as_posix() not in paths, "duplicate response path")
        paths.add(path.as_posix())
        payload = read_json(absolute)
        _require(payload["synthetic"] is True, "fixture response must be synthetic")
        _require(payload["input_digest"] == case.bundle.digest(), "fixture input digest mismatch")
        result = result_from_data(payload["result"])
        result.validate_binding(case.bundle, dataset.schema_version)
        responses.append(FixtureResponse(payload["input_digest"], result))
    _require({p.name for p in (directory / "responses").glob("*.json")} == {Path(p).name for p in paths}, "unlisted/missing response file")
    return FixtureExtractionAdapter(tuple(responses))


def _ratio(matched, expected):
    if expected == 0:
        return None
    with localcontext() as ctx:
        ctx.prec = 28
        return format(Decimal(matched) / Decimal(expected), "f")


def _metric(matched, expected):
    return {"matched": matched, "expected": expected, "ratio": _ratio(matched, expected)}


def _compare(expected, actual):
    state = actual is not None and actual.state is expected.state
    raw = actual is not None and actual.raw_value == expected.raw_value
    candidate = actual is not None and actual.parsed_candidate == expected.parsed_candidate
    return {"state_correct": state, "raw_exact": raw, "candidate_exact": candidate,
            "observation_exact": state and raw and candidate}


def _observation_pairs(case, result):
    headers = {f.field_path: f for f in result.header_fields} if result is not None else {}
    rows = {r.row_index: r for r in result.line_items} if result is not None else {}
    pairs = [(f"header.{f.field_path}", f, headers.get(f.field_path)) for f in case.expected_fields]
    for row in case.expected_rows:
        actual = {f.field_path: f for f in rows[row.row_index].fields} if row.row_index in rows else {}
        pairs.extend((f"rows.{row.row_index}.{f.field_path}", f, actual.get(f.field_path)) for f in row.fields)
    return pairs


def run_spike(dataset: SpikeDataset, adapter: ExtractionAdapter, *, execution_timestamp: datetime | None = None) -> dict:
    if not isinstance(dataset, SpikeDataset) or not isinstance(adapter, ExtractionAdapter):
        raise TypeError("run_spike requires SpikeDataset and ExtractionAdapter")
    if not isinstance(adapter.metadata, AdapterMetadata) or not isinstance(adapter.capabilities, AdapterCapabilities):
        raise TypeError("adapter metadata/capabilities must use contract types")
    if execution_timestamp is not None and (not isinstance(execution_timestamp, datetime) or execution_timestamp.tzinfo is None or execution_timestamp.utcoffset() is None):
        raise ValueError("execution_timestamp must be timezone-aware or None")
    case_reports, latencies = [], []
    totals = {field: dict(state=0, raw=0, exact=0, candidate=0, candidate_expected=0, abstention=0, abstention_expected=0) for field in CRITICAL_FIELDS}
    states_ok = abstained_ok = abstentions = expected_observations = 0
    rows_present = row_count = row_fields_ok = row_fields_expected = unexpected_rows = 0
    page_locations = boxes = completed = 0
    for case in dataset.cases:
        result, error = None, None
        try:
            candidate = adapter.extract(case.bundle, dataset.schema_version)
            if not isinstance(candidate, ExtractionResult):
                raise TypeError("adapter returned a non-extraction result")
            candidate.validate_binding(case.bundle, dataset.schema_version)
            if candidate.metadata != adapter.metadata:
                raise ValueError("adapter/result metadata mismatch")
            if not adapter.capabilities.page_locators and any(f.page is not None for f in candidate.observations()):
                raise ValueError("undeclared page locator capability")
            if not adapter.capabilities.bounding_boxes and any(f.bbox is not None for f in candidate.observations()):
                raise ValueError("undeclared bbox capability")
            if not adapter.capabilities.line_items and candidate.line_items:
                raise ValueError("undeclared line-item capability")
            result = candidate
        except Exception as exc:
            # Exception class only: provider messages may contain secrets/raw traces.
            error = type(exc).__name__
        if result is not None:
            completed += int(result.status is ExtractionStatus.COMPLETED)
            if result.elapsed_ms is not None:
                latencies.append(result.elapsed_ms)
        pairs = _observation_pairs(case, result)
        comparisons = {path: _compare(expected, actual) for path, expected, actual in pairs}
        for path, expected, actual in pairs:
            matched = comparisons[path]
            states_ok += int(matched["state_correct"])
            expected_observations += 1
            if expected.state is not ExtractionObservationState.PRESENT:
                abstentions += 1
                abstained_ok += int(matched["state_correct"] and actual is not None and actual.parsed_candidate is None)
            page_locations += int(actual is not None and actual.page is not None)
            boxes += int(actual is not None and actual.bbox is not None)
        expected_headers = {f.field_path: f for f in case.expected_fields}
        for name in CRITICAL_FIELDS:
            match = comparisons[f"header.{name}"]
            total = totals[name]
            total["state"] += int(match["state_correct"])
            total["raw"] += int(match["raw_exact"])
            total["exact"] += int(match["observation_exact"])
            expected = expected_headers[name]
            if expected.parsed_candidate is not None:
                total["candidate_expected"] += 1
                total["candidate"] += int(match["candidate_exact"] and match["state_correct"])
            if expected.state is not ExtractionObservationState.PRESENT:
                total["abstention_expected"] += 1
                total["abstention"] += int(match["state_correct"])
        expected_indices = {r.row_index for r in case.expected_rows}
        actual_indices = {r.row_index for r in result.line_items} if result is not None else set()
        row_count += len(expected_indices)
        rows_present += len(expected_indices & actual_indices)
        extra = len(actual_indices - expected_indices)
        unexpected_rows += extra
        row_matches = [match for path, match in comparisons.items() if path.startswith("rows.")]
        row_fields_expected += len(row_matches)
        row_fields_ok += sum(int(m["observation_exact"]) for m in row_matches)
        case_reports.append(dict(case_id=case.case_id, document_id=str(case.bundle.document_id),
            extraction_status=result.status.value if result is not None else "ADAPTER_ERROR",
            failure_code=result.failure_code if result is not None else error,
            run_id=str(result.run_id) if result is not None else None,
            adapter_elapsed_ms=to_data(result.elapsed_ms) if result is not None else None,
            comparisons=comparisons, expected_rows=len(expected_indices), observed_rows=len(actual_indices),
            missing_rows=sorted(expected_indices - actual_indices), unexpected_rows=sorted(actual_indices - expected_indices),
            metadata=to_data(result.metadata) if result is not None else None,
            raw_artifact_ref=result.raw_artifact_ref if result is not None else None))
    critical = {name: dict(state_correct=_metric(t["state"], len(dataset.cases)), raw_exact=_metric(t["raw"], len(dataset.cases)),
        observation_exact=_metric(t["exact"], len(dataset.cases)), parsed_candidate_exact=_metric(t["candidate"], t["candidate_expected"]),
        abstention_correct=_metric(t["abstention"], t["abstention_expected"])) for name, t in totals.items()}
    with localcontext() as ctx:
        ctx.prec = 28
        mean = format(sum(latencies) / Decimal(len(latencies)), "f") if latencies else None
    return dict(report_version="extraction-spike-report-v1", dataset_version=dataset.version,
        manifest_digest=dataset.manifest_digest, schema_version=dataset.schema_version,
        execution_timestamp=execution_timestamp.astimezone(timezone.utc).isoformat() if execution_timestamp is not None else None,
        adapter=to_data(adapter.metadata), capabilities=to_data(adapter.capabilities),
        unsupported_capabilities=[name for name, supported in to_data(adapter.capabilities).items() if not supported],
        interpretation="Structured synthetic observation agreement only; not visual/VLM or production accuracy.",
        cases=case_reports, aggregate=dict(documents_attempted=len(dataset.cases), extractions_completed=completed,
            status_counts={status: sum(c["extraction_status"] == status for c in case_reports) for status in [s.value for s in ExtractionStatus] + ["ADAPTER_ERROR"]},
            failed_or_unsupported=sum(c["extraction_status"] in {"ADAPTER_ERROR", "FAILED", "UNSUPPORTED"} for c in case_reports),
            critical_fields=critical, state_correct=_metric(states_ok, expected_observations),
            abstention_correct=_metric(abstained_ok, abstentions), row_coverage=_metric(rows_present, row_count),
            row_fields_exact=_metric(row_fields_ok, row_fields_expected), unexpected_rows=unexpected_rows,
            page_locator_availability=dict(available=page_locations, expected=expected_observations, ratio=_ratio(page_locations, expected_observations) if adapter.capabilities.page_locators else None),
            bbox_availability=dict(available=boxes, expected=expected_observations, ratio=_ratio(boxes, expected_observations) if adapter.capabilities.bounding_boxes else None),
            adapter_latency_ms=dict(available_count=len(latencies), document_count=len(dataset.cases),
                minimum=to_data(min(latencies)) if latencies else None, maximum=to_data(max(latencies)) if latencies else None, mean=mean)))


def main():
    parser = argparse.ArgumentParser(description="Compare synthetic fixture observations; no model/PDF/image execution.")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset = load_dataset(args.dataset)
    report = run_spike(dataset, load_fixture_adapter(args.dataset, dataset), execution_timestamp=datetime.now(timezone.utc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(dataset.cases)}-case structured fixture comparison to {args.output}")


if __name__ == "__main__":
    main()
