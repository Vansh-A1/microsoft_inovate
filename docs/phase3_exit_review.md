# Phase-3 exit review — Complete finance matching and controls

Disposition: **COMPLETE LOCALLY, WITH PRESERVED ENTERPRISE-RUNTIME DEFERRAL**. P3-01–P3-06 were directly approved
in one continuous implementation pass on 2026-10-03. This review is updated only
from executed checks. Phase 4 has not begun. Publication is a separate gate.

## Implemented tasks

| Task | Result |
|---|---|
| P3-01 | Stage/validate/activate immutable source versions, source/period/relationship/currency/money/band checks, pinned snapshots, exact/curated identity and ambiguous fuzzy candidates. |
| P3-02 | PO priority and authorized contract routes, ordered/accepted/net returns/prior allocations, grouped demand, ceilings, approved UOM, explicit tolerance operator and independent authorized service acceptance. |
| P3-03 | Indexed union retrieval, named business/fuzzy/file/pHash signals, candidate classifications, actual page fingerprints, both-version reviewer dispositions and side-by-side facts/pages. |
| P3-04 | Exact effective policy dimensions, configured purpose/attendees/class/merchant/window/preapproval/item/night/day/trip/month, source-bound shared capacity, independent company-card/advance protection and split REVIEW. |
| P3-05 | Append-only budget/resource lifecycle, commitment transfer without double deduction, all-resource compensating events, scope-locked fresh finalization, rollback on audit failure and bounded/idempotent workers. |
| P3-06 | Computed ordered authority requirements, authenticated role/master/ceiling/currency/scope/delegation/SoD, rejection audit, terminal decline, stale material/policy authority and explicit immutable waivers retaining original results. |

The original pure evaluator remains byte-unchanged. Explicitly activated
`rules-p3-v1` selects 28 controls at rule version 3.0.0; retained original contexts
still use their original 20 controls. The current policy does not rewrite older
evaluations. [ADR-0011](adr/0011-versioned-finance-controls.md) records the boundary.
Finance risk remains RULES_ONLY / NOT_CONFIGURED with no score.

## Computed acceptance paths

| Input/control | Executed result |
|---|---|
| Complete clean vendor + real ordered authority | PASS; actual reservations/report/evidence persisted. |
| Actual native invoice PDF → verified canonical → PO/GRN/budget → authority | PASS with DOCUMENT_DERIVED facts and physical evidence. |
| Actual receipt PDF → verified canonical → employee/policy/budget → authority | PASS with actual source UUID/pages. |
| Verified active duplicate | HOLD; explicit authorized DISTINCT can produce a separate reevaluation after version checks. |
| Punctuation/aggressive-key collision | REVIEW; no automatic identity binding or merge. |
| 100 ordered, 80 accepted, 30 prior billed, new 70 | HOLD; 50 remaining and 20 shortfall. |
| Price delta 15, absolute 20, relative 1% | MAX/OR PASS; MIN/AND FAIL under their explicit operators. |
| Incompatible UOM without approved conversion | UNKNOWN/HOLD; approved factor produces exact comparable quantities. |
| Contract without required service acceptance | HOLD; independent authorized accepted milestone can satisfy it. |
| Returned/reversed receipt quantities | Net accepted capacity decreases; cumulative requests cannot exceed it. |
| Changed payment-account instructions | HOLD; immutable vendor/account master untouched. |
| Missing approval | HOLD; factual source confirmation is not approval. |
| Clean expense / verified hotel denominator | PASS / 15,000 ÷ 2 = 7,500 within 8,000 per night. |
| Unknown hotel nights | REVIEW; no guessed divisor. |
| Daily meals 600 + 600 + 600 > 1,500 | REVIEW with all aggregation evidence. |
| Authorized shared receipt 600 + 600 <= 1,200 | Allocation control PASS; complete supported expense PASS. |
| Shared receipt 600 + 800 > 1,200 | HOLD with exact linked amounts. |
| Independently confirmed company card or advance requested again | HOLD; requested/computed amounts remain separate. |
| Two 2,400 claims near 2,500 threshold, combined 4,800 | PAT-001 REVIEW, without allegation. |
| Explicit permitted waiver | Original FAIL remains; separate disposition affects the new decision. |

## Concurrency and invariants

Actual PostgreSQL tests synchronize independent workers: two 80 requests against
100 budget, competing GRN demand against 50 capacity, and identical independent
submissions. At most one obtains eligible admission; budget/GRN capacity is never
overallocated. Finalization rechecks references, comparisons, approvals and capacity
under one scope lock before atomically writing allocations, decision, report and
audit. Failed audit persistence rolls everything back. Retry/finalization does not
duplicate decisions or financial effects. Current own unconsumed reservation is
excluded, while own consumed exposure prevents fresh double admission.

Allocation lifecycle transitions every resource owned by one evaluation together.
Cancellation releases RESERVED capacity, rejects consumed release, and cancels its
queued work; explicit reversal restores consumed exposure. PO-covered amounts
transfer open commitment to consumption rather than deducting twice. Real concurrent
worker claim/approval mutation verifies the shared lock order. Claim SQLState
40P01/40001 handling is bounded, not endless.

