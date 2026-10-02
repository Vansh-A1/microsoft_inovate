# Baseline domain glossary

This is terminology from the [specification](AP_Exception_Assistant_Codex_Spec.md), not an implemented schema, executable contract, or full production data model. It will evolve as approved tasks formally implement fields and relationships. No database fields are introduced here.

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

Financial screening, processing, and human review states must stay separate. Formal enums, schemas, evidence locators, and Decimal/currency contracts belong to P0-02 and are not implemented by this glossary.
