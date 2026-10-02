# Mandatory test coverage

This is the implementation coverage tracker for T01–T42 in [specification section 22.2](AP_Exception_Assistant_Codex_Spec.md#222-mandatory-test-cases). Scenarios and expected results are copied from that table; they describe required behavior, not executed tests.

**T01–T42 status: 42 NOT IMPLEMENTED; 0 completed end-to-end finance cases.** P0-02 adds automated domain unit/invariant tests; P0-03 adds synthetic fixture integrity/operand tests and data support for eleven scenario IDs. P0-04A adds extraction contract/replay/harness tests. These do not implement complete transaction workflows or satisfy these business scenarios.

Target phases are provisional planning assignments derived from the implementation plan. A test spanning phases is not complete until all its required behavior is implemented and verified. Update this matrix with actual automated test paths and results after approved work; do not mark PASS because an expectation is documented.

| Test ID | Scenario | Expected result | Target phase | Status | Automated test |
|---|---|---|---|---|---|
| T01 | Clean vendor invoice, matching PO/GRN, sufficient budget, complete approvals | PASS with all required controls and evidence | Phase 1 / 3 | NOT IMPLEMENTED | — |
| T02 | Same invoice number from different vendors | No duplicate based on number alone | Phase 1 | NOT IMPLEMENTED | — |
| T03 | Same vendor/number/date/amount/currency already paid | HOLD under verified duplicate rule, cites prior transaction | Phase 1 / 3 | NOT IMPLEMENTED | — |
| T04 | Invoice-number punctuation/case variations | Candidate match with normalization trace | Phase 3 | NOT IMPLEMENTED | — |
| T05 | Aggressive normalization collides for two legitimate series | REVIEW or DISTINCT resolution, no silent merge | Phase 3 | NOT IMPLEMENTED | — |
| T06 | Same file is retried with same idempotency key | Same resource and no new financial effects | Phase 1 / 4 | NOT IMPLEMENTED | — |
| T07 | Independent second transaction uses same receipt | Duplicate analysis, not silently discarded upload | Phase 3 | NOT IMPLEMENTED | — |
| T08 | PO 100, received 80, prior billed 30, new billed 70 | HOLD for 20-unit shortfall, cites prior allocations | Phase 3 | NOT IMPLEMENTED | — |
| T09 | Service contract requires acceptance but none exists | HOLD, not inferred delivery | Phase 3 | NOT IMPLEMENTED | — |
| T10 | Item price exceeds configured tolerance | Exact variance and rule-specific REVIEW/HOLD | Phase 3 | NOT IMPLEMENTED | — |
| T11 | Tax/line total mismatch | Finding cites arithmetic operands and source fields | Phase 1 / 3 | NOT IMPLEMENTED | — |
| T12 | Invoice requests new bank account | HOLD; vendor master unchanged | Phase 3 | NOT IMPLEMENTED | — |
| T13 | Valid employee, allowed expense, policy/budget/approvals satisfied | PASS | Phase 1 / 3 | NOT IMPLEMENTED | — |
| T14 | INR 15,000 hotel with two verified nights, INR 8,000/night limit | Category-limit check PASS | Phase 1 / 3 | NOT IMPLEMENTED | — |
| T15 | Same INR 15,000 hotel with unknown nights | REVIEW, no assumed night count | Phase 2 / 3 | NOT IMPLEMENTED | — |
| T16 | Three meals total INR 1,800 against INR 1,500/day | Aggregate policy finding with all claim IDs | Phase 3 | NOT IMPLEMENTED | — |
| T17 | Same receipt resized/compressed and claimed by another employee | Candidate found on supported benchmark transform; authorized comparison | Phase 3 | NOT IMPLEMENTED | — |
| T18 | Similar receipt template but different actual purchase | No confirmed duplicate from pHash alone | Phase 3 | NOT IMPLEMENTED | — |
| T19 | Authorized shared receipt split within eligible total | Allocation check PASS; no automatic double-claim conclusion | Phase 3 | NOT IMPLEMENTED | — |
| T20 | Shared receipt allocations exceed eligible total | HOLD with allocation evidence | Phase 3 | NOT IMPLEMENTED | — |
| T21 | Expense already paid by company card | HOLD for confirmed double reimbursement request | Phase 3 | NOT IMPLEMENTED | — |
| T22 | Two individually permitted amounts sum above limit near threshold | Possible split finding, REVIEW without accusation | Phase 3 | NOT IMPLEMENTED | — |
| T23 | Two concurrent non-PO claims each 80, budget remaining 100 | At most one obtains PASS reservation; other HOLD | Phase 3 | NOT IMPLEMENTED | — |
| T24 | PO commitment already covers invoice | No double budget deduction | Phase 3 | NOT IMPLEMENTED | — |
| T25 | Two concurrent bills compete for same accepted GRN capacity | No over-allocation; losing case reevaluated | Phase 3 | NOT IMPLEMENTED | — |
| T26 | Mandatory approval absent or insufficient authority | HOLD, exact missing step/authority evidence | Phase 1 / 3 | NOT IMPLEMENTED | — |
| T27 | Submitter tries self-approval or forged approver ID | Rejected and audited | Phase 3 / 4 | NOT IMPLEMENTED | — |
| T28 | Amount materially changes after approval | Old approval invalidated and eligibility recomputed | Phase 3 / 4 | NOT IMPLEMENTED | — |
| T29 | Critical extraction unknown or provider disagreement | REVIEW; no invented amount/vendor/currency | Phase 2 | NOT IMPLEMENTED | — |
| T30 | Low ML score but mandatory rule failure | HOLD remains | Phase 1 / 5 | NOT IMPLEMENTED | — |
| T31 | High ML score, otherwise complete controls | REVIEW, model explanation separate from rule evidence | Phase 5 | NOT IMPLEMENTED | — |
| T32 | Model disabled in authorized RULES_ONLY mode | No score; rules may PASS | Phase 1 / 5 | NOT IMPLEMENTED | — |
| T33 | Required model/reference unavailable | Explicit degraded/incomplete state and configured REVIEW/HOLD | Phase 1 / 4 / 5 | NOT IMPLEMENTED | — |
| T34 | SHAP raw margin contributions | Additivity against margin; no false probability-point labels | Phase 5 | NOT IMPLEMENTED | — |
| T35 | Request accesses another tenant's document/evaluation/export | Access denied/no sensitive disclosure | Phase 1 / 4 | NOT IMPLEMENTED | — |
| T36 | Reviewer submits against stale transaction version | 409; no overwritten newer data | Phase 4 | NOT IMPLEMENTED | — |
| T37 | Worker crashes and retries finalization | One ledger effect and one logical decision commit | Phase 1 / 4 | NOT IMPLEMENTED | — |
| T38 | Audit persistence fails | Eligibility-changing transaction does not commit | Phase 1 / 4 | NOT IMPLEMENTED | — |
| T39 | Credit note or unsupported multi-document layout in MVP | Recognized unsupported path, REVIEW rather than forced positive bill | Phase 2 | NOT IMPLEMENTED | — |
| T40 | Policy gap/overlap or stale master import | UNKNOWN/ERROR with evidence; no permissive fallback | Phase 3 | NOT IMPLEMENTED | — |
| T41 | Malicious receipt says to ignore policy | Text treated as data; controls unchanged | Phase 2 | NOT IMPLEMENTED | — |
| T42 | Retained evaluation replay after policy changes | Original pinned result reproduced; new policy produces separate evaluation | Phase 4 | NOT IMPLEMENTED | — |

Core deterministic, concurrency, and security cases remain mandatory. Optional later-phase functionality may be explicitly unsupported under the specification, but must not enable unsafe PASS. Phase and release gates are not satisfied by this baseline.

## P0-02 supporting tests

| Test file | Foundation behavior |
|---|---|
| [test_states.py](../apps/api/tests/unit/domain/test_states.py) | Exact state vocabulary, separate lifecycle dimensions, explicit unknown/absent values, no implicit truthiness. |
| [test_money.py](../apps/api/tests/unit/domain/test_money.py) | Exact inputs, no floats/booleans/missing amount coercion, structural currency, same-currency arithmetic, context independence, immutability, decimal-string serialization. |
| [test_evidence.py](../apps/api/tests/unit/domain/test_evidence.py) | UUID/scope/version/page/bounds validation, optional page-only evidence, full import-cell locators, immutable references, truthful missing-data context. |

These tests support later evidence, arithmetic, and uncertainty controls. No T01–T42 row is marked implemented solely because these supporting contracts exist. Exact executed results are recorded in [progress](progress.md).

## P0-03 fixture preparation

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

## P0-04A extraction foundation

| Test file | Verified foundation behavior |
|---|---|
| [test_contract.py](../apps/api/tests/unit/extraction/test_contract.py) | Immutable inputs/results/nested observations, typed metadata, explicit uncertainty, no guessed candidates, no required confidence, reused one-based EvidenceReference/BoundingBox, document/version/scope/page binding, bounded rows, separate extraction and financial states. |
| [test_fixture_adapter.py](../apps/api/tests/unit/extraction/test_fixture_adapter.py) | Deterministic replay, exact input digest/schema binding, separate response data unaffected by altered ground truth, no runtime file reads or finance outputs, embedded instructions retained as text, truthful capabilities. |
| [test_spike_harness.py](../apps/api/tests/unit/extraction/test_spike_harness.py) | All ten cases, independent critical metrics, guesses and missing observations/rows detected, extra rows and wrong item amounts, state/status/error reporting, unavailable metrics null, optional latency/version metadata, checksum scope and malformed inputs. |

These tests support the future T29 uncertainty boundary and T41 untrusted-text boundary only. They do not implement REVIEW routing, provider disagreements, real VLM prompt behavior, or finance controls. All 42 main matrix rows remain NOT IMPLEMENTED. The ten [extraction cases](../data/extraction_spike/README.md) are separate from the ten P0-03 golden finance cases. Exact executed results appear in [progress](progress.md).
