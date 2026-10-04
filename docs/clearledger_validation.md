# ClearLedger extraction validation — 2026-10-04

Continuation of [the first hardening checkpoint](clearledger_hardening.md).
CL-04/CL-05 improve extraction robustness, speed and source grounding while
preserving ClearLedger, its finance engine and accepted ADR-0015 runtime. No
further visual redesign, public deployment or push is part of this milestone.
See [ADR-0017](adr/0017-optional-isolated-cpu-ocr.md).

## Implemented behavior

Measured geometry now handles nearby aligned labels above values and bounded
wrapped descriptions followed by complete next rows. Crossing/competing values,
conflicting identity, ambiguous dates/currencies and incomplete tables abstain.
Legacy flattened text cannot override an independently associated field or turn
another printed label into a header value. Core mapping is still independent of
FastAPI and the finance decision engine.

TypeLLM questions respect the declared invoice/receipt purpose. Complete
independently observed table headings narrow requested columns. Strict
extraction-v1 is preserved; actual fields/question counts, images and timings
are recorded in extraction-routing-v3. Unrequested observations remain missing.
Model-only row discount/net/tax/gross observations become AMBIGUOUS unless the
corresponding row column is independently observed. Raw values/history survive;
normalization cannot create accounting facts from totals or implied tax.

Optional RapidOCR runs in a separate pinned CPU environment, selected by explicit
server configuration. The default remains Tesseract. The local demo opts in;
actual per-page package/model/provider provenance is retained. The resident
stdio child has source-root restrictions, no credential environment, bounded
responses, partial-response deadlines and actual CPU provider attestation.
Real Tesseract fallback uses only the remaining request budget. Child recovery
does not change drivers, GPU settings, credentials or system services. See the
[setup and rollback runbook](runbooks/cpu-ocr-experiment.md).

## Frozen source design

`data/clearledger_challenge/manifest.json` freezes twelve independently invented
lawful sources before tuning, on commit `88f3559`. Six are tuning cases and six
are reserved layouts. Reserved baseline outputs were sealed until tuning ended.
The harness verifies source SHA-256 on every run, refuses to overwrite results,
and scores truth only after production extraction/normalization. Fixture IDs,
filenames and answers do not enter inference or parser special cases.

The corpus varies native/scan, Courier/Times/Helvetica, side/stacked/three-column
headers, reordered headings, multi-page continuation, wrapped rows, gray sparse
scans, multiple invoice identities, ambiguous date/currency and corruption.
It shares fictional vocabulary and amounts; it is a layout holdout, not a
representative independent customer distribution. No real customer invoice is
in this corpus. Eleven readable sources plus one corrupt PDF are not a 40–60
invoice acceptance corpus or evidence of production accuracy.

The raw outputs remain ignored under `runtime/clearledger`. Inspectable
[synthetic-only metrics](../data/clearledger_challenge/results-2026-10-04.json)
retain source hashes, run/source-code provenance and individual outcomes. The
integrated runs preceded final malformed-response/timeout fixes and explicit
native MISSING row projection. Those fixes do not change printed mapping.
Their regression is recorded below.

## Measured pipeline results

All seconds include production processing/rendering, storage, extraction routing
and normalization. They exclude upload, database queue, browser rendering and
human confirmation. The model was resident, not cold loaded. Integrated CPU
first-visual requests include child startup; later requests reuse it. Single
executions on a shared host are not latency distributions or speed promises.

| Source/layout | Before s | After default s | After CPU s | Headers before → CPU | Row values before → CPU | VLM calls before → CPU |
|---|---:|---:|---:|---:|---:|---:|
| t01 native side columns | 0.229 | 0.209 | 0.222 | 7/7 → 7/7 | 8/8 → 8/8 | 0 → 0 |
| t02 labels above values | 67.789 | 0.207 | 0.250 | 4/7 → 7/7 | 4/8 → 8/8 | 4 → 0 |
| t03 wrapped native description | 35.808 | 0.207 | 0.238 | 7/7 → 7/7 | 0/8 → 8/8 | 3 → 0 |
| t04 ruled scan | 39.185 | 33.752 | 1.804 | 6/7 → 7/7 | 4/8 → 8/8 | 4 → 0 |
| t05 sparse gray scan/ambiguity | 37.098 | 33.277 | 1.460 | 6/7 → 7/7 | 4/8 → 8/8 | 4 → 0 |
| t06 corrupt PDF | 0.091 | 0.086 | 0.084 | CORRUPT_DOCUMENT | No extraction | 0 → 0 |
| h01 reserved landscape/three columns | 66.006 | 45.835 | 45.792 | 7/7 → 7/7 | 4/8 → 4/8 | 4 → 4 |
| h02 reserved three-page reordered table | 0.622 | 0.340 | 1.264 | 7/7 → 7/7 | 12/12 → 12/12 | 0 → 0 |
| h03 reserved Times card scan | 38.030 | 34.051 | 1.531 | 3/7 → 7/7 | 4/8 → 8/8 | 4 → 0 |
| h04 reserved wrapped Times scan | 38.304 | 34.756 | 13.762 | 6/7 → 7/7 | 4/8 → 0/8 | 4 → 3 |
| h05 reserved conflicting identities | 0.285 | 0.287 | 0.287 | 6/6 → 6/6 | 16/16 → 16/16 | 0 → 0 |
| h06 reserved date/currency ambiguity | 0.197 | 0.209 | 0.208 | 7/7 → 7/7 | 8/8 → 8/8 | 0 → 0 |

