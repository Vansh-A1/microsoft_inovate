# ClearLedger local hardening — 2026-10-04

This record supplements the preserved implementation and phase exit reviews.
The delegated task authorizes local fixes, validation and commits, with no push,
public deployment, host/GPU/driver/Docker change, new paid service or external
invoice transmission. Starting checkout: `main`, `81c061d`. The earlier project
overview task was idle and the checkout clean; the separate portfolio checkout
was not touched. See [ADR-0016](adr/0016-clearledger-grounded-intake.md).

## Delivered behavior

Measured PDF spans and OCR words now associate independent label/value columns
and explicit table headings. Repeated headers and page continuations retain their
source pages; crossing/wrapped/incomplete cells abstain. Upright OCR association
and original-image evidence coordinates are separate, fixing EXIF-rotated receipt
association. Legacy labeled/pipe extraction remains intact. Explicit dates and
currencies still go through the existing conservative normalizer.

The router skips inference when printed core facts and rows are covered; absent
charges, tax semantics, missing currency or uncertain dates remain unresolved.
Incomplete coverage uses the same pinned TypeLLM/Qwen service and existing bounded
page/ruled-row crops. Incomplete headers are independently reread; an OCR/model
invoice-number disagreement stays ambiguous. Model-only tax treatment cannot
become a canonical accounting fact. No confidence, zero tax, discount, FX rate,
model score or payable decision is invented.

Auto intake derives a purpose suggestion from printed document identities. When
unclear, it stops after safety preprocessing and asks for an audited type choice.
The confirmation is scoped, role checked, generation checked and idempotent. The
original AUTO request remains in immutable upload audit. Originals/pages survive;
no schema or used migration changes. Type selection is separate from mandatory
source confirmation and finance evaluation.

Normal UI is ClearLedger, with a separate Finance Workspace and Admin Console.
PASS/REVIEW/HOLD display as **Ready for processing / Needs review / On hold**;
stale eligibility requests fresh screening. A stale PASS cannot display readiness;
an outstanding HOLD keeps its stronger On hold label while requiring refresh.
Transaction rows cannot present an ineligible historical PASS as ready; dashboard
aggregates/filters explicitly describe recorded screenings rather than current
readiness. Retained reports and raw screening decisions stay unchanged.
Plain reasons/next steps lead, and
rule IDs, JSON, UUIDs and provider details remain expandable. Source observations
display uncertainty, measured citations and deterministic normalization traces.
Actual job stages drive progress; there is no simulated percentage.

`NEXT_PUBLIC_PRODUCT_NAME` configures the presentation name (default ClearLedger).
It is a build-time public string, not a tenant or security setting. Local entry
uses existing server-configured fictional identities and HttpOnly sessions; main
Finance/policy workspaces lead and other sample roles are expandable. Production
entry targets the existing Microsoft identity integration; real Entra/SSO has
not been provisioned or validated. Local roles are not production authentication.

Admin forms group allowances, approval hierarchy, employees, vendors and budgets
within existing permissions. Policy change previews show old/new allowance,
currency, unit, effective period, reason and new version. Editing a validated form
invalidates its draft before activation. History/audit and historical evaluations
remain intact. Synthetic provenance stays visibly fictional, even after versioning.
Missing business policies cannot authorize processing.

