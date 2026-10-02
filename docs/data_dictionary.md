# Domain glossary and implemented foundational contracts

Terminology comes from the [specification](AP_Exception_Assistant_Codex_Spec.md). P0-02 implements the foundational value contracts described below; the broader glossary is not a database schema or complete transaction/evaluation model. No persistence fields or financial workflow are introduced here.

| Term | Meaning |
|---|---|
| Tenant | An authenticated organizational isolation boundary. Trusted tenant identity comes from server authentication, not arbitrary request data. |
| Legal Entity | The business entity within a tenant whose transactions, references, policies, and budgets apply. |
| Transaction | A stable UUID-identified vendor invoice or employee expense being screened; it is distinct from an invoice number or file hash. |
| Transaction Version | An immutable canonical revision. Material corrections produce a new version and invalidate affected eligibility/approvals. |
| Vendor Invoice | A supplier's bill evaluated against approved vendor identity, commercial records, goods/service acceptance, arithmetic, duplicates, budget, and approvals. |
| Employee Expense | A reimbursement claim with authenticated claimant/submission metadata and receipt evidence, evaluated against expense policy and shared controls. |
| Document | A preserved original invoice/receipt source; previews and transformations are derived artifacts. One file need not equal one transaction. |
| Evidence | A source field, import cell, policy clause, or matched versioned record supporting a finding, accessible through authorized routes. |
| Evaluation | An immutable run over pinned transaction, references, rules/policies, versions, and evaluation time. Reassessment creates a separate run. |
| Rule Result | An individual check's status, effect, reason, observed/expected values, applicable rule/version, and evidence. |
| Reference Snapshot | The exact immutable reference versions used by an evaluation, including completeness/freshness information. |
| PASS | Screening eligibility under configured controls at the recorded snapshot. All applicable required checks must be satisfied; it does not mean paid. |
| REVIEW | A judgment, correction, ambiguous match, or uncertain fact requires examination. |
| HOLD | A mandatory condition or control must be resolved before eligibility. Held transactions remain visible for action. |
| Processing State | Whether ingestion/computation succeeded or needs action, separate from financial screening. Spec states include RECEIVED, QUARANTINED, QUEUED, PROCESSING, NEEDS_INPUT, FAILED_RETRYABLE, FAILED_FINAL, and COMPLETED. |
| Review State | Human workflow status, separate from screening: NOT_REQUIRED, OPEN, ASSIGNED, AWAITING_INFORMATION, APPROVED, DECLINED, RESOLVED, or CANCELLED. |
| UNKNOWN | A check cannot be established from available facts/dependencies. It is not PASS, FAIL, zero, false, missing, NOT_APPLICABLE, or ERROR. |
| NOT_APPLICABLE | A check is excluded by a cited applicability policy; absence of evidence alone does not establish this status. |
| ERROR | A check could not execute correctly; it must remain explicit and cannot count as passed. |
| Decision Effect | NONE, REVIEW, or HOLD: a finding's configured routing effect, distinct from rule status and severity. |
| Currency | The explicit denomination of a monetary value. Comparing/converting currencies requires a permitted, versioned FX convention/rate. |
| Money / Decimal | An exact decimal amount with currency. Authoritative calculations use Decimal; financial JSON values are decimal strings. |
| Approval | An authorized action bound to the applicable transaction version, policy, scope, authority, sequence, and separation of duties. |
| Budget | Configured capacity tracked with commitments/reservations/consumption and append-only adjustments, without double counting. Missing budget is not unlimited budget. |
| Duplicate Candidate | A comparison target supported by exact, business, fuzzy, or image signals. A candidate or pHash similarity alone is not a confirmed repeated obligation. |
| Audit Event | An append-only record of a significant action and its actor, versions, reason, and evidence; eligibility changes must commit consistently with audit. |
| Waiver | A separate, authorized, scoped, evidence-backed exception to a waivable rule; ordinary approval does not imply a waiver. |

Financial screening, processing, and human review states stay separate. Transaction/evaluation/rule-result schemas and business controls remain future tasks.

## Implemented states

Implementation: [states.py](../apps/api/app/domain/states.py).

| Contract | Exact values |
|---|---|
| ProcessingState | RECEIVED, QUARANTINED, QUEUED, PROCESSING, NEEDS_INPUT, FAILED_RETRYABLE, FAILED_FINAL, COMPLETED |
| ScreeningDecision | PASS, REVIEW, HOLD |
| ReviewApprovalState | NOT_REQUIRED, OPEN, ASSIGNED, AWAITING_INFORMATION, APPROVED, DECLINED, RESOLVED, CANCELLED |
| RuleStatus | PASS, FAIL, UNKNOWN, NOT_APPLICABLE, ERROR |
| DecisionEffect | NONE, REVIEW, HOLD |