Headers measure literal observed values; row checks measure description, quantity,
unit price and printed amount. They are not full canonical invoice accuracy or
finance eligibility. Ambiguous raw `$`/dates can match literal text while remaining
unresolved during trusted normalization.

| Check | Before | After default | After optional CPU |
|---|---:|---:|---:|
| Checked printed header literals | 66/76 | 72/76 | 76/76 |
| Checked printed core row values | 68/100 | 80/100 | 88/100 |
| Absent fields explicitly MISSING | 18/30 | 19/30 | 28/30 |
| Required date/currency/identity abstentions | 5/5 | 5/5 | 5/5 |
| Observed PRESENT false positives among checked absent headers | 0 | 0 | 0 |

The two CPU absent-field mismatches are provider nulls on h01, conservatively
AMBIGUOUS rather than proven MISSING. They do not become canonical values.
The baseline did not instrument every unprinted row column; no aggregate zero
is inferred from missing baseline telemetry. A paired forced-VLM t04 control
did observe eight unprinted row accounting values canonical before, versus zero
after. That run took 37.799 → 33.962 seconds with the same source/current model.
This isolated comparison is not a general speed estimate.

All readable challenge runs finish NEEDS_INPUT with no finance decision because
accounting semantics, source confirmation or deliberate ambiguity remain
unresolved. Corruption fails explicitly. No missing tax/discount is replaced by
zero, and no challenge result is made PASS to improve a metric.

Failures are material: h01 still loses the second model row. On h04 the model
repeats a row and disagrees with independent OCR inventory; all core row fields
stay ambiguous. This reduces its usable row score from 4/8 to 0/8 rather than
accepting a potentially wrong association. TABLE_COVERAGE_UNCERTAIN and raw
observations remain available to the reviewer. These reserved failures were not
used to retune and then relabeled unseen.

Whole-device GPU peaks across these runs were 14,053 MiB before, 14,495 MiB with
the default path, and 15,131 MiB with optional CPU routing. They include resident
weights and other processes; no GPU memory improvement is claimed. The CPU
candidate measured 428.58 MiB peak RSS, about 0.279 seconds initialization inside
its process, and 1.279/1.225 seconds OCR-only on two tuning scans. Host/process
startup and full pipeline measurements are distinct.

## Actual async timing

The fictional t04 scan was uploaded through the real loopback web proxy/API and
durable document workers. Cold worker: upload 0.336 seconds, upload-to-final-state
5.021 seconds. Warm worker: upload 0.130 seconds, upload-to-final-state 4.282
seconds. Actual stage observations include QUEUED/PROCESSING, PREPROCESS,
EXTRACT, NORMALIZE, VALIDATE and FINALIZE. Both finish NEEDS_INPUT, with no error
or finance decision. Polling granularity is 0.5 seconds; browser rendering,
source review and approvals are excluded. There is no old-code end-to-end paired
baseline, so pipeline before/after numbers are not compared to this queue timing.

```bash
.venv/bin/python scripts/benchmark/clearledger_challenge.py --label final-default --split tuning
.venv/bin/python scripts/benchmark/clearledger_challenge.py --label final-default --split holdout
.venv/bin/python scripts/benchmark/clearledger_challenge.py --label integrated-rapid --split tuning --rapid-production
.venv/bin/python scripts/benchmark/clearledger_challenge.py --label integrated-rapid --split holdout --rapid-production
.venv/bin/python scripts/benchmark/clearledger_async.py --label integrated-cold-worker --case t04
.venv/bin/python scripts/benchmark/clearledger_async.py --label integrated-warm-worker --case t04
```

The labels above identify already executed records; use fresh labels for new
measurements. Re-running baseline with current code is not the preserved baseline.

