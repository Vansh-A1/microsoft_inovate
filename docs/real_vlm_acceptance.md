# Real local VLM extraction acceptance — 2026-10-04

The user's priority override establishes real document inference on the current
machine. This is a compatibility/quality smoke and application integration record,
not universal invoice accuracy or a production deployment approval. Historical
Phase-0/6 runtime deferrals remain valid for their original tuples and scopes.

## Executed stack

| Component | Actual selection |
|---|---|
| GPU | NVIDIA RTX 2000 Ada Generation, SM 8.9, 16,380 MiB |
| Host driver | 550.120, unchanged |
| Serving Python | Isolated 3.12.3; finance Python 3.13.11 unchanged |
| Torch / bundled CUDA | 2.6.0+cu124 / 12.4 |
| SGLang | 0.4.6.post5, direct user-owned serving; Docker remains denied |
| Serving Transformers | 4.51.1 |
| Model | Qwen/Qwen2.5-VL-3B-Instruct |
| Revision | 66285546d2b821cf421d4f5eb2576359d3770cd3 |
| Precision | BF16; no quantization experiment was needed or claimed |
| Actual TypeLLM | 0.5.1, CPU client Python 3.12.3 / Transformers 5.3.0 |
| Client bridge | sglang-cu124-transport-v1, actual TypeLLM compiler/generation |
| Isolation | Authenticated loopback gateway, serial cache flush per generation |

The earlier CUDA-13 runtime would require a different driver; this tuple avoids
that host change and fits the available GPU. TypeLLM and serving Transformers
requirements are isolated in separate environments. See [ADR-0015](adr/0015-current-driver-compatible-real-vlm.md)
for measured compatibility repairs. The pinned model's actual license is the
Qwen RESEARCH LICENSE AGREEMENT, not Apache-2.0. Commercial deployment needs a
separate license/quality/hosting decision.

## Gates A–J

| Gate | Actual evidence |
|---|---|
| A GPU runtime | Real GPU tensor arithmetic and model execution on CUDA 12.4. |
| B Raw VLM image | Actual supplied invoice through Transformers vision generation; header and three rows returned. First image generation 9.618 s; cached asset load 1.914 s. This initial smoke used an isolated Transformers 5.3 overlay, before the final SGLang lane. |
| C TypeLLM text | Real server: printed amount returned as string `12.50`, 0.741 s. The raw amount omitted the source's currency token; no currency inference is claimed from this one question. |
| D TypeLLM image | Actual invoice number and dollar-prefixed total returned through TypeLLM, 2.408 s. |
| E Header | Primary supplier, invoice/date/due/PO, subtotal/tax/total matched independently; visible addresses and bill-to were extracted. Currency remains explicitly ambiguous. |
| F Lines | All 3 visible primary rows: 12/12 description/quantity/unit-price/amount literals matched. No expected answers were sent to the model. |
| G Adapter | Real outputs mapped into extraction-v1 with source document/page, unknown bbox and actual model/runtime/prompt metadata. |
| H Upload pipeline | Opt-in real tests exercise secure upload, SHA-preserved original, preprocessing, VLM-only and actual OCR-plus-VLM routes, persisted runs/observations/drafts and cross-tenant denial. |
| I Normalization | Actual INR strings normalize to decimal strings; total `23600.00`. Numeric-date/dollar ambiguity and row arithmetic mismatches block acceptance. |
| J Finance | The actual scanned synthetic invoice is corrected against its printed row, verified and committed; a durable finance evaluation returns HOLD for required approvals, with DOC-001 PASS. Retained extraction/evaluation history is unchanged. |

The Northstar `INV-2026-1004` source file was not found in repository/runtime or
available uploads. The already supplied invoice image was used as the user allowed.
Its original, independent expectations and complete raw output remain private in
ignored runtime reports. No uploaded document bytes or personal-address extracts
are added to Git.

## Benchmark and timings

One resident model served repeated documents. This final five-case benchmark was
run after visual row discovery stopped trusting partial OCR separators. Every
case uses actual image/PDF bytes and the real TypeLLM adapter. Digital PDFs are
deliberately forced through VLM for this smoke; a separate live application test
proves that complete native mapping stays cheap.

| Actual source variant | Total s | Header s | Inventory s | Rows s | Independent result |
|---|---:|---:|---:|---:|---|
| Supplied ruled-table invoice, one page | 33.717 | 17.543 | 1.500 | 13.779 | 8/8 literal headers, expected AMBIGUOUS currency, 12/12 core row literals, 3 rows. Missing fees/currency/date context still NEEDS_INPUT. |
| Rasterized preserved synthetic invoice | 58.416 | 36.491 | 4.764 | 16.884 | 6/6 checked canonical headers; 1 row, net/gross confusion caught by arithmetic. |
| Same synthetic invoice's digital PDF | 59.214 | 37.130 | 4.863 | 16.892 | 6/6 checked canonical headers; 1 row, arithmetic blocks incorrect amounts. |
| Two-page synthetic invoice | 117.735 | 73.549 | 9.742 | 33.929 | 6/6 checked canonical headers; rows linked to pages 1 and 2, arithmetic mismatch remains unresolved. |
| Actual synthetic receipt photograph | 34.760 | 34.461 | 0 | 0 | 4/4 checked receipt headers; no normalization findings. Optional item rows explicitly not requested without table candidates. |

The digital/rasterized invoices share one source; the multi-page fixture repeats
headers. They are source variants, not five independent real-world documents.
Synthetic comparisons above omit separate vendor/PO row checks; they are not
represented as perfect extraction. Full private reports include actual raw
observations, normalization traces, page transformations and independent checks.

