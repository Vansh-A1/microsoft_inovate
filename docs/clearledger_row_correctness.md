# ClearLedger unread-cell and row correctness — CL-07, 2026-10-04

Phase-6/final local continuation. The bounded goal is to stop ungrounded row
repetition and preserve incomplete source rows without replacing the finance
engine. Accepted model/runtime pins, host configuration, Decimal arithmetic,
source confirmation, tenant/entity authorization and historical reports remain.
No dependency, migration, driver, Docker, UI redesign, name or publication change.

## Diagnosis and correction

On the spent r07 source, OCR reads the description, price and amount around a
genuinely blank quantity. The parser previously stopped at that row and discarded
the following readable item. Its partial inventory forced full-page VLM item
generation; the model repeated/misassigned rows and all row candidates became
ambiguous. A quantity must never be recovered by dividing amount by price.

The measured layout parser now retains a row with exactly one unread numeric core
cell under unique printed headings, with a measured description and at least
three readable core cells. It preserves following rows and wrapped descriptions.
Crossing geometry, conflicting OCR/native values, multiple missing cells and
unowned text still fail the gate. A missing read has raw/canonical null, source
page context and no invented field box. Its diagnostic explicitly distinguishes
failure to read from proof of a blank versus illegible source. The reviewer gets
the actual line/description/page question. CPU crop retries stay bounded by the
existing deadline; an unresolved retry cannot supply a quantity.

Sufficient measured rows can stop model generation and route to human input.
This is extraction sufficiency, not complete accounting or finance clearance.
An independent partial table can also survive a header-only fallback, with its
unread cells and uncertain table status retained. Per-page reuse validates scope,
version and row budgets. A later unread page cannot inherit another page's coverage.

For remaining visual generation, row identity comes from document/version/scope,
page and an actual measured region. Equal values or identical crop bytes do not
prove duplicate items. Distinct measured regions and distinct pages preserve
legitimate identical items. If the same actual region is supplied twice, the
second request is avoided, the prior candidate is quarantined and the remaining
inventory slots stay explicitly unread. If equal model vectors lack distinct
measured row regions, both are retained as ambiguous candidates, further row
generation stops, and unread slots contain no manufactured values. This does not
assert that the source rows are duplicates. Existing call/row/token/deadline limits
still apply; timeout/retry cannot publish a partial run as complete.

Unassigned candidates have no canonical quantities or amounts. Their raw values
remain accessible in a collapsed reviewer drill-down, accompanied by a plain
source-association question. The default review does not display the repeated
raw values as printed facts. No source crop is promoted to a field box.
`document-normalizer-v3` retains observation diagnostics and these findings;
new evaluations pin v3 while old v2 drafts/reports remain unchanged.

## Frozen six-case evidence

Six original fictional variants were frozen on 7cc473e before tuning; the
baseline was sealed until the corrections and focused checks ended. These share
fictional vocabulary and are not a representative independently adjudicated
customer corpus. Sources/previous results are unchanged. Public code/source hashes
and exact checks are in [the new corpus](../data/clearledger_row_identity/README.md).

| Variant | Before s | After s | Readable row checks | VLM calls |
|---|---:|---:|---:|---:|
| q01 Times scan, blank quantity | 20.939 | 3.707 | 0/11 → 11/11 | 4 → 0 |
| q02 Helvetica native, blank quantity | 39.026 | 0.227 | 0/11 → 11/11 | 4 → 0 |
| q03 Courier scan, three legitimate equal items | 1.587 | 1.593 | 12/12 → 12/12 | 0 → 0 |
| q04 three-page native, equal items | 0.367 | 0.380 | 12/12 → 12/12 | 0 → 0 |
| q05 Helvetica scan, blank price | 20.265 | 2.867 | 0/11 → 11/11 | 4 → 0 |
| q06 native, two blank numeric cells | 39.109 | 28.927 | 0/10 → 0/10 | 4 → 3 |

Headers remain 42/42, readable row literals improve 24/67→57/67, explicit absent
header checks remain 18/18, and all five required canonical abstentions pass.
All six outcomes remain NEEDS_INPUT with no finance decision. No checked absent
row/header becomes PRESENT or canonical. The q06 failure is retained in the
denominator: two model rows repeat the first item's values without row geometry;
both remain ambiguous, the third slot is unread, and none is accepted. The actual
`REPEATED_UNASSOCIATED_CANDIDATES` stop saves one row-generation call. This case
still requires source row reconstruction and authorized missing facts.

