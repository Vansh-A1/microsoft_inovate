# Phase-2 exit review — Real document ingestion and extraction

Disposition: **COMPLETE LOCALLY, WITH APPROVED ENTERPRISE-RUNTIME DEFERRAL**. P2-01–P2-05 were continuously
authorized on 2026-10-03. Phase 3 has not begun. The approved external deferral
covers actual enterprise TypeLLM/SGLang/model execution, not the CPU document
pipeline or provider contract tests. Publication is a separately recorded gate.

| Task | Implemented behavior |
|---|---|
| P2-01 | Authenticated create/upload/finalize sessions, server-generated private keys, streaming SHA-256, immutable original metadata, content sniffing, quarantine, typed byte/page/pixel/time/resource limits and replaceable scanner. Local scanner status is NOT_CONFIGURED; required scanning blocks it. |
| P2-02 | Actual PyMuPDF text/spans/rendering, Pillow EXIF orientation, OpenCV defined blur/exposure measurements, original-to-derived transforms, one-based immutable pages and SHA-256 fingerprints. No pHash duplicate decision. |
| P2-03 | Native-first labeled header/explicit table extraction; actual replaceable English CPU OCR; remote TypeLLM flat state/string questions and bounded per-page/row calls, error/null handling, critical disagreement and versioned routing sidecars. Live GPU execution is deferred. |
| P2-04 | Observation-linked Decimal/string/date/key normalization traces, strict critical/source/arithmetic validation, manual source verification, new canonical revisions/evaluations, correction actor/reason/old/new/page lineage and original/page/box/zoom viewer. |
| P2-05 | Explicit CSV/XLSX column mapping with immutable raw/parsed/validation cells, rule-to-cell resolution, formula/macro rejection, actual receipt UUID requirements and versioned multi-document roles/page ranges. Uncertain segmentation requires input. |

## Exit criteria and evidence

| Specification criterion | Evidence / disposition |
|---|---|
| Representative PDFs/photos produce versioned facts and evidence. | Actual native and multi-page PDFs, scanned PDF/PNG and EXIF JPEG are parsed. PostgreSQL stores originals, pages, extraction runs, raw observations and normalized drafts. Source verification creates canonical versions linked to physical documents, the existing 20 controls compute decisions, and authenticated evidence resolves to actual pages/boxes. Both branches are exercised in integration and browser flows. |
| Unreadable or ambiguous critical fields cannot PASS. | Draft critical/date/currency/amount/source/arithmetic findings require input; unsafe files are quarantined without a screening decision. Provider timeout/configuration failure does not become empty success or fixture replay. Source confirmation cannot dismiss unresolved critical fields. Mandatory approval and other finance controls remain authoritative after verification. |
| Fixture and live extraction modes are distinguishable. | Preserved P0 FIXTURE replay and P1 STRUCTURED_SYNTHETIC intake remain explicit. Actual document runs record NATIVE_TEXT or LOCAL_OCR and canonical reports DOCUMENT_DERIVED. ENTERPRISE_VLM records configured/not-configured/error status; no live-model success or GPU metric is claimed. |

Document drafts use processing state, not a finance screening decision. A READY
draft still requires a trusted reviewer to confirm source facts and map reference
IDs. Confirmation is factual verification, not approval authority. Ordinary new
cases commonly HOLD for missing approvals; trusted test-only approvals demonstrate
that complete controls can PASS after actual source verification. Unknown facts
are never silently replaced with zero, a guessed date or a convenient provider.

## Preservation and architecture

The Phase-1 pure engine, ruleset `rules-p1-v7`, arithmetic and rule versions remain
unchanged. A narrow pure `document-source-v1` extension reconciles DOC-001 only
for physical document contexts and cannot clear another mandatory result.
Mapped import evidence changes provenance, not finance decisions. Historical
evaluations remain immutable. Physical reports use `report-p2-v1`; structured
reports retain their existing schema. [ADR-0010](adr/0010-phase2-document-lineage-and-provider-boundary.md)
records the additive queue and source boundary.

