# Mandatory test coverage

## Final continuous project verification — 2026-10-04

The [final exit](final_project_exit_review.md) records complete invocations and
limits. Final intelligence verification passes **38 tests**; final lifecycle,
scoped-demo/measurement/audit verification passes **16 tests**; actual TypeLLM/GPU
acceptance passes **6 tests**, 348.12 seconds. The real scan reaches PASS across
28 controls only after independent approvals, preserving its original HOLD and
source corrections. Ordinary CI requires neither GPU nor model download.

The complete ordinary suite passes **824**, with **six opt-in GPU skipped**,
3011.36 seconds, exit 0. Final collection is **830**; collection is not a passing
test. Separate focused and hardware runs overlap and are not added into a fake
full-run count. Final live-browser verification passes **39**, with one conditional
retained-provider-failure check skipped after recovery; that actual outage browser
batch previously passed **3**. Native READY/visual three-attempt failure and
idempotent real retry are separately exercised through the actual provider.

New tests verify scope/role/private-template isolation, manifest outcome integrity,
safe measurements, audit rollback, PID reuse/malformed state, model hash/memory
readiness and guarded cleanup. The real `/demo` checks source/report links,
retained/current versions and keyboard/mobile presentation. Repeated preparation
preserves versions/evaluations/audit/capacity. T01–T42 remains **39 passing / one
partial / two data-deferred**; no fabricated classifier/SHAP closes the matrix.

## Current real VLM integration — 2026-10-04

The approved priority override supplements the historical phase results below.
Actual pinned TypeLLM 0.5.1 / Qwen2.5-VL-3B BF16 / SGLang CUDA-12.4 execution
is now verified in six opt-in real integration tests (241.19 s, exit 0): text,
supplied-image secure uploads with and without actual OCR, complete native cheap
routing, an actual refused provider connection and a source-corrected real scan
through immutable canonical facts and the existing finance engine. These tests
assert provider/model/runtime metadata, source hashes/pages/null boxes, retained
observations, cross-tenant denial and critical-uncertainty commit rejection.
They cannot satisfy acceptance using FIXTURE or parser ground truth.

The ordinary CPU extraction/document batch passes **200 tests** (2.30 s, exit 0),
including authenticated gateway bounds/pins, explicit uncertainty, cache failure
isolation, row inventory independent of partial OCR, row-count disagreement,
string/Decimal reconciliation, explicit-currency normalization of printed visual
row amounts, and currency exclusion from quantities/rates.
Normal CI skips the opt-in GPU cases without downloads or startup. The paired
real crop experiment retains 12/12 core row values in both variants.

This strengthens T29/T33's actual extraction uncertainty/outage behavior without
changing the 39/1/2 scenario taxonomy below. It does not implement a supervised
classifier or SHAP: T31/T34 remain data-gated, and supervised T30 remains partial.
Five actual source variants are a smoke, not a representative accuracy dataset.
Final full regression/browser counts are recorded in the [acceptance record](real_vlm_acceptance.md).