An operator-provided local ClamAV executable can be connected through
`AP_MALWARE_SCANNER_EXECUTABLE`. No engine or definitions were installed. Scanner
status is disclosed by authenticated intake capabilities and Admin health.
NOT_CONFIGURED, UNAVAILABLE and CONFIGURED_UNVERIFIED never mean CLEAN. Required
scanning blocks until an actual successful scan; timeouts/errors/skipped files
remain failures. See the [official clamscan documentation](https://docs.clamav.net/manual/Usage/Scanning.html).

Browser validation exposed a real recovery defect: a PostgreSQL 55P03 claim timeout
escaped the worker loop and stopped API/worker/web through their supervisor. The
scoped cycle now contains only known transient database errors, logs an allowlisted
stage/reason and backs off one second. Rollback, durable leases, maximum attempts
and financial finalization remain unchanged; unknown database/business failures
are not hidden. A controlled read-only 6.5-second scoped lock in the actual owned
app confirms the same process survives with API/web READY and worker RUNNING,
logging only `worker_backoff / DATABASE_CONTENTION / FINANCE`. No database facts,
infrastructure settings or credentials change in that probe.

## Frozen extraction benchmark

Three lawful synthetic documents and expectations were frozen before extraction
changes. The last layout was reserved while developing against the first two.
It is a held-out *synthetic layout*, not representative external accuracy.
Expectations are compared only after inference and never enter the prompts/router.
The harness uses the production processor/router/normalizer and stores raw runs
under ignored `runtime/clearledger/`. Run:

```bash
.venv/bin/python scripts/benchmark/clearledger.py --freeze
.venv/bin/python scripts/benchmark/clearledger.py --label baseline
.venv/bin/python scripts/benchmark/clearledger.py --label after-final-development --split development
.venv/bin/python scripts/benchmark/clearledger.py --label after-held-out --split held_out
```

The baseline was executed on the starting implementation; running `--label baseline`
now measures current code and must not be presented as the old baseline.

| Layout | Baseline seconds | After seconds | Headers before → after | Row values before → after |
|---|---:|---:|---:|---:|
| Independent native columns, nine-column table | 74.093 | 0.249 | 3/5 → 5/5 | 15/18 → 18/18 |
| Scanned raster, compact four-column table | 74.154 | 0.390 | 2/5 → 5/5 | 6/8 → 8/8 |
| Reserved two-page Courier continuation | 114.216 | 0.565 | 3/5 → 5/5 | 16/18 → 18/18 |

All after samples avoid VLM. These are processor/render/storage/router/normalizer
wall times, excluding upload/database queue/UI polling. The model was already
resident for baseline; these are **not cold-start times**. Baseline whole-device
VRAM peaks were 13,999 / 13,947 / 14,149 MiB; after 13,173 / 13,173 / 13,178 MiB
still include the resident unused model and other GPU processes. They do not
establish per-request allocated VRAM or production capacity.

Source SHA-256:

| Layout | SHA-256 |
|---|---|
| columns | `8ef4a952bdbf3742c2467c377ce0b46a3d4e44e2bfd799100e4e808384f551b7` |
| scan | `b9975ee6fbcf3e86f3fadd5772a178f1940e5d03f2aabc48acc5d1ab9d80710c` |
| continuation | `ec284c860c6f45fa4058739e2a8afc1585fd5896d153ad875856447ac787fbb5` |

The compact scan lacks explicit accounting fields. Its 5/5 and 8/8 checked values
do **not** make it ready for processing: absent tax treatment/charges and partial
row semantics remain unresolved. No missing field is scored as a correct zero.

## Actual model verification

The supplied invoice remains private in `/tmp`; its original hash is retained in
the private probe output. Real opt-in tests assert TypeLLM 0.5.1, Qwen2.5-VL-3B
revision `66285546d2b821cf421d4f5eb2576359d3770cd3`, BF16 and cache isolation.
The same Python 3.12 serving/client environments and unchanged driver 550.120
remain isolated from finance Python 3.13. No dependency upgrade or model switch.

Final real-model test: **6 passed, 264.37 s, exit 0**:

```bash
AP_RUN_REAL_VLM=1 AP_VLM_PRIMARY_DOCUMENT=/tmp/codex-clipboard-696b68c8-3134-4cd4-95f6-ce656aa86785.png PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_real_vlm.py -q --tb=short
```

The supplied invoice's date/currency remain unresolved. OCR can read `us.001`
while vision reads `US-001`; neither overrides the other. Its visible three rows
match the independently inspected source. Unsupported tax semantics remain
AMBIGUOUS, not canonical. The synthetic real scan reaches a finance HOLD after
explicit source corrections, then PASS only after independent existing approvals;
its original HOLD and extraction remain retained. Native processing avoids a
configured VLM, and an actual refused connection is retryable with no fake draft.

An initial real-model run had **4 passed / 2 failed**, exposing the uncorroborated
partial OCR header and a test that attempted tax acceptance without independent
source confirmation. Both were corrected without a layout exception or expected
answer entering inference. An OCR regression run had **29 passed / 1 failed**;
fixing upright/original coordinate separation restored the existing receipt. A
subsequent **30 passed / 1 failed** run only exposed an exact float-coordinate test
assertion; it now uses coordinate tolerance. Final layout checks: **11 passed**.

Cold/warm probe, exit 0:

```bash
.venv/bin/python scripts/benchmark/clearledger_probe.py /tmp/codex-clipboard-696b68c8-3134-4cd4-95f6-ce656aa86785.png --restart-owned-model
```

| Work | Seconds | Peak whole-device MiB | Actual result |
|---|---:|---:|---|
| Owned service cold restart/startup | 15.048 | 11,604 | Pinned service AVAILABLE; verification/weight loading included |
| First extraction after startup | 34.814 | 12,638 | OCR + VLM, five calls, three rows, 28 unresolved findings |
| Next resident extraction | 33.101 | 12,624 | OCR + VLM, five calls, three rows, 28 unresolved findings |

Invoice number, date, currency and tax treatment remain AMBIGUOUS on both
requests. Printed row quantity/unit price/amount match 1/100/100, 2/15/30 and
3/5/15. Missing row tax/net/gross and charges stay missing; no finance decision is
asserted. Addresses remain unconfirmed model observations and can be incomplete.
The live app/provider recovered through their owned lifecycle with the same pins.
No old-code cold probe exists, so this is **not a cold before/after speedup claim**.
The historical 37.7-second result has a different measurement context and is not
used as a paired control here. Raw/private evidence: `runtime/clearledger/cold-warm-probe.json`.

## Demonstration acceptance and remaining risks

For the October 7, 21:00 Asia/Kolkata deadline, the core local journeys are:

1. Open Finance through local entry, upload an unfamiliar native invoice with Auto,
   inspect measured source facts and missing fields, then follow actual review steps.
2. Inspect a scanned invoice that truly invokes TypeLLM/Qwen; retain conflicting
   glyphs, uncertain currency/date and unsupported tax for source correction.
3. Resolve a matched-record exception using PO/GRN, duplicate or approval evidence,
   showing the exact shortfall/action and immutable report/audit.
4. In Admin, propose a fictional hotel INR 8,000→9,000 per eligible night with an
   effective date/reason; activate a validated new version and retain old reports.
5. Show unavailable extraction/scanner status honestly, with authorized retry and
   native independence rather than a substituted fixture result.

These scenarios run actual domain logic. An extracted document is not automatically
source verified, a matching budget does not supply approval authority, and a small
model's apparent confidence cannot override controls. There is no payment execution.

Remaining external gates: representative lawful independently adjudicated invoice
layouts, stronger approved inference provider, commercial model licensing, real
organization policies/masters, real identity and scanner acceptance, and deployment
inputs. Wrapped/irregular tables and very degraded scans can still need manual
review. This benchmark is not a universal accuracy/speed promise. No calibrated
confidence, classifier, SHAP, production pilot or guaranteed competition result.

## Final validation

Final local verification is complete. Backend, additional recovery, real-model,
cold/warm and final browser executions are recorded separately below.
Supporting private artifacts are ignored; no push or deployment follows.

Final full browser run, exit 0: **42 passed / one conditional provider-outage skip,
5.0 min**, no automatic retries:

```bash
PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH" npm --prefix apps/web run test:e2e
```

The skipped UI scenario expects an unconfigured visual provider; the accepted
provider is actually configured/available. It is not labeled passed. Actual refused
connection, retryability and absence of a fake finance draft are independently
covered in the six passing real-model integration cases. The complete browser run
covers source intake/correction/history, matching/approvals, governed stale
screening/rollback, future policy version/history, server roles, CSRF, loading/error/
empty states and 1280/1024/390 layouts. Actual final Finance and Admin screenshots
were inspected. TypeScript and the final production build both exit 0.

Full backend regression, exit 0: **846 passed / 6 opt-in real-model skips / one
upstream warning, 4339.74 s (72m19.74s)**:

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q --tb=short
```

The six skipped real-model cases are the six actual passing cases recorded above;
they are not counted as passes in this default run. Fourteen recovery cases were
added after the 852-case full invocation was collected. Their separate execution
passes, exit 0: **14 passed / one upstream warning, 18.54 s**:

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_clearledger_worker.py apps/api/tests/integration/test_clearledger_worker_recovery.py -q --tb=short
```

This includes a fresh migrated PostgreSQL schema, a real 5-second lock timeout,
zero attempts on the rolled-back claim, one later finalization and unchanged
approval HOLD/idempotent evaluation. Current collection is **866 cases, 0.59 s**;
collection is not an application test pass. Initial collection exposed duplicate
test module basenames; the migrated recovery module now has a unique name.

Fast final extraction regression, exit 0: **94 passed, 2.64 s**, one upstream
Starlette/httpx deprecation warning; no dependency change:

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_clearledger_layout.py apps/api/tests/test_clearledger_scanner.py apps/api/tests/test_vlm_integration_contract.py apps/api/tests/test_extraction_documents.py apps/api/tests/test_documents_phase2.py -q --tb=short
```

Migration drift (`PYTHONPATH=apps/api .venv/bin/alembic -c apps/api/alembic.ini check`),
OpenAPI comparison (`.venv/bin/python scripts/release/contracts.py`), source scan
(`.venv/bin/python scripts/release/source_security.py`), redacted Gitleaks/probe
(`.venv/bin/python scripts/release/secret_scan.py`) all exit 0. Artifact contracts
pass using the existing isolated `runtime/release-tools/bin/python
scripts/release/check_artifacts.py`; the finance environment correctly lacks its
YAML-only dependency, so running that tool with finance Python initially exited 1.
No package was installed to repair it.

All 9/23/11/15 original/synthetic/extraction/document manifest entries verify;
`cmp` confirms the working specification equals the original. `git diff --exit-code
81c061d -- apps/api/app/rules apps/api/app/domain apps/api/migrations` exits 0.
These preservation/document checks are separate from passing application tests.

Browser validation history is retained rather than described as passing:

| Run | Actual outcome | Disposition |
|---|---|---|
| Initial full UI | 39 passed / 3 failed / 1 conditional skip, 4.8 min, exit 1 | Sample link assertion and phone dropdown overflow fixed |
| Affected views | 14 passed / 1 failed / 1 conditional skip, 1.6 min, exit 1 | Total assertion now targets the actual field row with normalization evidence |
| Full role workflows | 40 passed / 2 failed / 1 conditional skip, 4.9 min, exit 1 | Helpers now wait for the admin landing after a role switch |
| Role/navigation retest | 18 passed / 1 conditional skip, 3.3 min, exit 0 | All affected role-switching checks passed |
| Duplicate-badge removal | 5 passed / 5 failed / 1 interrupted / 32 not run, 3.8 min, exit 130 | Stopped after finding remaining selectors aimed at the removed badge; assertions now target the current result, with immutable reports still checked |
| Final UI before worker fix | 15 passed / 28 failed, 3.6 min, exit 1 | Actual lock-timeout worker exit caused remaining connection failures; scoped worker recovery implemented |
| Serial UI after recovery | 41 passed / 1 failed / 1 conditional skip, 6.2 min, exit 1 | Stale mandatory HOLD displayed as Needs review; now retains On hold and still requires a fresh screening |

The final successful full browser execution above follows the implemented fixes.
No automatic Playwright retries are enabled.

The subsequent overlapping run after worker repair was stopped: **6 passed / 9
failed / 1 interrupted / 27 not run, 3.9 min, exit 130**. The app stayed READY and
emitted safe contention events, but fresh-schema regression coincided with slow
database writes and UI mutations exceeded existing timeouts. Read-only PostgreSQL
activity showed CREATE TABLE waiting on DataFileImmediateSync. Browser checks run
separately after that suite; no host/database setting or test timeout is changed
to mask the observation. This is a measured local load limitation, not a proven
root cause or production capacity claim.