Migration `0004_documents` adds twelve scoped tables to the existing 22. All 34
business tables enforce forced tenant/entity RLS. Eight new fact/link tables
reject mutation through ORM and PostgreSQL triggers. Existing migrations and
transaction-job constraints are preserved. Document stages use leased, bounded
at-least-once execution and guarded atomic persistence/outbox/audit; stale workers
cannot duplicate pages/stages or financial effects. Failed attempts retain the
last successful stage. Intake itself is the upload/finalize workflow; durable
stages are PREPROCESS, EXTRACT, NORMALIZE, VALIDATE and FINALIZE.

Initial bounds are 25 MiB/original, 30 pages and 40 megapixels/image, 1800-pixel
previews, 300,000 native text characters, 20,000 spans, 100 MiB derived output,
30-second parser limit, 1.5 GiB parser address space and 60-second upload receive
limit. Native routing uses a defined 80-character minimum and conservative label
coverage. These are routing measurements and resource limits, not accuracy scores.
Actual boxes map measured text coordinates; unknown rows or corrected fields use
page evidence with null boxes. Originals remain unchanged outside Git.

## Actual CPU benchmark

Command: `.venv/bin/python scripts/benchmark/documents_phase2.py`, exit 0.
Fourteen actual synthetic sources produced **7 READY, 5 NEEDS_INPUT and 2
PROCESSING_FAILURE** outcomes (the latter corrupt/encrypted sources are quarantined
by the durable pipeline). Clean native vendor/multi-page/instruction PDFs matched
6/6 independent printed critical fields; native receipt/scanned PDF/PNG/EXIF photo
matched 4/4. Ambiguous/missing/conflicting/bundled sources abstained on the affected
facts; unreadable image matched 0/4 and required input. Per-case actual CPU elapsed
times in this run were 0.085895–0.371405 seconds. These single-run timings include
local parsing/extraction, exclude durable queues/finance and establish no SLA.
The ignored report is `generated/reports/documents-phase2.json`; independent
ground truth is never read by extraction. Fifteen source/ground-truth files have
byte hashes. Corpus regeneration preserves the pinned encrypted rejection seed.

## Verification

Final commands, counts, repair history and publication outcome are recorded in
[progress](progress.md). Full Python regression: **641 passed**, 554.98s, zero
failures/skips. Final production browser gate: **16 passed**, 41.9s, including all
11 original checks plus actual PDF/photo/correction/pages/boxes/zoom/quarantine and
mobile/loading/error flows. TypeScript/build, dependency and migration drift checks
passed. Fresh schema/upgrade/downgrade, numeric constraints, RLS, finance concurrency
and immutable/source stage retry checks ran in PostgreSQL. Original inputs and
9/23/11 earlier fixture hashes plus the new 15-file corpus pass. Saved OpenAPI and
generated client match; private artifacts remain ignored and staged source is
reviewed for credentials/whitespace. The final source-coverage guard passed its
actual malformed-row PostgreSQL test (18.38s) after the aggregate run; confirmation
cannot dismiss unparsed rows. No pending GPU/provider execution is counted passed.

## Limits and external gates

Native parsing covers explicit labels and bounded pipe tables; arbitrary tables,
row cropping, deskew, complex layouts and automatic segmentation are not claimed.
Repeated headers are conservatively removed; ambiguous coverage remains input.
English OCR works on this small synthetic corpus. Production data authorization,
SSO, policy/reference inputs, quality thresholds and provider data terms remain
external. Malware scanning is NOT_CONFIGURED and is not CLEAN; production must
require and configure a real scanner. Parser bounds are a development safety
boundary, not a production sandbox certification. Private orphan blobs after
crash/rollback need later storage reconciliation.

TypeLLM 0.5.1 SDK contract and real schema compiler were checked without inference;
mocked responses test float/null/authority/timeout/row boundaries. The optional SDK
and approved local tokenizer assets are required on an appropriate client host.
No VLM weights, local SGLang, NVIDIA/Docker changes or cloud resources were used.
Driver 550.120 versus approved CUDA 13 >=580 and denied Docker access remain
recorded external blockers. Live VLM quality/latency/VRAM, tier cascade, batching,
quantization and production model selection remain deferred to suitable authorized
infrastructure. Stronger model fallback is not configured; unresolved facts go to
human input. No hidden reasoning or fabricated confidence is stored.

No Phase-3 matching, fuzzy/image duplicate decision, shared-receipt allocation,
advanced acceptance/approval workflow, ML or deployment work was introduced.
Next task requires separate approval: **Phase 3**, beginning with P3-01.
