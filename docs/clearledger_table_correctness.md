# ClearLedger table correctness — CL-06, 2026-10-04

Phase-6/final local continuation under the continuous hardening approval. This
bounded milestone fixes two spent table regressions without replacing the finance
engine, changing accepted GPU/TypeLLM dependencies or redesigning the interface.
The [previous benchmark](clearledger_validation.md) and its frozen sources/results
remain unchanged. h01/h04 are now development/regression cases, never newly unseen.

## Diagnosis and implementation

Actual h01 PDF spans already mapped both rows correctly. Unrecognized printed
Seller/Invoice ID/Issue date labels triggered a full VLM header/inventory/row read;
the second model row then spoiled the independent native observations. Common
explicit label aliases now map geometrically. A complete independent per-page
table can also survive a header-only VLM fallback with its raw values and measured
source boxes intact. Diagnostics or incomplete core columns prevent reuse.
`reused_tables` in extraction-routing-v4 records actual page/count/reason. Source
scope/version and row budgets are validated; indices remain contiguous across
pages. An unread page's uncertain inventory cannot be hidden by another page's rows.
If independent page reuse leaves only a document-level conflict and makes no
model call, provenance stays NATIVE_TEXT/LOCAL_OCR and CONFIGURED_NOT_NEEDED;
configured inference is never reported as executed.

Actual h04 OCR detections omitted the visibly printed single glyph 1 in row two's
quantity column. The model subsequently repeated row one and disagreed with OCR
inventory. The existing CPU model reads that glyph when supplied a measured row
crop at 2× scale. New bounded retries require unique printed headings, a measured
description and all but one numeric column, with no crossing geometry. At most
three retries consume the original page deadline; each scaled crop is capped at
four million pixels. Multiple absent cells and unowned text cannot request a retry.

The child crops in memory and maps each actual detector polygon back through the
exact crop offset/scale, then the existing inverse EXIF transform. Only one wholly
contained, vertically associated new detection may fill the missing cell.
Competing, crossing or unrelated detections abstain. Crop extents are routing
metadata, never field boxes. Word-alignment approximations are not used as precise
evidence; existing detector regions remain authoritative. Raw source facts are
not inferred from arithmetic, tax totals or confidence.

This is a small-glyph/routing failure, not evidence requiring RapidTable or
PPStructure. No heavier stack or new dependency was installed. ADR-0017's pinned
optional CPU environment, exact model hashes and CPU provider attestation remain.
Its existing model-attribution/commercial acceptance gap remains open.

## Spent regressions

| Case | Previous CPU pipeline s | Current s | Checked row literals | VLM calls |
|---|---:|---:|---:|---:|
| h01 landscape | 45.792 | 0.224 | 4/8 → 8/8 | 4 → 0 |
| h04 wrapped Times scan | 13.762 | 2.985 | 0/8 → 8/8 | 3 → 0 |

Current h04 uses one real CPU crop retry; its first separate cold-child probe took
3.362 seconds. All six spent holdout regressions retain their printed facts and
required date/currency/identity abstentions. All readable sources remain NEEDS_INPUT
with no finance decision. Unknown row accounting fields still require source review.

## Newly reserved variants

Eight original lawful fictional variants were frozen before tuning on db1095f.
The unchanged baseline output was sealed until tuning and boundary checks ended.
The [new manifest and synthetic metrics](../data/clearledger_reserved/README.md)
retain source/code hashes and the exact observed outcomes. Shared vocabulary and
synthetic provenance do not establish customer-distribution independence.

| Variant | Before s | After s | Checked row literals before → after | VLM calls |
|---|---:|---:|---:|---:|
| r01 changed landscape | 67.309 | 0.517 | 4/12 → 12/12 | 5 → 0 |
| r02 unfamiliar Trading entity header | 64.121 | 29.873 | 4/12 → 12/12 | 5 → 1 |
| r03 three-page reordered continuation | 0.357 | 0.361 | 12/12 → 12/12 | 0 → 0 |
| r04 Times wrapped scan | 1.513 | 1.526 | 12/12 → 12/12 | 0 → 0 |
| r05 Helvetica wrapped scan | 1.487 | 1.466 | 12/12 → 12/12 | 0 → 0 |
| r06 Courier scan, ambiguous date/currency | 1.584 | 1.575 | 12/12 → 12/12 | 0 → 0 |
| r07 genuinely absent quantity | 16.810 | 18.467 | excluded; required abstention passes | 4 → 4 |
| r08 conflicting invoice identities | 0.298 | 0.302 | 24/24 → 24/24 | 0 → 0 |

