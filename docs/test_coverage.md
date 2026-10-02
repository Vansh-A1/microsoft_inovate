# Mandatory test coverage

This is the implementation coverage tracker for T01–T42 in [specification section 22.2](AP_Exception_Assistant_Codex_Spec.md#222-mandatory-test-cases). Scenarios and expected results are copied from that table; they describe required behavior, not executed tests.

**Baseline: 42 NOT IMPLEMENTED; 0 automated cases; no application test suite exists.** Documentation verification does not change these statuses.

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
