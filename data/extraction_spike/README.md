# Structured synthetic extraction spike set

P0-04A prepares **10 cases**, dataset `extraction-spike-v1`, extraction schema `extraction-v1`. Every input and response is fictional and explicitly synthetic. The manifest's `STRUCTURED_ONLY_NO_VISUAL_ARTIFACTS` marker is literal: there are no images, PDFs, rendered pages, OCR results or VLM outputs. Available text is authored synthetic text; poor/rotated/obscured/repeated layouts are annotations or declared metadata. Future document/page artifact references are null. No pixels were inspected or transformed.

| Case | Variation | Expected observations |
|---|---|---|
| EXTRACT-001 | Clean single-page vendor invoice | Raw `INR 1,18,000.00` distinct from candidate `118000.00`; exclusive tax label; one row. |
| EXTRACT-002 | Multi-page vendor invoice | Two declared pages; three rows with page-level source references. |
| EXTRACT-003 | Clean employee receipt | Taxi/merchant facts; PO field NOT_APPLICABLE to this receipt schema. |
| EXTRACT-004 | Small/poor receipt text | Total ILLEGIBLE with no parsed candidate; annotation simulates unreadability. |
| EXTRACT-005 | Rotated receipt | Declared 90-degree metadata; no rotation detection/correction was run. |
| EXTRACT-006 | Ambiguous numeric date | Raw `03/04/2026`, AMBIGUOUS; no locale or chosen date guessed. |
| EXTRACT-007 | Tax-inclusive vendor invoice | Explicit inclusive tax label and authored amount observations; no tax arithmetic executed. |
| EXTRACT-008 | Missing PO reference | PO field MISSING with null raw/candidate. |
| EXTRACT-009 | Obscured critical field | Total ILLEGIBLE with null candidate; surrounding values do not reconstruct it. |
| EXTRACT-010 | Repeated header/footer | Two declared pages but one logical item; footer instruction is untrusted observed text. |

## Contracts and files

The [domain contract](../../apps/api/app/domain/extraction.py) uses frozen standard-library types. DocumentBundle includes scoped UUIDs, positive version, source type, ordered one-based page references, available text and future artifact slots. Header fields (maximum 64), flat indexed line items (maximum 200), and fields per row (maximum 16) are bounded; pages are bounded to 30. These are local contract resource limits, not TypeLLM capability claims.

FieldObservation preserves raw text, optional unverified candidate text, explicit state and optional EvidenceReference. Only PRESENT can carry a parsed candidate; MISSING cannot carry invented raw text. Page and optional normalized-original-page BoundingBox semantics reuse P0-02. No numeric confidence is required or supplied. Diagnostic notes, if used, are uncalibrated observations. No schema includes screening decisions or private reasoning traces. Receipt-field NOT_APPLICABLE is a schema annotation, not a policy waiver or RuleStatus.

ExtractionResult identifies run UUID, document/version/scope, schema, adapter/provider/version, optional model/template/runtime versions, status, optional Decimal elapsed milliseconds and raw artifact reference. COMPLETED means the adapter produced its observations; explicit MISSING/ILLEGIBLE/AMBIGUOUS fields may still exist. PARTIAL, FAILED and UNSUPPORTED describe extraction execution, never PASS/REVIEW/HOLD. Failures/unsupported responses require a code. Structural binding does not establish authorization, source existence or factual correctness.

- [manifest.json](manifest.json): input bundles, response paths and explicit expected header/row states/raw/candidates. Ground truth is separate from provider-shaped responses and contains no screening labels.
- `responses/*.json`: authored replay outputs with declared synthetic page evidence, fixed run UUIDs and exact input digests. There are no boxes, model/template/runtime versions or timing values to invent.
- [fixtures.sha256](fixtures.sha256): 11 JSON byte checksums (manifest plus ten responses), independent of the unchanged P0-03 23-file checksum set.