Checked headers remain 55/55; checked row literals improve 80/96 → 96/96.
Explicit MISSING absent headers improve 20/24 → 22/24. All four required canonical
abstentions pass. The two remaining absent-field mismatches are r02 payment-account
provider null and unsupported tax-exclusive inference, both AMBIGUOUS/noncanonical.
No checked absent header becomes PRESENT. The source prints no tax basis; the model
candidate is preserved for review rather than silently promoted or discarded.

r07 is a material failure, not a successful complete extraction. Its source prints
three rows but leaves the second quantity blank. The retry produces no cell read.
The VLM repeats descriptions/quantities and sometimes substitutes a total for a
row amount; inventory disagreement makes those row candidates AMBIGUOUS and
noncanonical. The intended blank quantity stays unresolved. No row literals on
this case are included in the 96-value denominator, and no aggregate hallucination
rate is inferred from its absent row-scoring telemetry. Its failed crop added about
1.486 seconds CPU inference and did not remove the four VLM calls. These reserved
failures were inspected after tuning and have not been tuned away as unseen success.

Measurements are single pipeline executions with a resident unchanged Qwen model
on a shared host. Upload/queue/UI/human time is excluded. Whole-device peaks are
14,613 MiB before and 14,667 MiB after, including other processes; no VRAM improvement
is claimed. Current CPU first-visual startup and subsequent resident execution are
included as observed, not a general cold/warm distribution. The final conservative
cross-page inventory and zero-call provenance guards were added after these
measurements; no measured case contains the states they guard. Source-code hashes
identify that boundary.

Executed benchmark commands (exit 0; fresh labels required for future runs):

```bash
.venv/bin/python scripts/benchmark/clearledger_reserved.py --freeze
.venv/bin/python scripts/benchmark/clearledger_reserved.py --label baseline
.venv/bin/python scripts/benchmark/clearledger_challenge.py --label cl06-regression --split holdout --case h04 --rapid-production
.venv/bin/python scripts/benchmark/clearledger_challenge.py --label cl06-regressions-final --split holdout --rapid-production
.venv/bin/python scripts/benchmark/clearledger_reserved.py --label after
```

## Minimum human confirmations and acceptance limits

- For r07, confirm all three row associations against the preserved source; the
  model candidates cannot be used. Obtain an authorized independent source for
  the blank Desk index tabs quantity, or leave it unknown. Equal amount/unit price
  is not source proof of quantity one.
- For r06, confirm the intended ISO currency and date convention for printed `$`
  and `04/05/2026`; neither is selected silently.
- For r08, confirm document segmentation/which invoice is being processed before
  any source verification or finance submission.
- For r02 and the scans, resolve unprinted tax treatment and required row accounting
  semantics using a source statement or an approved versioned business policy.
  A model's tax-exclusive candidate and demo defaults do not establish real policy.

No stronger provider is configured or authorized for external transmission.
The current fallback is explicit human review. A lawful, representative 40–60
invoice corpus with independently adjudicated truth and new reserved layouts remains
an acceptance input; no public corpus availability or production pilot is invented.

## Screenshot identity and timing clarification

The earlier 5.021 cold-worker / 4.282 warm-worker seconds refer specifically to
`data/clearledger_challenge/t04.png`, the fictional ruled scan uploaded as
VENDOR_INVOICE through the actual loopback web proxy/API and durable workers.
They exclude browser rendering, human confirmation and finance approvals. They
are not private East Repair invoice timing or cold GPU weight-loading measurements.

The three saved fictional screenshots have these verified Library identities,
all version 0. No private invoice image was uploaded:

| Screenshot | Library file ID | Uploaded file ID |
|---|---|---|
| phase6-loaded-finance-laptop.png | libfile_d82fa8d4878c8191b82f80bc82e30e45 | file_00000000ce1c8210baae4fbfad74b253 |
| phase6-loaded-admin-laptop.png | libfile_784bf251e26c8191a38fe0b2e8ac05a1 | file_0000000009388246a999561a98957723 |
| phase6-loaded-finance-mobile.png | libfile_26efa3504fe08191a404bf0bbbfc0a4c | file_00000000a8ac81f495845b73f1ebe52f |

The temporary phone gallery remains closed. Normal app/inference services remain
loopback only. No public deployment, push, credential repair or host change occurred.