These single pipeline timings include preprocessing/CPU startup and exclude
upload/database queue/browser rendering/human review. GPU weights stayed resident;
there was no cold-weight load or concurrency benchmark. First OCR child
initialization was 0.2665 s before and 0.2729 s after; later scan requests reuse
that child (the repeated initialization metric describes the same process).
q03 is a subsequent warm CPU request, not a paired cold/warm read of q01. Whole-
device peak was 15,220→15,167 MiB across the runs and includes other processes;
no per-request VRAM improvement is claimed. OCR recognition/crop time did not
materially improve; the gains come from avoiding unhelpful VLM generation.

The spent r07 development check now retains the three measured descriptions,
price/amount facts and unread quantity, in 3.267 pipeline seconds versus the
previous 18.467 seconds, with 4→0 VLM calls. Its historical zero-row scoring
denominator remains untouched; this is a new development diagnosis, not revised
holdout accuracy. Broader accuracy needs the [external acceptance inputs](clearledger_acceptance_inputs.md).

Actual r07 loopback upload/proxy/durable-worker/poll-to-result measurements were
6.469 s with a freshly restarted owned application worker and 6.883 s on its next
warm request (upload portions 0.227/0.135 s). Both keep NEEDS_INPUT, no processing
error, no VLM call and no finance decision. The first worker reports 0.2691 s OCR
initialization; the same value on the warm request refers to that resident child.
The warm observation is slower; queue/polling/shared-host variability matters.
These are single observations at 0.5 s polling granularity, excluding human review,
browser rendering and approvals, not weight-loading latency or a throughput SLA.

## Verification

Final focused source/extraction command:

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_clearledger_row_identity.py apps/api/tests/test_cpu_ocr.py apps/api/tests/test_clearledger_layout.py apps/api/tests/test_clearledger_grounding.py apps/api/tests/test_extraction_documents.py apps/api/tests/test_vlm_integration_contract.py apps/api/tests/test_documents_phase2.py -q --tb=short
```

**144 passed / 4.25 s / exit 0**. Tests cover unread actual cells, equal items on
different positions/pages, conflicting observations, reused source regions, model
repetition, bounded stopping, source scope/version and retryable timeout. Earlier
checks had 131 pass/two outdated diagnostic/version assertion failures (3.52 s,
exit 1). The first new-test collection failed (exit 2) because the schema registry
had not been initialized in that standalone test import order; initialize the
existing Base registry as other scoped worker tests do. No application/finance
import architecture was changed. Two subsequent 144-case runs passed before the
final stronger missing-state preservation assertion.

Financial/business/security regression:

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_rules_phase1.py apps/api/tests/test_finance_controls_unit.py apps/api/tests/test_duplicates_phase3.py apps/api/tests/test_risk_phase5.py apps/api/tests/test_release_boundaries.py apps/api/tests/test_clearledger_scanner.py apps/api/tests/test_clearledger_worker.py -q --tb=short
```

**125 passed / 0.85 s / exit 0**. No financial engine, policy fixture, migration or
dependency manifest was modified. Missing-policy/UNKNOWN controls, Decimal sums,
duplicate/capacity behavior, rules/anomaly governance, scanner failure boundaries
and durable work use the existing tested implementation.

Actual migrated CPU/source/pipeline/finance command:

```bash
AP_RUN_CPU_OCR=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_cpu_ocr_live.py apps/api/tests/integration/test_document_pipeline.py apps/api/tests/integration/test_document_finance.py -q --tb=short
```

**22 passed / two version-assertion failures / 378.66 s / exit 1**. New actual CPU
cases retain three measured r07 rows and its precise missing-quantity question,
deny an uncorrected canonical commit, and preserve three equal items at separate
scan positions and separate PDF pages. Existing child restart/fallback, isolated
source access and migrated worker/idempotency behavior pass. The two finance tests
still expected v2 despite deliberately new v3 traces; expectations were updated
while retaining report/draft/trace version equality, original evidence access,
HOLD before approvals and computed PASS after trusted test approvals.

Corrected finance plus actual pinned GPU command:

```bash
AP_RUN_REAL_VLM=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_document_finance.py apps/api/tests/integration/test_real_vlm.py -q --tb=short
AP_RUN_REAL_VLM=1 AP_VLM_PRIMARY_DOCUMENT=<authorized-local-source-path> PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_real_vlm.py -k real_primary_upload -q --tb=short
```