## Verification checkpoint

Final focused extraction/response-boundary regression: **121 passed, 3.30 seconds,
exit 0**, one existing Starlette/httpx deprecation warning. This includes real
partial-stdio timeout/child termination, invalid/NaN/bool response rejection,
exact EXIF coordinate mapping, model/package/provider pinning, bounded fallback,
stale optional Tesseract paths, printed geometry and model-only accounting guards.

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_cpu_ocr.py apps/api/tests/test_clearledger_grounding.py apps/api/tests/test_clearledger_layout.py apps/api/tests/test_extraction_documents.py apps/api/tests/test_vlm_integration_contract.py apps/api/tests/test_documents_phase2.py -q --tb=short
```

Before the final timeout fixes, the broader focused set passed 113 cases in 2.87
seconds and actual CPU integration passed three cases in 30.77 seconds, exit 0.
Earlier purpose-question test fixtures failed two assertions while 73 passed;
their vendor-only mock contract was corrected, preserving strict unknown-key
rejection. Passing checks do not erase that observed development failure.

Further scoped finance/security integration, actual CPU/model regression,
cold/warm model timing and judge/browser results are added only after execution.
The preceding full-backend and 42-pass browser checkpoint remains historical;
it is not represented as a full rerun of this milestone.

Three inspected fictional Finance/Admin laptop/phone screenshots were saved to
Library using the [Library skill](skill://plugin_connector_1p_1b8ff8edfc1481918b252c8277e23125/library/SKILL.md).
Prepared upload failed before reservation (`prepare_uploads` unavailable); the
documented direct create fallback saved all three, version 0, and local identity
xattrs were verified. The first helper invocation used an unsupported argument;
only local writeback was corrected, with no second cloud create. No private
invoice or model-result screenshot was uploaded. The temporary allowlisted phone
gallery was stopped; port 3001 was verified closed while application/model
listeners remained loopback only.

## Remaining acceptance inputs

Broader acceptance needs lawful independent layouts and adjudicated truth,
approved business policies/masters, actual identity/scanner integration and
commercial checkpoint/CPU-model attribution review. A stronger provider can
only be connected with approval. Wrapped/irregular tables and degraded scans can
still require human transcription. No universal speed, production pilot, model
accuracy, paid provider or legal/compliance certification is claimed.

## Executed integration and model results

Scoped real PostgreSQL extraction/finance/intake/security regression: **55 passed,
893.66 seconds, exit 0**, including fresh migrations, policy version selection,
tenant boundaries, source correction, independent approvals and financial capacity:

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_document_pipeline.py apps/api/tests/integration/test_document_finance.py apps/api/tests/integration/test_finance_phase3.py apps/api/tests/integration/test_release_phase6.py apps/api/tests/integration/test_clearledger_intake.py -q --tb=short
```

Final actual CPU integration: **3 passed, 32.07 seconds, exit 0**. It exercises
real CPU model hashes/providers, boxes, missing accounting/tenant rejection,
actual Tesseract fallback and actual child exit/restart after descriptor cleanup.

```bash
AP_RUN_CPU_OCR=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_cpu_ocr_live.py -q --tb=short
```

Actual current TypeLLM/Qwen suite returned **5 passed / 1 failed, 176.63 seconds,
exit 1**. The combination retains a numeric versus currency-prefixed total as an
AMBIGUOUS raw observation, with no canonical amount; its older assertion expected
a single spelling. The application safeguard was correct. The assertion now
requires ambiguity/no canonical total when independent readings differ and
allows actual OCR boxes without inventing model boxes. Its affected case returned
**1 passed, 37.73 seconds, exit 0**. All six cases are covered by these separate
passing executions; this is not a single six-pass rerun.

```bash
AP_RUN_REAL_VLM=1 AP_VLM_PRIMARY_DOCUMENT=/tmp/codex-clipboard-696b68c8-3134-4cd4-95f6-ce656aa86785.png PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_real_vlm.py -q --tb=short
AP_RUN_REAL_VLM=1 AP_VLM_PRIMARY_DOCUMENT=/tmp/codex-clipboard-696b68c8-3134-4cd4-95f6-ce656aa86785.png PYTHONPATH=apps/api .venv/bin/python -m pytest 'apps/api/tests/integration/test_real_vlm.py::test_real_primary_upload_layout_rows_and_critical_uncertainty[True]' -q --tb=short
```

The OCR-off branch explicitly disables both engines and verifies actual VLM
provenance. The synthetic image-to-finance case reaches HOLD after source review,
then PASS only after independent approvals; its HOLD survives. An actual refused
connection is retryable with no observations/draft/decision; complete native
processing bypasses the configured model.