## Verification

Final focused extraction/response/source-scope regression: **133 passed, 3.49 s,
exit 0**, with one retained Starlette/httpx deprecation warning. This includes
complete-table reuse, contiguous multi-page row indices, cross-tenant rejection,
cross-page uncertain coverage, bounded missing-cell routing, exact rotated source
coordinates and competing/crossing/invalid telemetry rejection.

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_cpu_ocr.py apps/api/tests/test_clearledger_layout.py apps/api/tests/test_clearledger_grounding.py apps/api/tests/test_extraction_documents.py apps/api/tests/test_vlm_integration_contract.py apps/api/tests/test_documents_phase2.py -q --tb=short
```

The prior post-change run passed 131 cases in 3.45 s; the added final coverage
guard accounts for the next case. A 132-pass/3.50 s check preceded the final
zero-call provenance regression. Before new regressions, 94 existing focused
cases passed in 2.36 s. These are scoped checks; no new full-backend run is claimed.

Actual migrated integration: **24 passed, 367.23 s, exit 0**. These exercise
durable uploads/pipeline, both finance branches, correction/history, untrusted
document instructions, source-confirmation rejection, actual CPU boxes/recovery/
fallback and three real concurrent idempotent admission scenarios. No database
durability, constraints or financial checks are weakened.

```bash
AP_RUN_CPU_OCR=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_document_pipeline.py apps/api/tests/integration/test_document_finance.py apps/api/tests/integration/test_cpu_ocr_live.py apps/api/tests/integration/test_finance_phase3.py::test_phase3_real_concurrent_admission_and_idempotent_finalize -q --tb=short
```

Actual browser: **13 passed, one conditional outage skip, 67.629 s, exit 0**,
one worker/no retries/no unexpected or flaky tests. Actual h04 recovered-source
and blank-accounting checks pass on laptop/phone; r07 remains blank/unresolved
with visible coverage uncertainty. Both roles/authorization, native invoice
submission/results, future fictional INR 8000→9000 hotel version/effective date/
actor/reason/audit and retained historical reports pass. Final source phone/laptop
and Admin screenshots were visually inspected. The conditional absent outage
fixture is a skip, not a passing outage drill. No UI redesign or naming change.

```bash
AP_RUN_CPU_OCR_BROWSER=1 PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH" npm --prefix apps/web run test:e2e -- tests/cpu-ocr.spec.ts tests/clearledger.spec.ts tests/release.spec.ts tests/hackathon.spec.ts tests/visual-release.spec.ts
```

After an app-only owned-supervisor restart, actual h04 upload-to-final-state was
**6.641 s cold worker / 6.494 s warm worker** (upload 0.419/0.290 s), both NEEDS_INPUT,
no error or finance decision, with actual stages through FINALIZE. Polling is 0.5 s;
browser/human/approval time is excluded. This is a different source from the earlier
t04 5.021/4.282 s measurements and has no old-code paired queue baseline.

```bash
.venv/bin/python scripts/benchmark/clearledger_async.py --label cl06-cold-worker --case h04
.venv/bin/python scripts/benchmark/clearledger_async.py --label cl06-warm-worker --case h04
.venv/bin/python scripts/release/judge_verify.py
```

The eight-scenario read-only judge check exits 0 with current 28-control decisions,
eligibility, exception citations, verified actual VLM history and retained original
correction HOLD. Clean actual-source PASS, paid-duplicate HOLD and future policy
history remain computed by the preserved finance engine. Actual r02/r07 outputs
verify Qwen revision 66285546d2b821cf421d4f5eb2576359d3770cd3, BF16, TypeLLM 0.5.1
and SGLang 0.4.6.post5; the isolated client and serving Transformers versions stay
separate. The current driver remains 550.120 on RTX 2000 Ada 16 GB.

Compileall and whitespace checks exit 0; all nine original input hashes, exact
working-spec copy and all 20 frozen source hashes pass. Finance domain, migrations
and finance requirements have no diff from db1095f. The existing local Gitleaks
8.30.1 scan finds zero source secrets and its redacted deliberate probe finds one.
The final source-security check scans 366 text files with zero forbidden artifacts
or configured credential-pattern findings. Invalid labels and zero-source benchmark
requests are rejected explicitly. App/model listeners
are loopback; port 3001 is absent. No extra model/table-stack installation, cloud
transmission, identity/scanner provisioning, host change, push or deployment.