The first is **11 passed / two missing-input failures / 235.52 s / exit 1**: the
two private-invoice cases failed before extraction because this invocation omitted
their required source-path environment variable. The affected rerun is **two
passed / four deselected / 82.79 s / exit 0**. All seven finance cases and all six
distinct GPU cases thus have passing executions; there is no fabricated single
13-pass run. The previously authorized private invoice remains local/ignored.
Its actual row triples are preserved; ambiguous date/currency, unsupported tax
and partial address still do not justify canonical clearance or broad accuracy.
TypeLLM/model/revision/BF16/cache provenance remains actual and unchanged. The
first run's four passing GPU cases include the real scan/source-correction/finance
flow and provider-outage behavior. The retained Starlette/httpx deprecation warning
does not justify a dependency upgrade under this task.

Frozen measured commands (exit 0):

```bash
.venv/bin/python scripts/benchmark/clearledger_rows.py --freeze
.venv/bin/python scripts/benchmark/clearledger_rows.py --label baseline
.venv/bin/python scripts/benchmark/clearledger_rows.py --label after
.venv/bin/python scripts/benchmark/clearledger_reserved.py --label cl07-development --case r07
.venv/bin/python scripts/benchmark/clearledger_async.py --label cl07-cold-worker --case r07
.venv/bin/python scripts/benchmark/clearledger_async.py --label cl07-warm-worker --case r07
```

Each baseline/after is six actual local pipeline executions, the development run
is one, and cold/warm are two actual durable uploads. Baseline requires the old
7cc473e code; this is a record of executed commands, not an instruction to obtain
the original baseline with new code. No baseline output or frozen source changed.

Actual running-browser command (from apps/web, using the existing project Node
24.21.0 PATH):

```bash
AP_RUN_CPU_OCR_BROWSER=1 npm run test:e2e -- tests/cpu-ocr.spec.ts tests/documents.spec.ts tests/clearledger.spec.ts tests/release.spec.ts tests/hackathon.spec.ts tests/visual-release.spec.ts
```

**20 passed / one conditional outage skip / 180.364 s / exit 0**, one worker,
zero retries. The skip is absence of the optional persisted UI outage example,
not a passing outage drill; the actual provider integration outage check passed.
Actual r07 shows the line-2/page-1 quantity question, blank correction and no field
box. Actual q04 retains three identical items on distinct pages. Actual q06 keeps
unassigned quantity null and candidate text collapsed by default, with truthful
raw drill-down and no invented source box. Laptop/390px source screenshots and
loaded Finance/Admin screenshots were visually inspected; no page-width overflow.
Existing source revision/history, corrupt upload/quarantine/loading/error states,
role denial, report/audit and future fictional hotel policy history pass. The
future hotel INR 8000→9000 version is 42 in this run, with reason/effective date,
audit and prior report preserved; it is still fictional configuration.

`npm --prefix apps/web run build` and `run typecheck` exit 0 using the existing
runtime. The app-only supervisor reload validates PID/ownership/start identity
and keeps separate model weights resident. `.venv/bin/python scripts/demo.py
health` is READY. `.venv/bin/python scripts/release/judge_verify.py` exits 0:
eight computed local scenarios retain 28 controls, current eligibility/citations
and the original correction HOLD, including clean PASS and paid-duplicate HOLD.
These checks do not relabel unresolved benchmark sources as finance PASS.

Compilation and `git diff --check` exit 0. All nine original input hashes,
byte-identical working specification and all 26 frozen fictional source hashes
match. `.venv/bin/python scripts/release/source_security.py` scans 374 text files
with no forbidden artifacts/configured credential patterns; the existing pinned
`scripts/release/secret_scan.py` reports zero Gitleaks 8.30.1 findings and one
successful redacted synthetic detection probe, both exit 0. Finance Python remains
3.13.11, finance/isolated-CPU `pip check` both pass. GPU reports RTX 2000 Ada,
driver 550.120, 16,380 MiB unchanged; accepted BF16 serving/client pins remain.
Temporary phone port 3001 stays closed. No full backend/browser suite rerun or
production security/performance certification is claimed for this scoped change.

## Remaining acceptance

The functioning fictional local demo is separate from production acceptance.
Independent lawful invoices with adjudicated truth, business-approved policies,
real organization identity/role mappings, actual malware engine/definitions,
commercial model attribution and approved release inputs remain outstanding.
No stronger/external provider is silently selected. An unprinted quantity, tax
treatment, zero charge, FX or missing allowance policy stays unknown until an
authorized source correction or configuration exists. Supervised risk training
still lacks the mandatory representative adjudicated labels.

No push, public deployment, private invoice export or host/runtime upgrade occurred.