These are separate Enum types, not interchangeable string aliases. Use `.value` for their documented wire vocabulary and explicit member comparisons such as `status is RuleStatus.PASS`. Boolean coercion raises TypeError for every state, so `if status` cannot mistake UNKNOWN, FAIL, or NOT_APPLICABLE for success. No state transition logic or decision combiner exists.

### UNKNOWN and absent values

`RuleStatus.UNKNOWN != False`, `0`, `None`, FAIL, PASS, NOT_APPLICABLE, and ERROR. None represents an absent optional value; UNKNOWN is an explicit unresolved-check status. Neither defaults to a clean result. Money rejects None and booleans; monetary zero must be supplied explicitly. Evidence observations may be absent (`None`) or explicit text (`"0"`, `"false"`, or a redacted representation); they do not become numeric/boolean facts or replace a rule status. Eligibility handling belongs to later controls.

## Money and currency

Implementation: [money.py](../apps/api/app/domain/money.py).

- `Money(amount, currency)` is frozen. It accepts finite Decimal values, ungrouped plain ASCII decimal strings, and integers; it rejects floats, booleans, None, non-finite decimals, grouped/localized text, and scientific-notation strings. An existing Decimal may have an exponent; no constructor rescales or rounds it.
- An externally constructed Decimal is accepted as an exact value. This type cannot establish how that Decimal was produced; callers must not first create it from a float.
- Currency must be exactly three ASCII letters and is normalized to uppercase. Whitespace/symbols/digits are rejected. This validates structure only, not official registration or policy support.
- Equality compares amount and currency; differing scale with the same exact value compares equal. Addition/subtraction require another Money in the same currency, otherwise fail explicitly. There is no FX, scalar coercion, tax calculation, division, or rounding policy.
- Arithmetic uses a private Decimal context with operand-derived sufficient precision and rounding/inexact/overflow traps. It does not read or mutate the caller's precision, rounding, or flags. Supported operations never silently lose digits; implementation-limit errors remain errors.
- `to_dict()` emits `amount` as plain decimal text and `currency` as normalized text. Fractional zeros are preserved without rounding, including tiny values beyond ordinary currency minor units. No API endpoint is implemented.
- Explicit zero and negative values are valid generic monetary values. This does not authorize any bill/credit/refund treatment; those are later business controls. Currency scale, input resource limits, tax/FX, and rounding policy are not implemented in P0-02.

## EvidenceReference and source locators

Implementation: [evidence.py](../apps/api/app/domain/evidence.py).

| Contract/field | Meaning and validation |
|---|---|
| EvidenceKind | DOCUMENT_FIELD, IMPORT_CELL, TRANSACTION, PO_LINE, GRN_LINE, CONTRACT, POLICY_CLAUSE, MASTER_RECORD, APPROVAL, BUDGET_LEDGER, HISTORICAL_AGGREGATE |
| EvidenceReference | Frozen reference to an existing record/version, with optional source, snapshot, and raw/redacted observation metadata. |
| record_id / tenant_id / legal_entity_id | Required, non-nil UUID objects; display numbers and UUID strings are not automatically converted. Tenant/entity values must eventually come from trusted server context. |
| record_version | Positive integer or nonblank text tag, supporting transaction revisions and versioned policies/master records; booleans, floats, and missing versions are rejected. |
| field_path | Optional nonblank field/clause path on the referenced record. |
| document_id / snapshot_id | Optional non-nil UUID objects. |
| page | Optional positive one-based integer; a page locator requires document_id. No default page is guessed. |
| BoundingBox | Frozen x1/y1/x2/y2 numeric positions satisfying `0 <= x1 <= x2 <= 1` and `0 <= y1 <= y2 <= 1`. Non-finite, reversed, out-of-bounds, boolean, or nonnumeric coordinates are rejected. Coordinate floats are positions, not financial values. |
| bbox / coordinate_system | Optional typed BoundingBox; when present, document_id and page are required and the convention is `normalized_original_page`. When absent, both bbox and coordinate_system are None. Coordinates are never invented. |
| observed_value | Optional text preserving an observed or redacted representation. Numeric/boolean values are not silently converted. |
| ImportCellLocator | Frozen batch UUID, nonblank sheet, positive one-based row, and nonblank original column identifier. IMPORT_CELL evidence requires this complete locator; no importer or spreadsheet parser exists. |

These references validate structure and keep facts immutable; they do not prove record existence, authorize access, verify tenant relationships against a database, or verify that coordinates map to real content. Source resolution and transform validation are later work.

### Missing evidence without invented records

A missing-approval finding can carry a TRANSACTION reference to the actual current transaction/version, a POLICY_CLAUSE reference to the actual requirement/version, and the search snapshot on the transaction reference. Its observed text can state that approval was absent. It does not create an APPROVAL reference or guess an approval UUID. No standalone missing-approval rule, evaluation, or policy engine is implemented here.