This is the implementation coverage tracker for T01–T42 in [specification section 22.2](AP_Exception_Assistant_Codex_Spec.md#222-mandatory-test-cases). Scenarios and expected results are copied from that table; they describe required behavior, not executed tests.

**Current Phase-6 scenario status: 39 IMPLEMENTED + PASSING; 1 PARTIALLY IMPLEMENTED; 2 DEFERRED — SUPERVISED DATA GATE.** Phase 6 preserves these truthful dispositions; it does not fabricate a classifier or SHAP. The preserved Phase-1 gate executed 569 Python tests (488 preserved Phase-0 + 44 pure rules + 37 PostgreSQL integration) and 11 live-browser tests, with zero failures or skips. This is supported synthetic development coverage, not a full production release gate.

The original scenario and expected-result text is preserved below. A partial row means some supporting behavior exists but the complete scenario has not been proved. Target phases retain the original planning assignments; Phase 1 implements only the minimal safe subset. See the [Phase-6 exit review](phase6_exit_review.md) for current gates and limits and the unmodified [Phase-5 review](phase5_exit_review.md) for its retained checkpoint. Phase-2 extraction and its external VLM deferral are preserved.

Test references: **PG** = [PostgreSQL integration](../apps/api/tests/integration/test_vertical_slice.py); **RULES** = [pure rules](../apps/api/tests/test_rules_phase1.py); **UI** = [live browser flows](../apps/web/tests/workspace.spec.ts). Each named test below was executed; unsupported cases are never promoted from fixture availability.

| Test ID | Scenario | Expected result | Target phase | Status | Automated test / remaining scope |
|---|---|---|---|---|---|
| T01 | Clean vendor invoice, matching PO/GRN, sufficient budget, complete approvals | PASS with all required controls and evidence | Phase 1 / 3 | IMPLEMENTED + PASSING | PG `test_real_postgres_golden_end_to_end[vendor/clean]`; UI persisted vendor PASS/evidence/report. |
| T02 | Same invoice number from different vendors | No duplicate based on number alone | Phase 1 | IMPLEMENTED + PASSING | PG `test_same_number_other_vendor_not_duplicate`. |
| T03 | Same vendor/number/date/amount/currency already paid | HOLD under verified duplicate rule, cites prior transaction | Phase 1 / 3 | IMPLEMENTED + PASSING | PG golden `vendor/paid_duplicate`; UI persisted duplicate HOLD/evidence/report. |
| T04 | Invoice-number punctuation/case variations | Candidate match with normalization trace | Phase 3 | IMPLEMENTED + PASSING | PG `test_duplicate_punctuation_resolution_and_version_binding`: separate UUIDs, conservative/aggressive keys, persisted signals, REVIEW then DISTINCT/new evaluation. |
| T05 | Aggressive normalization collides for two legitimate series | REVIEW or DISTINCT resolution, no silent merge | Phase 3 | IMPLEMENTED + PASSING | The punctuation-collision PG test proves REVIEW instead of silent merge and authorized DISTINCT invalidation after material candidate revision; exact DISTINCT/policy replay also passes. |
| T06 | Same file is retried with same idempotency key | Same resource and no new financial effects | Phase 1 / 4 | IMPLEMENTED + PASSING | PG `test_idempotent_create_revision_and_evaluate`, `test_csv_preview_commit_invalid_rows_retained_and_evidence_resolves`; P2 `test_two_step_original_hash_server_keys_replay_and_cross_tenant` and source-commit replay cover actual upload/finalization without duplicate effects. |
| T07 | Independent second transaction uses same receipt | Duplicate analysis, not silently discarded upload | Phase 3 | IMPLEMENTED + PASSING | PG actual JPEG uploads persist independent documents and comparisons; browser two-receipt PDF comparison displays both sources. Repeated bytes are not silently discarded claims. |
| T08 | PO 100, received 80, prior billed 30, new billed 70 | HOLD for 20-unit shortfall, cites prior allocations | Phase 3 | IMPLEMENTED + PASSING | PG golden `vendor/partial_grn`; RULES golden fixture computes HOLD from 50 remaining versus 70 requested and preserves prior allocation evidence. |
| T09 | Service contract requires acceptance but none exists | HOLD, not inferred delivery | Phase 3 | IMPLEMENTED + PASSING | PG authorized service contract: without independent acceptance HOLD; authorized acceptance plus new approved version PASS. |
| T10 | Item price exceeds configured tolerance | Exact variance and rule-specific REVIEW/HOLD | Phase 3 | IMPLEMENTED + PASSING | Pure tolerance MAX/MIN/AND/OR cases compute exact variance and configured disposition; matching emits commercial evidence. Unknown UOM remains incomplete. |
| T11 | Tax/line total mismatch | Finding cites arithmetic operands and source fields | Phase 1 / 3 | IMPLEMENTED + PASSING | PG `test_arithmetic_and_bank_failures_have_persisted_evidence`; RULES missing operands tests. |
| T12 | Invoice requests new bank account | HOLD; vendor master unchanged | Phase 3 | IMPLEMENTED + PASSING | PG `test_arithmetic_and_bank_failures_have_persisted_evidence` verifies VEN-003 failure and unchanged master. |
| T13 | Valid employee, allowed expense, policy/budget/approvals satisfied | PASS | Phase 1 / 3 | IMPLEMENTED + PASSING | PG golden `employee/clean_taxi`; UI persisted employee PASS. |
| T14 | INR 15,000 hotel with two verified nights, INR 8,000/night limit | Category-limit check PASS | Phase 1 / 3 | IMPLEMENTED + PASSING | PG golden `employee/hotel_two_nights`; RULES `test_daily_aggregate_and_nightly_units` asserts 7,500 per night. |
| T15 | Same INR 15,000 hotel with unknown nights | REVIEW, no assumed night count | Phase 2 / 3 | IMPLEMENTED + PASSING | PG golden `employee/hotel_unknown_nights`; RULES explicit UNKNOWN denominator and empty-item abstention. |
| T16 | Three meals total INR 1,800 against INR 1,500/day | Aggregate policy finding with all claim IDs | Phase 3 | IMPLEMENTED + PASSING | PG golden `employee/daily_meals`; RULES `test_daily_aggregate_and_nightly_units` asserts 1,800 and two related claim IDs plus current source. |
| T17 | Same receipt resized/compressed and claimed by another employee | Candidate found on supported benchmark transform; authorized comparison | Phase 3 | IMPLEMENTED + PASSING | Actual resize/JPEG/brightness/minor-blur pHash tests; PG separate employees retrieve indexed <=6-bit candidates from actual uploads with authorized/masked visibility. |
| T18 | Similar receipt template but different actual purchase | No confirmed duplicate from pHash alone | Phase 3 | IMPLEMENTED + PASSING | Actual changed purchase with same image template in pure and PG tests; DUP-003 does not confirm a duplicate solely from pHash. |
| T19 | Authorized shared receipt split within eligible total | Allocation check PASS; no automatic double-claim conclusion | Phase 3 | IMPLEMENTED + PASSING | PG/API/browser source/item/version-bound authorized share, computed receipt capacity and actual ledger allocation; supported complete synthetic expense PASS. |
| T20 | Shared receipt allocations exceed eligible total | HOLD with allocation evidence | Phase 3 | IMPLEMENTED + PASSING | PG cumulative 600 + 800 > 1200 produces EXP-005 FAIL/HOLD with source/prior allocation evidence. |
| T21 | Expense already paid by company card | HOLD for confirmed double reimbursement request | Phase 3 | IMPLEMENTED + PASSING | PG independently confirmed COMPANY_CARD and ADVANCE records produce EXP-006 FAIL/HOLD; requested reimbursement is preserved. Pure offset checks also pass. |
| T22 | Two individually permitted amounts sum above limit near threshold | Possible split finding, REVIEW without accusation | Phase 3 | IMPLEMENTED + PASSING | PG same employee/merchant/day/category/trip near-threshold aggregate produces PAT-001 REVIEW without accusation or duplicate confirmation. |
| T23 | Two concurrent non-PO claims each 80, budget remaining 100 | At most one obtains PASS reservation; other HOLD | Phase 3 | IMPLEMENTED + PASSING | PG `test_concurrent_admission_never_overallocates[BUDGET]` with two real concurrent finalizations; Phase-6 eight-way test admits one 80 claim, holds seven and preserves allocation count on retries. |
| T24 | PO commitment already covers invoice | No double budget deduction | Phase 3 | IMPLEMENTED + PASSING | PG `test_re_evaluation_supersedes_immutable_reports_and_reservations` asserts zero incremental budget against covered PO commitment. |
| T25 | Two concurrent bills compete for same accepted GRN capacity | No over-allocation; losing case reevaluated | Phase 3 | IMPLEMENTED + PASSING | PG `test_concurrent_admission_never_overallocates[GRN]`: one PASS, one HOLD, active capacity remains within 50; Phase-6 eight-way test admits one 30-unit invoice, holds seven and preserves retry effects. |
| T26 | Mandatory approval absent or insufficient authority | HOLD, exact missing step/authority evidence | Phase 1 / 3 | IMPLEMENTED + PASSING | PG golden `vendor/approval_pending`, `test_insufficient_approver_authority_is_persisted_hold`; UI new submissions lack authority and HOLD. |
| T27 | Submitter tries self-approval or forged approver ID | Rejected and audited | Phase 3 / 4 | IMPLEMENTED + PASSING | PG self-approval 403 with immutable REJECTED action/audit; forged actor DTO 422; ordered authenticated roles and authority enforced. Validation rejection does not fabricate an approval action. |
| T28 | Amount materially changes after approval | Old approval invalidated and eligibility recomputed | Phase 3 / 4 | IMPLEMENTED + PASSING | PG `test_revision_invalidates_approved_version_and_capacity` and `test_material_amount_change_requires_new_authority_chain_and_retains_old_approvals`: 50,000→150,000 retains historical authority but requires the fresh Manager/Director chain. |
| T29 | Critical extraction unknown or provider disagreement | REVIEW; no invented amount/vendor/currency | Phase 2 / 4 + real VLM override | IMPLEMENTED + PASSING | Actual native/OCR and opt-in real TypeLLM/VLM uncertainty/source rejection, provider disagreements and row arithmetic abstention; PG missing-total attachment DOC-001 UNKNOWN/REVIEW. Actual real invoice critical ambiguity stays NEEDS_INPUT; no automatic PASS. Representative production quality remains unverified. |
| T30 | Low ML score but mandatory rule failure | HOLD remains | Phase 1 / 5 | PARTIALLY IMPLEMENTED | Actual PostgreSQL `test_actual_low_anomaly_cannot_clear_mandatory_hold` computes score 0 from retained statistical inputs and preserves mandatory HOLD in SHADOW and active anomaly mode; pure combiner and required-outage tests also preserve precedence. Supervised classifier behavior remains deferred because the representative-label gate fails; no complete supervised-ML claim. |
| T31 | High ML score, otherwise complete controls | REVIEW, model explanation separate from rule evidence | Phase 5 | DEFERRED — SUPERVISED DATA GATE | No justified supervised classifier. Actual statistical anomaly escalation PASS→REVIEW is tested in PostgreSQL and browser, with separate factors and unchanged rule results; this does not fabricate the supervised-model scenario. |
| T32 | Model disabled in authorized RULES_ONLY mode | No score; rules may PASS | Phase 1 / 5 | IMPLEMENTED + PASSING | All eight PG golden flows assert NOT_CONFIGURED, no risk_score; eligible clean cases PASS. |
| T33 | Required model/reference unavailable | Explicit degraded/incomplete state and configured REVIEW/HOLD | Phase 1 / 4 / 5 | IMPLEMENTED + PASSING | Required references and extraction fail closed as previously tested. Phase-5 actual RULES_PLUS_MODEL without a provider returns MODEL_UNAVAILABLE/null score and REVIEW for otherwise complete controls. Removing an active private anomaly artifact produces explicit outage/REVIEW; mandatory HOLD remains. Retained replay reports unavailable dependencies rather than empty success. |
| T34 | SHAP raw margin contributions | Additivity against margin; no false probability-point labels | Phase 5 | DEFERRED — SUPERVISED DATA GATE | No justified tree classifier/raw margin exists. SHAP is NOT_APPLICABLE; no static attribution/additivity test or probability bars have been fabricated. |
| T35 | Request accesses another tenant's document/evaluation/export | Access denied/no sensitive disclosure | Phase 1 / 4 | IMPLEMENTED + PASSING | PG `test_auth_scope_and_database_rls` plus P2 intake/finance/mapped-cell tests cover physical originals/pages/field evidence and foreign scope under forced RLS. Phase-4 `test_operational_authorization_scope_export_replay_and_formula_escape` denies cross-scope review/audit/export and unauthorized export/retry/cancellation. |
| T36 | Reviewer submits against stale transaction version | 409; no overwritten newer data | Phase 4 | IMPLEMENTED + PASSING | PG `test_idempotent_create_revision_and_evaluate` rejects stale correction/evaluation. `test_exception_resolution_retains_original_decision_and_two_reviewer_conflict` retains A's review v4→v5 resolution and rejects B's stale write with 409; synchronized competing claims admit one owner. |
| T37 | Worker crashes and retries finalization | One ledger effect and one logical decision commit | Phase 1 / 4 | IMPLEMENTED + PASSING | PG `test_worker_recovers_expired_lease_and_effects_are_idempotent`, `test_retry_pass_has_one_capacity_effect`; P2 `test_expired_document_lease_does_not_duplicate_pages_or_stages` proves stale document finalization rejection. |
| T38 | Audit persistence fails | Eligibility-changing transaction does not commit | Phase 1 / 4 | IMPLEMENTED + PASSING | PG `test_atomic_audit_failure_rolls_back_creation`, `test_audit_failure_blocks_pass_and_all_effects`. |
| T39 | Credit note or unsupported multi-document layout in MVP | Recognized unsupported path, REVIEW rather than forced positive bill | Phase 2 / 4 | IMPLEMENTED + PASSING | PG `test_native_unknown_and_unsupported_credit_route_to_review_without_source_invention` evaluates explicitly identified unsupported CREDIT_NOTE with complete prerequisites to SYS-001 UNKNOWN/REVIEW. P2 uncertain bundle retains NEEDS_INPUT and prevents silent splitting. Credit accounting remains unsupported. |
| T40 | Policy gap/overlap or stale master import | UNKNOWN/ERROR with evidence; no permissive fallback | Phase 3 | IMPLEMENTED + PASSING | Pure gap/overlap/stale cases retain UNKNOWN; staging rejects overlap/band gaps; PG stale activated sources prevent PASS, resolve exact evidence and preserve old pinned PASS. |
| T41 | Malicious receipt says to ignore policy | Text treated as data; controls unchanged | Phase 2 | IMPLEMENTED + PASSING | Actual instruction-bearing synthetic invoice and receipt PDFs: `test_embedded_instructions_have_no_extraction_authority` and PG `test_document_instructions_cannot_clear_approval_or_mutate_master` retain printed amounts, mandatory approval HOLD and unchanged vendor master. Remote prompt safety is separately contract-tested; no live-model claim. |
| T42 | Retained evaluation replay after policy changes | Original pinned result reproduced; new policy produces separate evaluation | Phase 4 | IMPLEMENTED + PASSING | PG exact DISTINCT/policy replay and retained reference replay reproduce original pinned decisions after reference changes; fresh evaluation uses separate current versions. Legacy evaluator is byte-unchanged. |

Core deterministic, concurrency, and security cases remain mandatory. Optional later-phase functionality may be explicitly unsupported under the specification, but must not enable unsafe PASS. Supported Phase-3 deterministic scenarios work; the complete production release, supervised T30 coverage and T31/T34 remain incomplete for the explicit representative-data limitation.

## Historical Phase-0 supporting coverage

The sections below preserve the Phase-0 disposition when those checks ran. Statements that no finance engine existed or all 42 rows were unimplemented describe that historical checkpoint; the Phase-5 matrix above is current.

### P0-02 supporting tests

| Test file | Foundation behavior |
|---|---|
| [test_states.py](../apps/api/tests/unit/domain/test_states.py) | Exact state vocabulary, separate lifecycle dimensions, explicit unknown/absent values, no implicit truthiness. |
| [test_money.py](../apps/api/tests/unit/domain/test_money.py) | Exact inputs, no floats/booleans/missing amount coercion, structural currency, same-currency arithmetic, context independence, immutability, decimal-string serialization. |
| [test_evidence.py](../apps/api/tests/unit/domain/test_evidence.py) | UUID/scope/version/page/bounds validation, optional page-only evidence, full import-cell locators, immutable references, truthful missing-data context. |

These tests support later evidence, arithmetic, and uncertainty controls. No T01–T42 row is marked implemented solely because these supporting contracts exist. Exact executed results are recorded in [progress](progress.md).

### P0-03 fixture preparation

**Fixture prepared; rule not yet implemented.** The main matrix above remains unchanged. This support table maps ten independent golden cases to exactly eleven T IDs. Labels are adjudicated future expectations; fixture-integrity tests do not count as executed business scenarios.

| T ID(s) | Fixture support | Data prepared |
|---|---|---|
| T01, T24 | [clean vendor](../data/golden_cases/vendor/clean.json) | Approved party, PO/GRN quantities, budget commitment coverage, synthetic completed approval actions. Commitment transfer and full-control PASS remain future behavior. |
| T03 | [paid duplicate](../data/golden_cases/vendor/paid_duplicate.json) | Separate UUID obligation with exact paid historical business facts and cited history. |
| T08 | [partial GRN](../data/golden_cases/vendor/partial_grn.json) | 100 ordered, 80 accepted, 30 prior consumed, 70 new, 50 remaining, 20 shortfall; excluded cancelled/reversed allocations. |
| T13 | [clean taxi](../data/golden_cases/employee/clean_taxi.json) | Employee, synthetic receipt facts, policy, budget, Manager action and INR 2,400/day operands. |
| T14 | [two-night hotel](../data/golden_cases/employee/hotel_two_nights.json) | INR 15,000 / 2 nights = 7,500 versus 8,000; matched policy/context. |
| T15 | [unknown hotel nights](../data/golden_cases/employee/hotel_unknown_nights.json) | Explicit null nights/stay dates/per-night amount; UNKNOWN expectation, no guessed denominator. |
| T16 | [daily meals](../data/golden_cases/employee/daily_meals.json) | Paid, pending reserved and current claim IDs: 600 + 600 + 600 = 1,800 versus 1,500. |
| T19 | [shared within](../data/golden_cases/employee/shared_within.json) | Authorized peer 600 + proposed claimant 600 within eligible receipt 1,200. |
| T20 | [shared exceeded](../data/golden_cases/employee/shared_exceeded.json) | Same reference receipt; independent proposal 600 + 800 = 1,400, excess 200. |
| T26 | [approval pending](../data/golden_cases/vendor/approval_pending.json) | Exact absent Department Head step; transaction/policy/snapshot evidence and only the existing Manager action. |

Supporting integrity tests: [reference integrity](../apps/api/tests/fixtures/test_reference_integrity.py), [golden cases](../apps/api/tests/fixtures/test_golden_cases.py), [financial representation](../apps/api/tests/fixtures/test_no_financial_floats.py). They test declared links, dimensions/dates, malformed mutations, evidence pins, deterministic content/checksums and exact operands. No duplicate detector, policy/approval/budget engine or authorization service exists. P0-03 source records are JSON facts only and are not used as extraction responses. The [dataset READMEs](../data/synthetic/README.md) describe scope and limitations. The other 31 T IDs have no dedicated golden case preparation in P0-03.

### P0-04A extraction foundation

| Test file | Verified foundation behavior |
|---|---|
| [test_contract.py](../apps/api/tests/unit/extraction/test_contract.py) | Immutable inputs/results/nested observations, typed metadata, explicit uncertainty, no guessed candidates, no required confidence, reused one-based EvidenceReference/BoundingBox, document/version/scope/page binding, bounded rows, separate extraction and financial states. |
| [test_fixture_adapter.py](../apps/api/tests/unit/extraction/test_fixture_adapter.py) | Deterministic replay, exact input digest/schema binding, separate response data unaffected by altered ground truth, no runtime file reads or finance outputs, embedded instructions retained as text, truthful capabilities. |
| [test_spike_harness.py](../apps/api/tests/unit/extraction/test_spike_harness.py) | All ten cases, independent critical metrics, guesses and missing observations/rows detected, extra rows and wrong item amounts, state/status/error reporting, unavailable metrics null, optional latency/version metadata, checksum scope and malformed inputs. |

These tests support the future T29 uncertainty boundary and T41 untrusted-text boundary only. They do not implement REVIEW routing, provider disagreements, real VLM prompt behavior, or finance controls. All 42 main matrix rows remain NOT IMPLEMENTED. The ten [extraction cases](../data/extraction_spike/README.md) are separate from the ten P0-03 golden finance cases. Exact executed results appear in [progress](progress.md).

### P0-04B source and environment verification

Official-source compatibility research and read-only hardware/package checks are documented in the [plan](typellm_spike_plan.md) and [progress](progress.md). They add no provider tests or financial behavior. The existing 488-test suite remains the regression baseline; all T01–T42 remain NOT IMPLEMENTED. Model accuracy/latency, the proposed 4B image tuple and runtime failure mappings require an explicitly approved P0-04C execution. No test is promoted from fixture agreement to real visual verification.

### Consolidated Phase 0 exit coverage

Phase 0 closes under the latest explicitly approved external-runtime deferral; the [exit review](phase0_exit_review.md) maps AC01–AC20 to supporting foundations and remaining release work. None is claimed as an end-to-end product release pass. All original T01–T42 scenarios, expectations and NOT IMPLEMENTED statuses remain unchanged.

**TEST FIXTURE READY** means synthetic inputs/operands and independent expectations exist. **BUSINESS BEHAVIOR IMPLEMENTED** requires actual production rules/workflows/persistence and meaningful tests. The existing 241 domain + 123 finance-fixture + 124 extraction tests (488 total) verify only their stated local boundaries. No tests were deleted, weakened or relabeled. Architecture acceptance in ADR-0003–0008 does not create integration tests or deployed behavior.

The fixture CLI remains runnable without GPU, cloud or paid provider. Real TypeLLM image behavior/quality, latency/VRAM, field-locator correctness, supported quantization and complete text/visual/tier cascade are **DEFERRED — REQUIRES SUITABLE INFERENCE HOST** plus later provider/preprocessing work, with benchmark requirements in [inference architecture](inference_architecture.md). Historical P0-04C execution recommendations above are superseded by this qualified closure; no failed GPU gate was repeated. No fixture agreement is promoted to real visual accuracy or finance PASS.

### Phase-2 A/B executed checks

The 569-test baseline is preserved. New parser/storage suite (12), PostgreSQL intake suite (4), extraction/normalization/mock-provider/stage/real CPU photo suite (40) pass; full suite is **625 passed, 0 failed, 0 skipped**, 433.02s. Safety, content limits, corruption/encryption/active PDF content, authoritative hashes, one-based pages, actual transforms, raw string finance values, ambiguity/disagreement, RLS and immutable/replayed stage outputs are exercised. These checks support partial T06/T29/T35/T37/T39/T41 work; full scenario status changes await canonical/UI/exit verification. Real VLM metrics remain deferred.

## Phase-2 canonical, mapping and browser checks

Actual-document finance tests cover both branches, approval HOLD/PASS with trusted test provisioning, physical field/page evidence, immutable corrections/new evaluations, fixture-substitution rejection, uncertain segmentation and multi-document links. Mapped CSV/XLSX tests retain cell provenance and reject formulas, numeric money and claimed attachment flags. Ten document-stage integration checks pass after isolating provider configuration from private development settings. Final production-browser gate: **16 passed**, 41.9s, including all original 11 checks plus actual PDF/photo, date corrections, pages/boxes/zoom, quarantine and mobile/loading/error paths. Final full Python aggregate: **641 passed**, 554.98s, zero failures/skips. The final retained table-coverage guard passed its targeted PostgreSQL test (18.38s) after that aggregate. No unexecuted live VLM scenario is promoted.

## Phase-3 executed coverage

Original 641 Python and 16 browser scenarios remain present. Phase 3 adds 63
collected Python cases and seven browser cases. The final aggregate returned exit 0: **704 passed in 1179.01 s**, with no
failures/skips and one upstream Starlette/httpx deprecation warning. The browser command
`npm --prefix apps/web run test:e2e` returned exit 0: **23 passed**. Build and
TypeScript commands returned exit 0. Exact commands/times belong in progress.

Pure checks cover tolerances, UOM, acceptance, returns, repeated demand, Decimal
capacity boundary sweeps, item/trip/month aggregates, offsets, fuzzy/pHash abstention,
mandatory precedence, gap/overlap/staleness and retained original findings.
Real PostgreSQL checks cover activation/snapshots, authority/scope/privacy,
actual PDF-to-PASS in both branches, image retrieval, shared capacity, all-resource
ledger lifecycle, PO commitment transfer, concurrent budget/GRN/duplicate admission,
audit rollback/retries, delegation/preapproval/expiry, stale policy/version authority,
computed exceptional CFO requirements, waivers, replay and resolved evidence.

Browser checks cover matching, budget, approvals, DISTINCT, receipt shares,
waivers, activation, loading/empty/error/role denials and actual paired receipt
pages on laptop/mobile. The original overview test now identifies its retained
seeded transaction by UUID because invoice number is an attribute, not identity.
New expense fixtures use distinct fictional employee/grade/policy dimensions so
repeated browser runs cannot consume one another's daily limits. No original
source fixture semantics or historical test scenarios were weakened.

Remaining owners: T29 needs separately authorized suitable live inference;
T30/T31/T34 need Phase-5 ML; T33 needs Phase-4 dependency/Phase-5 required-model
operations; T39 needs Phase-4 unsupported-input resolution (credit accounting needs
its own approved scope). None can silently permit PASS today.

Final staged review also found and closed a disabled-demo-cookie selection path.
`node --test apps/web/checks/development-identity.mjs` passes its actual server
module boundary test (1 passed); final typecheck/build and all 23 live browser
checks passed again after the repair. This Node check is separate from browser
and Python counts. No new finance or extraction behavior changed.

## Phase-4 executed workflow coverage

[PostgreSQL tests](../apps/api/tests/integration/test_workflow_phase4.py) cover
review-version conflicts, simultaneous ownership, source-linked correction with
actual PDF re-verification and fresh approval, immutable old decisions, cancellation
and exact nonzero compensation, scoped review/audit/export authorization, forged
actors, safe private CSV, pinned PASS/HOLD/REVIEW replay, retry classification and
exhaustion, bounded manual recovery of transient document preprocessing to one READY
document, stale worker rejection, audit rollback, delayed outbox, cancelled
reservation and missing projection repair, retained orphan evidence, critical
source UNKNOWN, unsupported credit and actual required enterprise dependency failure.
New company-payment proof makes current eligibility stale and cannot consume old
reservations. New workflow facts reject SQL mutation. The original Phase-3 suite
retains authority/waiver/self-approval/stale approvals and financial concurrency.

[Browser tests](../apps/web/tests/workflow.spec.ts) use the actual running backend
for claim, source evidence, stale form 409, correction/reassessment, approval and
resolution, retained reports, separate auditor exports, permanent dead-letter
inspection, scoped dependency/reconciliation, filters and error/empty/focus states.
The original receipt flow now uses typed linked-item amount/quantity inputs.
API transaction pagination retains the original three-query batching check.
Exact final commands/counts belong in the exit review and progress after execution.

The final Phase-4 aggregate returned exit 0: **720 passed in 1452.86s**, zero
failures/skips, one upstream deprecation warning. The final actual-backend browser
gate returned exit 0: **27 passed, 1.6m**, no retries. TypeScript, production build,
OpenAPI generation and migration drift checks returned exit 0. These totals preserve
the Phase-3 baseline and include 16 new PostgreSQL workflow tests. Phase 5 is not
implemented; the tracker deliberately remains 38 complete, 2 partial and 2 absent.

## Phase-6 final executed coverage

The current tracker is **39 complete / one partial T30 / two data-deferred T31 and T34**, retaining the Phase-5 supervised gate. Phase-6 full backend execution returned **777 passed, 2550.42 s** before two final enterprise checks were added. The stable final release run returned **21 passed, 152.39 s** (12 pure and nine real PostgreSQL cases); it includes both new checks. Current collection is **779 unique cases** and all are covered by these executions. These are separate runs, not a single 798-test suite. Both runs have one nonfatal upstream Starlette/httpx deprecation, zero failures/skips.

[Pure release boundaries](../apps/api/tests/test_release_boundaries.py) verify RSA/issuer/audience/tenant/client/membership, signature/outage, private Blob integrity and warm-cache missing/outage, fail-closed enterprise configuration and TLS/HTTPS. [Release PostgreSQL cases](../apps/api/tests/integration/test_release_phase6.py) verify future policy selection, immutable snapshots, authorization/revocation/audit rollback, actual on-behalf enterprise membership and eight-way budget/GRN/duplicate/receipt capacity plus retries. Cloud contracts are mocked; PostgreSQL rules/admission/audit/RLS are real. They are not hosted Azure tests.

The final browser suite returns **36 passed, 2.7 min**, real backend and worker, no retries. [Release flows](../apps/web/tests/release.spec.ts) cover small finance navigation, separate Admin future allowance version/history/report preservation and actual document-to-result/audit/report/reload without JSON editing. The development-free presentation check overrides only the UI mode flag and rejects development-template requests; it does not simulate a live SSO deployment. [Loaded viewport checks](../apps/web/tests/visual-release.spec.ts) exercise 1280/1024/390 widths and keyboard focus; actual screenshots were inspected. Existing document, duplicate, policy/approval, review, operations and statistical governance cases remain in the full run.

TypeScript, normal/standalone production build, actual standalone minimal health, fresh migrations/drift, OpenAPI/client, dependency/secret/source checks, Bicep/workflow/approval contracts, actual restart persistence and disposable restore all pass. [Exit review](phase6_exit_review.md) records exact commands and AC01–AC20; [performance](performance_phase6.md) records real local scopes/sample counts. Live VLM/SGLang, hosted cloud/SSO/Blob/restore/rollback, container image builds and representative classifier/SHAP remain deferred rather than promoted from contract tests.

## ClearLedger hardening verification — 2026-10-04

New focused tests cover real positioned PDF labels/cells, actual OCR word geometry,
upright association/original rotated boxes, ambiguity/segmentation/crossing gates,
no inference for complete printed facts, model-only tax abstention, scoped Auto
purpose confirmation/idempotency, authenticated scanner status and bounded scanner
contracts. Existing TypeLLM/worker/normalization and finance invariants remain.

Actual model suite: 6 passed, 264.37 s, exit 0. Layout suite: 11 passed, exit 0.
Complete final invocation/results and repaired failures are recorded in
[ClearLedger hardening](clearledger_hardening.md). Full backend regression,
corrected real-backend browser tests and cold/warm probe are still running at this
checkpoint; their final counts are appended only after execution. No expected
benchmark answer enters extraction and no extraction confidence/model metric is
fabricated. Historical T01–T42 status and previous exit reviews remain unchanged.

The additional worker recovery tests distinguish 55P03/deadlock/serialization and
lost connections from permission/schema/business errors, verify the next cycle
continues, and reject driver/SQL/value logging. A migrated PostgreSQL case verifies
the actual timed-out claim remains QUEUED with zero attempts, then finalizes once
after lock release with required approvals still HOLD. The initial full backend
run was already collected before these cases were added; their result is a separate
execution, never counted as part of that original run.

Final hardening execution: **846 passed / six opt-in skips / 4339.74 s / exit 0**
in the original 852-case full backend run; **14 passed / 18.54 s / exit 0** in the
separate recovery run. Current collection is 866 unique cases. The six opt-in cases
separately returned **six passed / 264.37 s / exit 0** against the actual pinned
TypeLLM/Qwen provider. Do not add these executions into a fictitious single suite.
Final complete browser run: **42 passed / one conditional unconfigured-provider
skip / 5.0 min / exit 0**, without retries. Both roles and actual laptop/phone
screenshots were inspected. Stale HOLD cannot soften to review; stale PASS rows
cannot imply readiness, and retained reports remain checked. Earlier failures,
repaired worker outage and concurrent-write limits are recorded in the hardening
report. One nonfatal upstream Starlette/httpx warning accompanies backend runs;
dependencies are not changed to silence it.

## CL-04/CL-05 extraction continuation

[Validation](clearledger_validation.md) and
[fictional metrics](../data/clearledger_challenge/results-2026-10-04.json)
retain six tuning/six reserved sources, literal/row scores, abstention/corruption,
source hashes and observed failures. Truth enters only post-extraction scoring.
These are not representative invoice accuracy or finance PASS checks.

Final focused suite: **120 passed / 3.26 s / exit 0**. Scoped real PostgreSQL
pipeline/finance/release/intake: **55 passed / 893.66 s / exit 0**. Actual isolated
CPU: **3 passed / 32.07 s / exit 0**, using real CPU sessions, source boxes,
child restart, fallback, tenant rejection and unresolved source-commit blocking.

Actual Qwen suite: **5 passed / 1 failed / 176.63 s / exit 1**, followed by
the affected combination **1 passed / 37.73 s / exit 0**. Its assertion now
requires preserved ambiguity/no canonical total for independent raw spellings;
no application safeguard was weakened. Six distinct cases have passing evidence
across those runs, not a fictitious single six-pass suite. Current cold/first/
resident VLM: 14.974/30.245/30.468 seconds; separate OCR+VLM: 26.158/24.189 seconds,
all preserving unresolved finance facts. Read-only judge verification exits 0
for eight computed current scenarios, eligibility, citations and source history.
Historical full-suite results and T01–T42 are preserved; no new full-backend run
is claimed. Final serial browser checks are recorded after execution.

Final source-form review added explicit native MISSING row observations and
cleared unsupported template amounts/units and eligible nights. Current focused
run: **121 passed / 3.30 s / exit 0**. Post-change migrated source/finance/actual
CPU integration: **20 passed / 301.18 s / exit 0**. The initial mock append created
duplicate fields (**115 passed / five failed**); mocks now replace an observation,
with duplicate rejection preserved.

Complete browser before the form fix: **44 passed / one conditional outage skip /
5.7 min / exit 0**. Final affected source/role/policy/viewport run: **17 passed /
one conditional outage skip / 141.788 s / exit 0**, no retries. Assertions verify
blank unprinted accounting/eligible-night values, measured source rectangles,
retained wrapped-row disagreement, source corrections, vendor/expense finance
submission, both roles and future hotel history/report preservation. Actual
final laptop/phone screenshots were inspected. Typecheck/production build and
source/secret/contracts/locked dependency/preservation checks pass. The conditional
UI skip is not an actual outage pass; real refused-connection behavior is tested
in the model suite. Exact commands and failure history are in the validation report.

## CL-06 table correctness

Final focused extraction/boundaries: **133 passed / 3.49 s / exit 0**. New checks
cover independent table reuse, contiguous multi-page rows, tenant/source binding,
incomplete-table rejection, cross-page coverage uncertainty, exact inverse-EXIF
retry geometry and competing/crossing/invalid telemetry rejection. Earlier
post-change checks passed 94 existing cases, then 131 and 132 with new regressions.
Final zero-call provenance retains native/provider metadata when no VLM executed.

Actual migrated pipeline/source/finance/CPU/concurrency: **24 passed / 367.23 s /
exit 0**. Actual h04 crop recovers quantity 1 with an actual glyph box, retains
missing row accounting, blocks unconfirmed finance commit and preserves child/
fallback boundaries. Three concurrency scenarios verify idempotent capacity
admission. Scope is recorded; no new full-backend run is claimed.

Actual browser: **13 passed / one conditional outage skip / 67.629 s / exit 0**,
no retries/flakiness. Finance/Admin authorization, actual recovered source boxes
and blank unknown values, r07 uncertainty, phone/laptop layouts, computed result
history and future hotel policy audit/report preservation pass; final screenshots
were inspected. Eight read-only judge scenarios pass with all 28 current controls.

Eight fresh reserved variants retain real code/source provenance; 55/55 headers,
96/96 checked row literals and 4/4 required abstentions pass. r07 is excluded from
literal row scoring because its blank quantity/full-table association remains
unresolved. Two absent r02 header fields remain ambiguous. Model raw failures
are retained. The previous holdout results are not rewritten or relabeled unseen.
Actual h04 cold/warm-worker queue is 6.641/6.494 s. Exact commands and measurement/
acceptance limits: [CL-06 correctness](clearledger_table_correctness.md).

## CL-07 unread cells and row identity

Final focused extraction/source boundaries: **144 passed / 4.25 s / exit 0**.
New cases retain single-unread-cell rows/following items and null source facts,
reject competing/multiple-blank geometry, preserve equal items at separate source
positions/pages, stop repeated unassociated vectors/duplicate-region requests,
retain candidates ambiguous with unread remaining slots, and discard retryable
timed-out partial work. Missing observations are never fabricated as a literal
"unresolved" value during row-count disagreement. Existing strict v1/schema limits
and source/scoping checks remain. Finance/security/governance/scanner/worker unit
regressions: **125 passed / 0.85 s / exit 0**.

Actual migrated CPU/pipeline/finance execution: **22 passed / two outdated v2
assertion failures / 378.66 s / exit 1**. All new CPU cases pass. Corrected finance
plus actual GPU: **11 passed / two missing private-source input failures / 235.52 s /
exit 1**; affected private-source rerun **two passed / four deselected / 82.79 s /
exit 0**. All seven finance and six distinct real GPU cases have passing execution,
including both source branches, computed controls, authorized corrections, retained
report/trace version pins and actual provider outage. This is not a fabricated
single fully passing combined run. Initial focused diagnostic/version and import
collection failures are recorded in the report.

Actual browser **20 passed / one conditional outage skip / 180.364 s / exit 0**,
one worker/no retries. Real r07 precise human question/null quantity/unknown box,
three-page equal items, unassigned candidate collapsed default and accessible raw
drill-down, source/corruption/revision/history, Finance/Admin authorization and
future fictional allowance/report audit pass. Laptop/phone source and loaded
Finance/Admin screenshots inspected. Read-only eight-scenario judge gate retains
all 28 current controls/eligibility/citations and original correction HOLD.

New six frozen fictional variants: **42/42 headers, 57/67 readable row literals,
18/18 explicit absent headers, 5/5 canonical abstentions**. q06's ten row literals
remain failed/in the denominator; actual repeated-model stop saves one call and
no candidate becomes canonical. Old held-out evidence remains unchanged; inspected
variants now serve regression, not fresh unseen accuracy. Actual r07 cold/warm
worker queue timings 6.469/6.883 s (warm slower), both NEEDS_INPUT/no finance result.
Source/secret/original preservation and dependency checks pass; no full-suite or
representative production accuracy/performance claim. Commands and limitations:
[CL-07 correctness](clearledger_row_correctness.md).

## CL-08 independent public evaluation and local judge acceptance

Unchanged real local pipeline processed four licensed independently authored
fictional sources: 19 rows/five pages, frozen pixel truth before output. **25/31
header and 72/86 row-field checks**; all failures counted, including wrong p01 tax/
repeated item fields, p04 null-contaminated headers/false shipping and p03 unresolved
normalization. All NEEDS_INPUT/no finance decision; 23/23 absent header canonical
nulls, 14/23 explicit MISSING and five required canonical abstentions. Timings
90.736/55.190/31.523/58.822 s include upload/proxy/durable processing/final polling.
The benchmark exit 0 means measurements completed, not invoices passed accuracy.

`PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_public_evaluation.py -q --tb=short`:
**three passed / 0.03 s / exit 0**. Comparator checks reject punctuation rewriting,
wrong source page, ambiguous row-as-success, invented zero tax and ungrounded dollar
state. No implementation-mirroring finance tests or engine changes were added.

Actual browser **15 passed / one conditional outage skip / 116.310 s / exit 0**,
one worker/zero retries. Role denial, Auto intake, source confirmation/correction/
revision, blocked missing quantity, invoice/expense computed HOLD, corrupt quarantine,
loading/error/phone and Admin effective policy version 44/history/report behavior
pass; latest source/Finance/Admin laptop/phone screens inspected. The skip is not
a new outage drill. Read-only judge: eight current computed scenarios with 28
controls and retained correction HOLD pass. Local API/web/worker/model health READY.

Compileall, whitespace, 382-text-file bounded source scan, cached Gitleaks zero
findings plus one redacted detection probe, original nine hashes/spec and all 26
previous frozen source/snapshot checks pass. Four public source/truth hashes and
eight production hashes match the measured unchanged 0319cf4 code. No new full
backend/browser, representative real-company accuracy, paired before/after or VRAM
claim. Exact commands/method/failures: [CL-08 report](clearledger_independent_validation.md).

## CL-09 source normalization and header/table ownership

Final focused extraction suite **183 passed / 4.41 s / exit 0**: measured European
format sources, unique/ambiguous currencies, mixed/isolated separator rejection,
invalid grouping/source-free locale, stacked/font overlap/left-column/inline
ownership, dense metadata financial anchors, missing/crossing cell abstention,
provider null versus genuine conflict, cross-page known-header reuse, separate
equal rows, unsupported summary tax/charge/zero quarantine and retained schema/
tenant/worker boundaries. Finance/security/governance/duplicate/rules/scanner
regression **125 passed / 0.88 s / exit 0**.

Actual CPU/migrated durable document and both source-to-finance branches **24
passed / 363.03 s / exit 0**. The actual t04 failure was not waived: targeted
diagnosis **one failed / 13.95 s / exit 1** exposed inline Total paired with the
next Tax basis row. Production association and a focused regression were added;
the unchanged original CPU assertion now passes. Existing source/tenant/commit
guards, immutable revisions/reports, approval before clearance and embedded
instruction/master resistance remain tested. No new full backend/all prior GPU
suite claim.

Four final resident real-model development sources **31/31 header, 86/86 row,
23/23 absent canonical null and explicit MISSING, five required abstention checks**;
all 19 rows counted, all NEEDS_INPUT/no finance result. Two initial additional
reserved source-fact probes and final spent regression each **15/15 header, 21/21
row, 12/12 absent canonical null, 11/12 explicit MISSING, four abstentions**. These
share author/template families, not genuinely unseen layout acceptance. Final q06
remains **0/10 rows**, both absent quantity/price canonical null, no unsupported
canonical row; its failed row denominator remains visible. Original manifests/
results stay unchanged and intermediate wrong p01 reads retained.

Initial actual browser **16 passed / one selector failure / one conditional outage
skip / 132.647966 s / exit 1**; affected corrected selector **one passed / 2.7 s /
exit 0**; final actual-source checks **two passed / 4.438873 s / exit 0**, one worker,
no retries/flakiness/skips. Fifteen other earlier cases pass: both role boundaries,
Auto intake/unknowns, computed invoice/expense HOLD, source correction/revision/
report retention, errors/quarantine/mobile and future fictional policy version 46
with effective date/reason/audit/old report. Final source tests use current actual
API documents, no truth/correction injection; measured dense tax, euro raw/canonical,
blocked confirmation, page-two evidence and dollar ambiguity pass. Laptop/phone/
Admin screenshots inspected. No fake combined clean browser count or new outage
drill follows from the skip.

Eight read-only computed judge scenarios with 28 current controls/eligibility/
citations/original correction HOLD pass. Typecheck/compilation/whitespace, 392-file
bounded source scan, cached Gitleaks zero findings/one redacted probe, both finance/
CPU `pip check`, original nine hashes/spec, all 26 prior fictional hashes/40 tracked
historical evidence files and six public originals pass. App/model health READY/
AVAILABLE and approved driver/runtime preserved. Exact commands, actual latency/
whole-device telemetry and remaining corpus/business/Arabic/rotation limits are
in [CL-09 evidence](clearledger_source_repair.md). No additional T01–T42 completion
or production acceptance is inferred.
