# Mandatory test coverage

This is the implementation coverage tracker for T01–T42 in [specification section 22.2](AP_Exception_Assistant_Codex_Spec.md#222-mandatory-test-cases). Scenarios and expected results are copied from that table; they describe required behavior, not executed tests.

**Phase-1 status: 21 IMPLEMENTED + PASSING; 11 PARTIALLY IMPLEMENTED; 10 NOT IMPLEMENTED.** The final gate executed 569 Python tests (488 preserved Phase-0 + 44 pure rules + 37 PostgreSQL integration) and 11 live-browser tests, with zero failures or skips. This is supported synthetic development coverage, not a full production release gate.

The original scenario and expected-result text is preserved below. A partial row means some supporting behavior exists but the complete scenario has not been proved. Target phases retain the original planning assignments; Phase 1 implements only the minimal safe subset. See the [exit review](phase1_exit_review.md) for modes, rules, commands and limitations.

Test references: **PG** = [PostgreSQL integration](../apps/api/tests/integration/test_vertical_slice.py); **RULES** = [pure rules](../apps/api/tests/test_rules_phase1.py); **UI** = [live browser flows](../apps/web/tests/workspace.spec.ts). Each named test below was executed; unsupported cases are never promoted from fixture availability.

| Test ID | Scenario | Expected result | Target phase | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
|---|---|---|---|---|---|
| T01 | Clean vendor invoice, matching PO/GRN, sufficient budget, complete approvals | PASS with all required controls and evidence | Phase 1 / 3 | IMPLEMENTED + PASSING | PG `test_real_postgres_golden_end_to_end[vendor/clean]`; UI persisted vendor PASS/evidence/report. |
| T02 | Same invoice number from different vendors | No duplicate based on number alone | Phase 1 | IMPLEMENTED + PASSING | PG `test_same_number_other_vendor_not_duplicate`. |
| T03 | Same vendor/number/date/amount/currency already paid | HOLD under verified duplicate rule, cites prior transaction | Phase 1 / 3 | IMPLEMENTED + PASSING | PG golden `vendor/paid_duplicate`; UI persisted duplicate HOLD/evidence/report. |
| T04 | Invoice-number punctuation/case variations | Candidate match with normalization trace | Phase 3 | PARTIALLY IMPLEMENTED | Conservative invoice-number key exists; candidate workflow and retained normalization trace are deferred. |
| T05 | Aggressive normalization collides for two legitimate series | REVIEW or DISTINCT resolution, no silent merge | Phase 3 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T06 | Same file is retried with same idempotency key | Same resource and no new financial effects | Phase 1 / 4 | IMPLEMENTED + PASSING | PG `test_idempotent_create_revision_and_evaluate`, `test_csv_preview_commit_invalid_rows_retained_and_evidence_resolves` (identical import bytes/key/commit reuse). |
| T07 | Independent second transaction uses same receipt | Duplicate analysis, not silently discarded upload | Phase 3 | PARTIALLY IMPLEMENTED | Structured source-document ID reuse is guarded; independent uploaded receipt/file comparison and full duplicate analysis are deferred. |
| T08 | PO 100, received 80, prior billed 30, new billed 70 | HOLD for 20-unit shortfall, cites prior allocations | Phase 3 | IMPLEMENTED + PASSING | PG golden `vendor/partial_grn`; RULES golden fixture computes HOLD from 50 remaining versus 70 requested and preserves prior allocation evidence. |
| T09 | Service contract requires acceptance but none exists | HOLD, not inferred delivery | Phase 3 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T10 | Item price exceeds configured tolerance | Exact variance and rule-specific REVIEW/HOLD | Phase 3 | PARTIALLY IMPLEMENTED | PO-003 computes term variance/tolerance; complete over-tolerance behavior across configured policies lacks a dedicated scenario test. |
| T11 | Tax/line total mismatch | Finding cites arithmetic operands and source fields | Phase 1 / 3 | IMPLEMENTED + PASSING | PG `test_arithmetic_and_bank_failures_have_persisted_evidence`; RULES missing operands tests. |
| T12 | Invoice requests new bank account | HOLD; vendor master unchanged | Phase 3 | IMPLEMENTED + PASSING | PG `test_arithmetic_and_bank_failures_have_persisted_evidence` verifies VEN-003 failure and unchanged master. |
| T13 | Valid employee, allowed expense, policy/budget/approvals satisfied | PASS | Phase 1 / 3 | IMPLEMENTED + PASSING | PG golden `employee/clean_taxi`; UI persisted employee PASS. |
| T14 | INR 15,000 hotel with two verified nights, INR 8,000/night limit | Category-limit check PASS | Phase 1 / 3 | IMPLEMENTED + PASSING | PG golden `employee/hotel_two_nights`; RULES `test_daily_aggregate_and_nightly_units` asserts 7,500 per night. |
| T15 | Same INR 15,000 hotel with unknown nights | REVIEW, no assumed night count | Phase 2 / 3 | IMPLEMENTED + PASSING | PG golden `employee/hotel_unknown_nights`; RULES explicit UNKNOWN denominator and empty-item abstention. |
| T16 | Three meals total INR 1,800 against INR 1,500/day | Aggregate policy finding with all claim IDs | Phase 3 | IMPLEMENTED + PASSING | PG golden `employee/daily_meals`; RULES `test_daily_aggregate_and_nightly_units` asserts 1,800 and two related claim IDs plus current source. |
| T17 | Same receipt resized/compressed and claimed by another employee | Candidate found on supported benchmark transform; authorized comparison | Phase 3 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T18 | Similar receipt template but different actual purchase | No confirmed duplicate from pHash alone | Phase 3 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T19 | Authorized shared receipt split within eligible total | Allocation check PASS; no automatic double-claim conclusion | Phase 3 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T20 | Shared receipt allocations exceed eligible total | HOLD with allocation evidence | Phase 3 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T21 | Expense already paid by company card | HOLD for confirmed double reimbursement request | Phase 3 | PARTIALLY IMPLEMENTED | Explicit company-paid/advance arithmetic exists; independent card/payment ledger proof of double reimbursement is deferred. |
| T22 | Two individually permitted amounts sum above limit near threshold | Possible split finding, REVIEW without accusation | Phase 3 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T23 | Two concurrent non-PO claims each 80, budget remaining 100 | At most one obtains PASS reservation; other HOLD | Phase 3 | IMPLEMENTED + PASSING | PG `test_concurrent_admission_never_overallocates[BUDGET]` with two real concurrent finalizations. |
| T24 | PO commitment already covers invoice | No double budget deduction | Phase 3 | IMPLEMENTED + PASSING | PG `test_re_evaluation_supersedes_immutable_reports_and_reservations` asserts zero incremental budget against covered PO commitment. |
| T25 | Two concurrent bills compete for same accepted GRN capacity | No over-allocation; losing case reevaluated | Phase 3 | IMPLEMENTED + PASSING | PG `test_concurrent_admission_never_overallocates[GRN]`: one PASS, one HOLD, active capacity remains within 50. |
| T26 | Mandatory approval absent or insufficient authority | HOLD, exact missing step/authority evidence | Phase 1 / 3 | IMPLEMENTED + PASSING | PG golden `vendor/approval_pending`, `test_insufficient_approver_authority_is_persisted_hold`; UI new submissions lack authority and HOLD. |
| T27 | Submitter tries self-approval or forged approver ID | Rejected and audited | Phase 3 / 4 | PARTIALLY IMPLEMENTED | RULES `test_no_approval_authority_intake` and PG role tests reject forged authority; rejected-attempt audit/human approval workflow is deferred. |
| T28 | Amount materially changes after approval | Old approval invalidated and eligibility recomputed | Phase 3 / 4 | IMPLEMENTED + PASSING | PG `test_revision_invalidates_approved_version_and_capacity`. |
| T29 | Critical extraction unknown or provider disagreement | REVIEW; no invented amount/vendor/currency | Phase 2 | PARTIALLY IMPLEMENTED | Required null fields route unresolved rules away from PASS (RULES missing tests); live extraction/provider disagreement is deferred. |
| T30 | Low ML score but mandatory rule failure | HOLD remains | Phase 1 / 5 | PARTIALLY IMPLEMENTED | RULES `test_precedence` proves mandatory HOLD dominance; no ML score path exists to exercise the complete scenario. |
| T31 | High ML score, otherwise complete controls | REVIEW, model explanation separate from rule evidence | Phase 5 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T32 | Model disabled in authorized RULES_ONLY mode | No score; rules may PASS | Phase 1 / 5 | IMPLEMENTED + PASSING | All eight PG golden flows assert NOT_CONFIGURED, no risk_score; eligible clean cases PASS. |
| T33 | Required model/reference unavailable | Explicit degraded/incomplete state and configured REVIEW/HOLD | Phase 1 / 4 / 5 | PARTIALLY IMPLEMENTED | Missing required reference/context fails closed and HTTP database readiness is explicit; a required-model mode/outage scenario is deferred. |
| T34 | SHAP raw margin contributions | Additivity against margin; no false probability-point labels | Phase 5 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T35 | Request accesses another tenant's document/evaluation/export | Access denied/no sensitive disclosure | Phase 1 / 4 | IMPLEMENTED + PASSING | PG `test_auth_scope_and_database_rls` covers source/evaluation/report, foreign tenant, foreign entity and raw non-superuser RLS. |
| T36 | Reviewer submits against stale transaction version | 409; no overwritten newer data | Phase 4 | IMPLEMENTED + PASSING | PG `test_idempotent_create_revision_and_evaluate` asserts stale correction and evaluation both 409. |
| T37 | Worker crashes and retries finalization | One ledger effect and one logical decision commit | Phase 1 / 4 | IMPLEMENTED + PASSING | PG `test_worker_recovers_expired_lease_and_effects_are_idempotent`, `test_retry_pass_has_one_capacity_effect`. |
| T38 | Audit persistence fails | Eligibility-changing transaction does not commit | Phase 1 / 4 | IMPLEMENTED + PASSING | PG `test_atomic_audit_failure_rolls_back_creation`, `test_audit_failure_blocks_pass_and_all_effects`. |
| T39 | Credit note or unsupported multi-document layout in MVP | Recognized unsupported path, REVIEW rather than forced positive bill | Phase 2 | PARTIALLY IMPLEMENTED | RULES `test_credit_currency_and_scope_incomplete_abstain` covers recognized unsupported credit type; multi-document ingestion is deferred. |
| T40 | Policy gap/overlap or stale master import | UNKNOWN/ERROR with evidence; no permissive fallback | Phase 3 | PARTIALLY IMPLEMENTED | Effective version/band selection and missing dependencies exist; stale import activation and complete gap/overlap scenarios are deferred. |
| T41 | Malicious receipt says to ignore policy | Text treated as data; controls unchanged | Phase 2 | NOT IMPLEMENTED | Later-phase behavior; no executed complete scenario. |
| T42 | Retained evaluation replay after policy changes | Original pinned result reproduced; new policy produces separate evaluation | Phase 4 | PARTIALLY IMPLEMENTED | PG `test_persisted_pinned_inputs_reproduce_evaluation` and supersession tests verify current pinned replay; changed-policy and legacy-engine replay are deferred. |

Core deterministic, concurrency, and security cases remain mandatory. Optional later-phase functionality may be explicitly unsupported under the specification, but must not enable unsafe PASS. The Phase-1 local exit is satisfied; the full release gate remains incomplete.

## Historical Phase-0 supporting coverage

The sections below preserve the Phase-0 disposition when those checks ran. Statements that no finance engine existed or all 42 rows were unimplemented describe that historical checkpoint; the Phase-1 matrix above is current.

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
