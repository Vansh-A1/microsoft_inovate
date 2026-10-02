# P0-03 golden finance cases

**Fixture prepared; rule not yet implemented.** These ten fictional, manually adjudicated cases contain future screening expectations. PASS/REVIEW/HOLD in these files are data labels; neither the validator nor an application produces a finance decision. T01–T42 remain NOT IMPLEMENTED.

Each case loads against the unchanged [synthetic references](../synthetic/README.md). Cases are **independent alternatives**: do not reserve them together or count one golden transaction as another case's history. The two shared-receipt cases intentionally reuse the same synthetic receipt facts while describing different proposed allocations. Only `historical_transactions.json` supplies baseline financial effects.

## Case inventory

| File | Prepared T IDs | Future expectation | Adjudication basis |
|---|---|---|---|
| [vendor/clean.json](vendor/clean.json) | T01, T24 | PASS | 20 new units fit 50 remaining; INR 23,600 covered by the PO commitment, both demo approval steps present. |
| [vendor/paid_duplicate.json](vendor/paid_duplicate.json) | T03 | HOLD | Distinct new UUID repeats vendor/number/date/amount/currency of a paid historical obligation. |
| [vendor/partial_grn.json](vendor/partial_grn.json) | T08 | HOLD | Ordered 100, net accepted 80, prior consumed 30, new 70: remaining 50, shortfall 20. |
| [vendor/approval_pending.json](vendor/approval_pending.json) | T26 | HOLD | Manager approved INR 23,600; the required Department Head step is absent. |
| [employee/clean_taxi.json](employee/clean_taxi.json) | T13 | PASS | INR 2,400 against INR 3,000/day, employee/receipt-fact/budget/Manager context supplied. |
| [employee/hotel_two_nights.json](employee/hotel_two_nights.json) | T14 | PASS | INR 15,000 / 2 verified synthetic nights = INR 7,500/night, below INR 8,000. |
| [employee/hotel_unknown_nights.json](employee/hotel_unknown_nights.json) | T15 | REVIEW | Total known; night count, stay dates and per-night amount are null, category check expectation UNKNOWN. |
| [employee/daily_meals.json](employee/daily_meals.json) | T16 | REVIEW | Paid 600 + reserved/pending 600 + current 600 = INR 1,800/day against INR 1,500, excess 300. |
| [employee/shared_within.json](employee/shared_within.json) | T19 | PASS | Authorized peer share 600 + proposed claimant share 600 = INR 1,200 eligible receipt. |
| [employee/shared_exceeded.json](employee/shared_exceeded.json) | T20 | HOLD | Peer share 600 + proposed claimant share 800 = INR 1,400 against 1,200, excess 200. |

T14 and T19 specify category/allocation checks; their fixture-level PASS labels additionally assume the supplied demo employee, budget and approval context is satisfied by future controls. These labels do not validate unmodeled production controls. T24 prepares PO budget coverage arithmetic, not a commitment-transfer implementation or concurrency test.

## Case contract

[manifest.json](manifest.json) declares fixture schema `p0-03-v1`, the exact file set and each case's display ID, branch, T IDs and future decision. Each case contains:

- Stable UUID `id`, display `case_id`, positive version, scope and `synthetic: true`.
- Fixed `evaluation_at`, `decision_mode: RULES_ONLY` as input intent, and data-only readiness text.
- A synthetic transaction with source-fact IDs, separate business number, exact financial fields, claimed context, and version-bound synthetic approval actions.
- `reference_ids` and a versioned `reference_snapshot`; pins include the transitive reference roots needed by the case. Embedded child versions match their parent. Other golden cases cannot supply links.
- `expected_facts` with explicit math operands; nullable denominators are preserved. `expected_decision`, rule/reason concepts and rationale come from specification examples, not executed RuleResults.
- `expected_evidence` relationships using the P0-02 contract. Record versions and field paths resolve. Document references address JSON source facts with no invented pages, boxes or extraction confidence. Missing approval cites the actual transaction, policy and snapshot, never an imaginary approval UUID.

The source records are `SYNTHETIC_JSON_FACTS_ONLY` with `ADJUDICATED_SYNTHETIC_FACTS` verification. This is not authentication, receipt ingestion, a provider output, or real-document evidence. Approval identities/roles are synthetic declared metadata. Receipt shares remain data; an excessive `PROPOSED` share is not an already committed over-allocation.

## Validation and extension

Run `python3 -m pytest apps/api/tests/fixtures -q` from the repository root. Tests validate case/reference schemas and scoped relationships, pinned versions, evidence paths/kinds, manifest consistency, allowed decisions/T IDs, exact arithmetic and repeated-load determinism; malformed mutations must fail. Follow the [reference README](../synthetic/README.md) for adding fixtures and intentionally updating `data/synthetic/fixtures.sha256`. Update [coverage](../../docs/test_coverage.md) as fixture support only until the corresponding business behavior exists and is tested.

This representative subset contains no services, rule registry/combiner, extraction adapter, images/PDFs, training data, database, API, or implemented approval/budget/duplicate evaluation. Full-scale and additional scenario fixtures remain later approved work.