Current cold model probe, exit 0, uses the already-authorized supplied invoice
and only the identity-verified owned model lifecycle, with OCR explicitly off:

| Work | Seconds | Peak whole-device MiB | Actual result |
|---|---:|---:|---|
| Cold service startup | 14.974 | 11,610 | Accepted revision/BF16 AVAILABLE |
| First VLM request | 30.245 | 12,546 | Five actual calls, three rows, 23 unresolved findings |
| Resident subsequent request | 30.468 | 12,594 | Five actual calls, three rows, 23 unresolved findings |

Date, currency, tax treatment and all unprinted row accounting facts remain
noncanonical. Three source row quantity/price/amount triples match independent
inspection; no finance decision is asserted. Separate actual OCR+VLM requests
took 26.158 and 24.189 seconds, both five calls and 23 unresolved findings.
The numeric/currency-prefixed total disagreement remains AMBIGUOUS. Model-only
row boxes remain unknown. These are single-source measurements with different
routing. The prior milestone's OCR+VLM probe is not a paired old-code baseline
for this new forced-VLM measurement.

```bash
.venv/bin/python scripts/benchmark/clearledger_probe.py /tmp/codex-clipboard-696b68c8-3134-4cd4-95f6-ce656aa86785.png --restart-owned-model --force-vlm --label cl04-cold-warm-vlm
.venv/bin/python scripts/benchmark/clearledger_probe.py /tmp/codex-clipboard-696b68c8-3134-4cd4-95f6-ce656aa86785.png --label cl04-resident-ocr-vlm
.venv/bin/python scripts/release/judge_verify.py
```

Read-only judge verification exits 0 for eight computed fictional scenarios,
each with 28 current controls. Four entries are eligible PASS (visual/correction
share a current source case), three HOLD and one REVIEW. Exception findings have
citations; actual source verification/provider history and original correction
HOLD survive. This check performs no reevaluation, approval or policy mutation.

The complete browser run passed **44 / one conditional outage skip / 5.7 minutes /
exit 0**, one worker/no retries. Both added actual CPU/source and wrapped-scan
checks passed. Visual inspection then exposed misleading template net/tax/gross/
unit defaults in source-derived forms. The API already blocked submission;
presentation now leaves unsupported fields blank and never seeds eligible nights.
Native v4 adds explicit MISSING row observations for audited correction controls.
Printed mapping, finance rules/migrations and historical outcomes stay unchanged.

Five grounding mocks initially duplicated those explicit fields (**115 passed /
five failed / 3.30 s / exit 1**); they now replace a field while retaining strict
duplicate rejection. The 121-pass result above follows this correction. Final
source integration passed **20 cases / 301.18 s / exit 0**, including actual CPU
and migrated PostgreSQL upload/normalization/source/finance flows:

```bash
AP_RUN_CPU_OCR=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_document_pipeline.py apps/api/tests/integration/test_document_finance.py apps/api/tests/integration/test_cpu_ocr_live.py -q --tb=short
```

Typecheck and rebuilt production web both exit 0. The affected source/role/policy/
laptop/phone browser rerun returned **17 passed / one conditional outage skip /
141.788 seconds (2.4 min) / exit 0**, one worker/no retries:

```bash
AP_RUN_CPU_OCR_BROWSER=1 PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH" npm --prefix apps/web run test:e2e -- tests/cpu-ocr.spec.ts tests/documents.spec.ts tests/release.spec.ts tests/clearledger.spec.ts tests/visual-release.spec.ts tests/hackathon.spec.ts
```

Actual final Finance source/form, 390-pixel source boxes and 1024-pixel Admin
policy viewports were inspected. The first screenshot helper used a wrong
relative Node path and exited 127 before opening a browser; the existing absolute
bundled executable succeeded. No dependency was installed to repair it. The
conditional skipped case expects an unconfigured visual provider; the current
provider is available. Actual refused-connection behavior is covered by the
passing real-model test, not described as a passed UI outage scenario.

Final source scan: **361 text files**, exit 0. Public OpenAPI and existing release
artifact/workflow contracts pass. Finance and isolated CPU `pip check` each exit
0. Gitleaks 8.30.1 reports zero source findings and its deliberate synthetic
probe detects one redacted credential-format sample. All nine original input
hashes, byte-identical working specification and twelve challenge source hashes
verify. Rules/domain/migrations/finance dependency manifests are unchanged from
88f3559. These are preservation/build checks, separate from passing app tests.
Final documentation, ignore/staged review and local commit follow; no push,
credential repair, cloud deployment or host change is authorized.