The [fixture adapter](../../apps/api/app/extraction/fixture.py) accepts only synthetic inputs and the known schema. It replays immutable responses keyed by the complete canonical input digest, then verifies document/version/scope/page binding. It does not parse text, read files during extraction, inspect finance golden cases or execute rules. Same input repeats the same synthetic run ID and semantic output; this replay identity is not a persistent production ExtractionRun/audit service.

## Harness and report meaning

The [ExtractionAdapter Protocol](../../apps/api/app/extraction/base.py) exposes `extract(document_bundle, schema_version) -> ExtractionResult`, metadata and explicit capabilities. [run_spike](../../apps/api/app/extraction/spike.py) accepts any conforming adapter and compares it with the same immutable expectations. Only fixture replay is implemented/tested now. Later visual inputs/provider integrations require their own approved preparation/version update.

From the repository root:

```bash
python3 scripts/benchmark/extraction_spike.py --dataset data/extraction_spike --output generated/reports/extraction-fixture.json
python3 -m pytest apps/api/tests/unit/extraction -q
sha256sum -c data/extraction_spike/fixtures.sha256
```

The runtime JSON records report/schema/dataset versions, canonical manifest SHA-256, adapter/provider/model/version metadata, optional execution timestamp, capabilities, each result/status/run/failure, comparisons, row counts and optional adapter latency. Reports under `generated/reports/` are ignored by Git. Library comparisons default to no timestamp and are deterministic; the CLI supplies current UTC time only to generated runtime output. Adapter exceptions contribute a failure with exception class only; their potentially private messages are not logged.

Metrics use explicit numerators/denominators. Ratios are decimal strings; a zero denominator or unsupported capability yields null, never a perfect score.

| Metric | Meaning |
|---|---|
| Critical fields | Total, currency, document number, date and party name each have ten expectations. Compare raw text, explicit state and combined observation independently; candidate exact match is scored only where a candidate is annotated. |
| State/abstention | 130 header/row observations; seven non-PRESENT expectations. Correct abstention requires the exact expected state and no guessed candidate. An omitted observation does not equal explicit MISSING. |
| Rows | Twelve expected indexed rows, 48 important row values. Coverage counts expected row indices present; value agreement is separate. Missing/extra rows are reported per case and extra rows separately aggregated. No general table alignment is attempted. |
| Locators | Page/box availability for expected observations, not evidence correctness. Fixture capability declares page-only locators; boxes/visual input are unsupported. |
| Execution/latency | Status counts, failed/unsupported/error cases and optional adapter-supplied millisecond count/min/max/mean. No latency is fabricated or inferred from replay speed. |

Authored responses mirror the annotations, so perfect fixture agreement is expected by construction. Tests deliberately corrupt actual fields, guesses, rows, metadata and capabilities to verify detection. This is comparison/replay validation, not independently measured extraction accuracy, calibrated confidence, production quality, finance eligibility or VLM performance. No TypeLLM/SGLang/OCR/model work occurred.

## Intentional dataset updates

Preserve the original finance fixture set and its checksum manifest. For an approved extraction-fixture change, edit only this dataset's inputs/ground truth/responses, update dataset/schema/adapter versions when semantics change, and recalculate exact input digests for replay responses. Do not regenerate old finance fixtures. Use a deterministic sorted checksum list from the repository root:

```bash
find data/extraction_spike -type f -name '*.json' -print0 | sort -z | xargs -0 sha256sum > data/extraction_spike/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
python3 -m pytest apps/api/tests/unit/extraction -q
python3 -m pytest -q
```

Review altered expectations independently; never change them merely to make a provider look correct. Add actual artifact checksums and update artifact-status/loader conventions only when future visual preparation is approved. The current source manifest contains no unstable timestamps; future runtime reports stay separate. See the [document-only compatibility checklist](../../docs/extraction_compatibility.md) before proposed provider environment changes.