One paired primary-invoice experiment disabled row crops while using the same
resident model, prompts and actual source. Both runs matched 12/12 core row
literals. Full-page rows took **20.413 s**, versus measured composite crops
**13.779 s**; full document extraction was **39.481 s** versus **33.717 s**.
This is one hardware/session comparison, not a statistically established speedup
or batch-throughput measurement. Private comparison JSON preserves actual outputs.

Fresh process startup with cached assets measured **9.421 s**. Whole-device
memory: **idle 1,735 MiB**, **loaded/health-ready 11,651 MiB**, **peak 14,733 MiB**
during the final benchmark. These include other display/process memory and are
not just weights or tensor allocations. Initial raw Transformers allocated peak
7,854,726,656 bytes and loaded tensors 7,656,617,984 bytes. No concurrent throughput,
new-download cold start, production availability or quantized performance is claimed.

## Integrity and remaining limits

Native PDF positions and OCR coordinate transforms are retained where trustworthy.
Measured ruled-grid crops preserve dimensions/extents/offsets/hash/storage/parent
transform; their extents never become field bboxes. Invoice visual row inventory
is independent of incomplete OCR mapping. Conflicting row counts retain both
provider outputs, expose the larger set as ambiguous candidates and require input.

Model money is a raw string, never a float. `document-normalizer-v2` adds the
visual row's printed `amount` to the existing trusted Decimal/currency handling;
all earlier field rules and retained v1 traces remain unchanged. Quantities/rates
cannot acquire currency units.
Reconciliation compares formatting differences only with agreed currency and
never selects a value to make arithmetic or a finance rule pass. Unknown fields
are not zero. The VLM cannot return authoritative finance decisions.

A small model can invent tax-basis/receipt semantics or confuse compact tables.
Visible receipt/header extras are not necessarily correct merely because a scalar
schema is valid. Human source verification remains required. Numeric dates require
locale/order; a dollar symbol alone does not identify an ISO currency. Advanced
table families and automatic multi-invoice segmentation are not validated here.
The 120-second document budget is close to the measured two-page case; larger
visual bundles may end explicitly incomplete rather than succeed silently.

The gateway uses actual TypeLLM constrained generation, adapts only transport
incompatibilities, and retains no hidden reasoning. An actual refused connection
produces FAILED_RETRYABLE / PROVIDER_UNAVAILABLE, preserves preprocessing and
creates no observations/draft/finance decision. Failed cache cleanup makes the
provider unavailable until restart; there is no fixture or zero-risk fallback.

All model/runtime/cache/report/private document artifacts are ignored. No NVIDIA
driver, host CUDA, GPU configuration, system Python or Docker daemon was changed.
No sudo was used. The upstream Decord wheel's incorrect WHEEL/RECORD metadata was
rebuilt locally; all runtime files were verified byte-identical. All three
environment dependency checks pass. Raw outputs are not supervised-risk data.

## Verification and publication

Before integration: full backend **779 passed**, one existing warning,
**2563.64 s**, exit 0; browser **36 passed**, TypeScript and production build
exit 0. Post-integration full backend: **803 passed, 6 opt-in GPU cases skipped**,
one existing warning, **2375.28 s**, exit 0. Five final monetary/reconciliation
guard cases were added after that collection; the final affected CPU batch is
**200 passed**, one existing warning, **2.30 s**, exit 0. These overlapping runs
cover all **808 current ordinary backend cases**; 808 is not a single full-run
count. The current collection is 814 including the six opt-in GPU cases.

The separate final real-GPU run is **6 passed**, one existing warning,
**241.19 s**, exit 0. Final actual-backend browser regression: **37 passed**,
**2.8 minutes**, exit 0. TypeScript and production build pass, exit 0. The focused
four-flow browser repair batch also passed (6.4 s). Source-viewer inspection used
actual uploaded model output at 1280×800 and 390×844: three rows, one-based field
page links, page-level evidence without invented highlights, explicit NEEDS_INPUT
and no document-page horizontal overflow at the mobile viewport.

Alembic drift (no new operations), OpenAPI contract, finance/client/serving
dependency checks, original source-pack hashes, three fixture manifests, source
security and redacted Gitleaks with its detection probe have passed. A full
post-integration browser run identified a delayed reference-list response race,
a test navigation race and the outdated deferred-provider assertion; repairs
preserve access and finance behavior and pass the final browser suite. The owned
inference stop command was exercised: health failed after stop, then returned
AVAILABLE after start; a real TypeLLM image smoke succeeded after restart. The
application supervisor was restarted to load the final normalization code.

Executed application checks: `.venv/bin/pytest -q apps/api/tests`; final affected
batch with `test_vlm_integration_contract.py`, `test_extraction_documents.py`,
`test_documents_phase2.py` and `unit/extraction`; opt-in `test_real_vlm.py` with
`AP_RUN_REAL_VLM=1` and the actual private image path; `npm run test:e2e`,
`npm run typecheck` and `npm run build` in `apps/web`. Full/private command output
is retained under `runtime/inference/logs`. Dependency checks are `python -m pip
check` in each of the three environments. See the runbook for real-test commands.

Implementation is checkpointed locally as `4d69cf0`; the separate final UI/docs
commit preserves the measured report and browser fixes. The task makes reviewed
local commits only. No Git push, token repair, workflow
upload, cloud deployment or later-phase work is attempted under this override.
See [run/start/stop/health/cleanup instructions](runbooks/local-inference.md).