## Authorization, evidence and UI

API authorization is authoritative: tenant/entity filtering, forced RLS, current
version, role, effective master/delegation authority, sequence, currency/ceiling
and SoD are enforced. Self-approval persists a rejected action/audit; forged actor
fields fail strict DTO validation. Own-claim readers cannot fetch peers' cases,
sources or master catalog; comparison/report/evidence peer facts are masked.
Ordinary approval cannot waive mandatory vendor/bank/duplicate/capacity controls.
Waivers require explicit configured role, current rule/version/evidence and expiry.

Every new finding resolves scoped immutable facts: commercial/delivery/prior
allocation, policy/master, budget ledger, approval, share, comparison and actual
document page/cell evidence. Source coordinates remain physical or null. JSON/HTML
reports retain original control findings, calculations, signals, approval states,
waivers and next actions; no LLM explanation or invented confidence is used.

Actual browser tests and inspected screenshots cover matching, budgets, ordered
approval identities, duplicate field/signals/DISTINCT, receipt share, waiver,
reference stage/validate/activate, original document corrections/boxes/pages,
loading/empty/error/authorization and laptop/mobile layout. Paired uploaded receipt
pages render together, with explicit page-level evidence when no box is available.
The synthetic identity picker is enabled only by the loopback supervisor; tokens
remain private/server-side and clients cannot manufacture roles.

## Database and migrations

Head: `0005_finance`. New tables: reference_batches, reference_activations,
finance_allocations, allocation_events, budget_events, duplicate_comparisons,
duplicate_resolutions, image_fingerprints, fingerprint_bands, receipt_shares,
approval_requests, approval_actions, waivers. Total: 47 business tables plus Alembic.
All business tables enforce forced tenant/entity RLS. Twelve new fact tables reject
ORM/direct-SQL mutation; staging source fields are protected while workflow state
is a projection. Scoped FK/unique/check constraints retain precision and logical
operation identity. Polymorphic receipt/resource UUIDs are service-validated within
scope rather than asserted to have one fictitious FK target.

Frozen additive DDL preserves old migrations. Actual development 0004→0005 upgrade
retained the original case/doc/report data (also exercised by old browser cases).
Fresh isolated upgrade, base downgrade and re-upgrade execute in the migration
test. `alembic current` reports head; `alembic check` reports no new operations.
No meaningful database or history was reset.

## Measured performance

Command: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/benchmark/finance_phase3.py`,
exit 0. The disposable PostgreSQL schema contains 10,000 generated histories plus
five originals, 200 structured transactions, 20 vendors, 30 employees, 50 PO/GRN
lines and 3 cost centers. FX is explicitly fictional USD→INR 83 TARGET_PER_SOURCE.
The complete target's ten measured evaluations all compute PASS. EXPLAIN records
the actual indexed plan; images are not a 10,000-image quality benchmark.

Environment: Intel Core Ultra 7 265, MemTotal 65,278,588 kB, Linux
6.11.0-1020-oem x86_64/glibc 2.39, Python 3.13.11, PostgreSQL 16.15.

| Operation | Samples | Median ms | Measured p95 ms | Max ms |
|---|---:|---:|---:|---:|
| Candidate lookup | 25 | 3.764 | 4.813 | 8.217 |
| Pure rules including PO/GRN | 10 | 2.995 | 3.332 | 4.630 |
| Transactional finalization including budget | 10 | 140.317 | 185.991 | 186.304 |
| Enqueue/claim/context/finalization | 10 | 356.879 | 384.471 | 400.376 |

These are warm local small samples, with other local verification work running;
they establish no production SLA, extraction accuracy, image retrieval recall or
enterprise throughput. Detailed ignored report: generated/reports/finance-phase3.json.

## Verification and preservation

The original 641 Python / 16 browser scenarios remain present; 63 Python and seven
browser checks were added. The final Python aggregate returned **704 passed**, exit 0, **1179.01 s**,
zero failures/skips and one upstream Starlette/httpx deprecation warning. The final
reference-label correction also passed its post-fix seven-unit check. Browser:
**23 passed in 72.343 s**, exit 0, zero failures/skips/flaky. TypeScript/build: exit 0; final production compile 711 ms. A separate
Node server-identity check passed (1 test), proving disabled-cookie rejection and
explicit enabled configured selection. `pip check`: no broken requirements.
Source checks: nine original pack/ZIP, 23 finance fixture/golden, 11 extraction
fixture and 15 actual synthetic document entries all match; working spec compares
identically with preserved original. No original fixture semantics changed.
Original pure rules have no diff. Private uploads, personal user invoice, tokens,
runtime databases, benchmark outputs, screenshots and weights are absent from Git.

T01–T42: 36 IMPLEMENTED + PASSING, 4 partial (T29/T30/T33/T39), 2 not implemented
(T31/T34), with exact test evidence and owners in [coverage](test_coverage.md).
Native/OCR and remote TypeLLM contracts are preserved. Live VLM remains
**DEFERRED — BLOCKED EXTERNAL PREREQUISITE**; no driver, Docker, CUDA, SGLang,
model download or cloud provisioning was attempted.

## All 38 approved exit criteria

| # | Criterion | Disposition | Evidence |
|---:|---|---|---|
| 1 | Reference staging/activation | SATISFIED | PG staged/snapshot/invalid/RLS; browser activation. |
| 2 | Pinned reference snapshots | SATISFIED | Old/new catalog snapshots and retained policy replay. |
| 3 | Exact/ambiguous identity | SATISFIED | Exact/curated/fuzzy units, scoped API. |
| 4 | Vendor/payment accounts | SATISFIED | Blocked/change HOLD; no master mutation. |
| 5 | PO matching | SATISFIED | Pure/PG clean and commercial evidence. |
| 6 | Contract matching | SATISFIED | Real staged authorized contract route. |
| 7 | GRN/service acceptance | SATISFIED | Goods capacity and actual staged service accepter. |
| 8 | Cumulative allocations | SATISFIED | Prior current/legacy allocations and grouped lines. |
| 9 | Partial deliveries | SATISFIED | 50 remaining, 70 new, 20 shortfall. |
| 10 | Returns/reversals | SATISFIED | Net-capacity tests and append-only lifecycle. |
| 11 | Configured UOM | SATISFIED | Approved factor vs missing conversion. |
| 12 | Price tolerance | SATISFIED | All four explicit operators. |
| 13 | Fuzzy candidate search | SATISFIED | Indexed retrieval, punctuation REVIEW/DISTINCT. |
| 14 | pHash candidate search | SATISFIED | Actual image transformations and PG band retrieval. |
| 15 | No confirmation from fuzzy/pHash alone | SATISFIED | Different-purchase negative, pure abstention. |
| 16 | Shared receipts | SATISFIED | Authorized actual source/item shares. |
| 17 | Overallocated receipts blocked | SATISFIED | 600 + 800 > 1200 HOLD. |
| 18 | Company-card/advance protection | SATISFIED | Independent PG payment proofs for both types. |
| 19 | Possible split REVIEW | SATISFIED | Actual near-threshold/cross-month trip fixture. |
| 20 | Budget ledger/reservations | SATISFIED | Source ledger, reservations and all-resource events. |
| 21 | No PO double-counting | SATISFIED | Covered commitment/consumption/reversal invariants. |
| 22 | Concurrent budget capacity | SATISFIED | Real PostgreSQL synchronized 80+80 against 100. |
| 23 | Concurrent GRN capacity | SATISFIED | Real synchronized competition against 50. |
| 24 | Concurrent duplicate finalization | SATISFIED | Identical independent obligations, <=1 eligible. |
| 25 | Approval chains | SATISFIED | Ordered authenticated browser/API completion. |
| 26 | Authority checked | SATISFIED | Scope/role/master/amount/currency/exception CFO. |
| 27 | Self-approval prevented | SATISFIED | 403 + rejected action/audit; forged DTO 422. |
| 28 | Delegation | SATISFIED | Valid/expired approval and on-behalf submission. |
| 29 | Stale authority invalidation | SATISFIED | Material revision, changed policy/requirements. |
| 30 | Explicit immutable waivers | SATISFIED | Original FAIL retained; nonwaivable rejection. |
| 31 | Evidence resolves | SATISFIED | PG every evidence, stale/preapproval/doc/page/cell. |
| 32 | Expanded reports | SATISFIED | JSON/HTML calculations/waiver findings; old reports retained. |
| 33 | Relevant UI works | SATISFIED | 23 browser cases and visual inspection. |
| 34 | Migrations | SATISFIED | Fresh/old upgrade, roundtrip, RLS/precision/drift. |
| 35 | Phase-1/2 regressions | SATISFIED | Full 704 aggregate and original 16 browser cases pass. |
| 36 | New tests | SATISFIED | Full 704 aggregate, post-fix reference units and all 23 browser cases pass. |
| 37 | Deterministic acceptance | SATISFIED | Computed vendor/employee/concurrency/PDF paths above. |
| 38 | Phase-4 boundary | SATISFIED | No operations/lease/export/ML implementation. |

## Limitations and next boundary

Fictional policies/authority/FX are not signed-off company rules. INR ordinary
finance is bounded; credit/refund and uncertain segmentation cannot receive unsafe
PASS. History/reference/aggregate bounds fail explicitly. Scope locking is
conservative. Synthetic JSON facts have no real page previews; actual PDFs/photos
do. Source verification stays manual; general invoice layout/VLM quality is not
claimed. Malware scanner is NOT_CONFIGURED. Production SSO, ERP integration,
real-data authorization, backup/restore and measured enterprise deployment remain
external/later work. Publication status and exact final commits belong in progress.

Recommended next approved batch: Phase-4 reviewer ownership/version conflict,
dependency/dead-letter inspection, reconciliation and audit replay with immutable
decisions/effects. Recommendation only; **Phase 4 has not begun**.
