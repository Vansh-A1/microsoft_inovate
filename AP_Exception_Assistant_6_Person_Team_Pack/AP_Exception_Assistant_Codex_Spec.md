# Accounts-Payable Exception Assistant — Codex Implementation Specification

> Build an evidence-based finance control system that automatically passes eligible clean cases, routes uncertainty to a reviewer, and holds transactions that lack mandatory controls. Every conclusion must be traceable to source documents, matched records, and versioned rules.

## 0. Metadata, provenance, and how to use this document

| Field | Value |
|---|---|
| Project | The Accounts-Payable Exception Pile |
| Event | Microsoft Innovate 2026 |
| Team | AI BATTALION 1 — Team ID 152 |
| Specification version | 1.0 — 2026-09-28 |
| Intended reader | Codex and the student implementation team |
| Branches | Vendor invoices and employee expenses |
| Final screening decisions | `PASS`, `REVIEW`, `HOLD` |
| Source conversation | Explain Problem Statement — `6ab9473a-248c-83e8-9e80-b14a00c8295e` |

This specification consolidates the available conversation history and the current request, then adds explicitly proposed engineering choices. All 10 turns returned by the conversation reader were inspected; its longest technical answer was capped at 20,000 characters. The current request supplies the intended coverage beyond that cap. Do not interpret illustrative figures in the earlier conversation as measured results or approved company policy. The presentation template is not an implementation constraint and was not needed to author this specification.

**Requirement language:** MUST is a release gate. SHOULD is the default unless an architectural decision record explains the alternative. MAY is optional. All limits, tolerances, thresholds, service targets, and policy examples below are proposed development defaults, not legal requirements or confirmed sponsor rules.

**Codex execution contract:** implement one phase at a time; maintain a working vertical slice; preserve deterministic business controls; write tests for financial invariants; record assumptions; stop only the dependent work when a real external decision is missing. Use synthetic data and local adapters until credentials, deployment destinations, and real-data authorization are supplied. Creating this specification does not authorize cloud purchases, live payments, messages to vendors, or use of real employee data.

## 1. Business problem and intended outcome

Finance receives thousands of invoices and reimbursement claims. Repeated bills, missing documents, mismatched quantities, unapproved suppliers, over-limit expenses, and insufficient approvals create a queue of exceptions. Manual inspection of every row wastes time, while simplistic automation can pass the wrong records or offer explanations that cannot be verified.

The assistant must answer: **Does this transaction have enough verified evidence and authorization to pass the configured finance controls, or what must a human resolve?**

The product is a hybrid decision-support application, not primarily a chatbot. It combines document extraction, deterministic rules, record matching, optional ML, and a reviewer workspace. A conversational interface can be added later as a read-only explanation surface.

### 1.1 Required outcomes

1. Accept invoice PDFs/images, receipt PDFs/images, and structured invoice/expense spreadsheets.
2. Produce canonical, validated records with field-level provenance.
3. Evaluate the vendor or employee workflow and shared budget/approval controls.
4. Automatically pass only cases whose required checks are complete and satisfied.
5. Route ambiguous cases to `REVIEW`; route mandatory unmet controls to `HOLD`.
6. Explain every finding with the applicable rule/version and source or matched record IDs.
7. Record original decisions, corrections, approvals, overrides, and reevaluations without overwriting history.
8. Measure routing accuracy, reviewer workload, extraction quality, latency, and operational failures.

### 1.2 Scope boundaries

| In the implementation scope | Outside the initial scope |
|---|---|
| Two complete intake-to-review workflows | Executing bank transfers or issuing reimbursements |
| CSV/XLSX master-data imports with validation | Building a full ERP, payroll system, or tax filing product |
| Versioned configurable finance controls | Claiming legal or tax compliance from format checks |
| PO, contract, receipt, budget, and approval matching | Automatically modifying vendor bank details |
| Rules-first screening and anomaly prioritization | Declaring fraud or misconduct |
| Human corrections and decisions with permissions | Unsupervised policy changes or model promotion |
| Azure-ready deployment and local development | Requiring expensive GPU infrastructure for the first usable slice |

Credit notes, refunds, prepayments, partial reimbursements, and service milestones must be recognized rather than forced through an inappropriate positive-invoice path. In the MVP, unsupported document types receive `REVIEW` with an explicit unsupported-flow reason. Their specialized accounting treatment is a later phase.

### 1.3 Product measures

- Auto-pass rate: PASS cases / successfully evaluated cases. Report this alongside correctness, never as the only goal.
- False-pass rate: adjudicated material exceptions among sampled PASS cases / adjudicated PASS cases.
- Exception recall: confirmed exception cases routed to REVIEW or HOLD / all confirmed exception cases in the evaluated set.
- Reviewer workload: cases routed, median handling time, age of queue, and reopened cases.
- Duplicate detection: precision and recall for confirmed duplicate pairs and transaction-level routing.
- Extraction: per-field accuracy, critical-field exact match, abstention rate, and correction rate.
- Report quality: percentage of findings with resolvable evidence and reproducible arithmetic.
- No historical conversation example such as “9,200 automatically passed” is a measured project result.

## 2. Decisions, lifecycle states, and non-negotiable invariants

### 2.1 Three different state dimensions

| Dimension | Allowed states | Meaning |
|---|---|---|
| Processing | `RECEIVED`, `QUARANTINED`, `QUEUED`, `PROCESSING`, `NEEDS_INPUT`, `FAILED_RETRYABLE`, `FAILED_FINAL`, `COMPLETED` | Whether computation and ingestion succeeded |
| Screening | `PASS`, `REVIEW`, `HOLD`; null before a decision | Result of an immutable evaluation run |
| Review/approval | `NOT_REQUIRED`, `OPEN`, `ASSIGNED`, `AWAITING_INFORMATION`, `APPROVED`, `DECLINED`, `RESOLVED`, `CANCELLED` | Human workflow; approvals also have per-step states |

`PASS` means eligible under the configured screening and approval policy at the recorded snapshot. It does not mean paid. `REVIEW` means a judgment, correction, or uncertain match needs examination. `HOLD` means processing toward payment eligibility must wait for a mandatory control or condition to be resolved. A held item remains visible in the exception queue and may need human action.

An unavailable dependency is not a clean result. Persist an incomplete evaluation with its missing checks; generate REVIEW or HOLD according to the affected control. Never substitute zero risk or a passed check for a timeout. Files that cannot safely be opened remain quarantined with no finance decision.

### 2.2 Invariants

1. All business records carry `tenant_id` and `legal_entity_id`; tenant identity comes from authenticated server context.
2. UUIDs are primary keys. Invoice numbers and hashes are matching attributes, not record identities.
3. Monetary values use decimal arithmetic and an explicit currency. JSON encodes amounts as strings. No binary floats for financial calculations.
4. Unknown is different from false, zero, absent, or passed. Rule statuses are `PASS`, `FAIL`, `UNKNOWN`, `NOT_APPLICABLE`, and `ERROR`.
5. Raw documents and extraction outputs are preserved. Corrections create new versions with actor, reason, and source evidence.
6. Every evaluation pins transaction, rules, policies, reference snapshots, normalizer, feature, and model versions.
7. A mandatory failure or unresolved mandatory dependency cannot be offset by a low ML score.
8. All required controls must be satisfied or explicitly not applicable under a cited policy before PASS.
9. A fuzzy match, perceptual similarity, or unusual amount is not conclusive duplicate evidence or proof of misconduct.
10. No vendor/employee/master record is created or changed solely because an extracted document says so.
11. Budget and PO/receipt allocations must remain valid under concurrent processing, retries, cancellation, and reevaluation.
12. A material edit invalidates previous eligibility and affected approvals. Reports remain tied to their original versions.
13. Payment execution is outside scope. Even a future integration must revalidate eligibility, reservations, and approval freshness immediately before handoff.
14. No live model learns from a reviewer click immediately. Labels enter a governed offline retraining pipeline.

## 3. Recommended stack and system architecture

### 3.1 Technology choices

| Layer | Proposed choice | Responsibility and boundary |
|---|---|---|
| Web | React with Next.js and TypeScript | Upload, review, approvals, evidence, reporting; no authoritative financial decisions in the browser |
| API | FastAPI, Pydantic, SQLAlchemy, Alembic | Authentication integration, validated contracts, orchestration, transactions, migrations |
| Database | PostgreSQL | Business data, versioned decisions, rules, reference imports, work queue in MVP |
| Files | Azure Blob Storage; local filesystem adapter in development | Originals, safe previews, extraction artifacts, report exports, model bundles |
| Preprocessing | PyMuPDF, OpenCV, Pillow | PDF text/page extraction, safe image transforms, quality measurements |
| Extraction | TypeLLM adapter + compatible VLM | Schema-constrained field extraction; provider implementation isolated |
| Optional OCR | Replaceable OCR adapter | Text and word coordinates when the primary extraction path needs fallback |
| Matching | RapidFuzz, image perceptual hashing | Candidate scoring, text similarity, receipt-image similarity |
| Finance rules | Typed Python functions + versioned configuration | Decimal arithmetic and auditable checks |
| ML | Isolation Forest baseline; XGBoost OR LightGBM later | Anomaly prioritization first; supervised exception probability only with adequate labels |
| Explanations | SHAP for the supported model configuration | Model attribution, separate from rule evidence |
| Jobs | PostgreSQL outbox/jobs initially; Azure Service Bus adapter later | Durable at-least-once work dispatch and idempotent workers |
| Azure | Container Apps or App Service for web/API; separate workers; PostgreSQL; Blob; Key Vault; monitoring | Deployment targets, selected and costed before provisioning |
| Identity | Entra ID/OIDC for enterprise; clearly isolated development identity | Server-side authorization and role mapping |

Choose one frontend deployment path, one supervised model library, and one queue implementation per phase. Pin tested package versions in lockfiles after the first compatibility spike. Do not claim that any hosted LLM API automatically works with TypeLLM. The VLM runtime and GPU sizing require a measured compatibility and cost check.

### 3.2 End-to-end architecture

```mermaid
flowchart TD
    U[Finance web app and structured imports] --> A[Authenticated FastAPI intake]
    A --> O[Original document storage]
    A --> Q[Transactional outbox and job queue]
    Q --> P[Safe preprocessing and classification]
    O --> P
    P --> X[Extraction adapter: TypeLLM plus VLM]
    P -. optional fallback .-> OCR[OCR adapter]
    OCR --> X
    X --> N[Canonicalization and field validation]
    N --> V[Vendor invoice branch]
    N --> E[Employee expense branch]
    M[(Versioned reference and historical data)] --> V
    M --> E
    V --> VC[Vendor, duplicates, PO, contract, receipt, price, quantity]
    E --> EC[Employee, receipt duplicates, category, policy, limits]
    VC --> S[Budget, approvals, dates, arithmetic]
    EC --> S
    S --> R[Versioned rule results and exact evidence]
    S --> F[Point-in-time features and anomaly signals]
    F --> ML[Optional risk model]
    ML --> SH[SHAP model explanation]
    R --> D[Deterministic decision combiner]
    ML --> D
    SH --> D
    D --> PASS[PASS]
    D --> REV[REVIEW]
    D --> HOLD[HOLD]
    PASS --> REP[Versioned explainable report]
    REV --> REP
    HOLD --> REP
    REP --> UI[Human review and approval workspace]
    UI --> COR[Correction or resolution event]
    COR --> N
    UI --> LAB[Adjudicated feedback dataset]
    LAB --> TRAIN[Offline evaluation and retraining]
    TRAIN --> REG[Approved model registry]
    REG --> ML
    A --> AUD[(Append-only audit events)]
    D --> AUD
    UI --> AUD
```

The diagram shows logical dependencies. Safe independent checks may run concurrently, but finalization waits for every required result. Audit events are also emitted at imports, worker transitions, reference changes, and configuration changes, not only at the three diagrammed entry points.

### 3.3 Service and module contracts

- `StorageAdapter`: upload/download by internal object key; no client-selected arbitrary URLs.
- `DocumentProcessor`: returns immutable page artifacts, transforms, extracted text, and quality metadata.
- `ExtractionAdapter`: `extract(document_bundle, schema_version) -> ExtractionResult`; fixture, TypeLLM, and fallback implementations share this contract.
- `Normalizer`: produces canonical fields and a normalization trace without changing raw evidence.
- `ReferenceResolver`: returns exact records, candidate sets, effective dates, source versions, and ambiguity reasons.
- `DuplicateDetector`: retrieves candidates, computes signals, and returns comparisons; it does not silently delete or merge transactions.
- `RuleEngine`: pure evaluation over a pinned context, with no network writes or database mutation inside rules.
- `FeatureBuilder`: point-in-time numeric/categorical features and lineage.
- `RiskModel`: score, score kind, version, applicability, and optional explanation; no final finance authority.
- `DecisionService`: precedence, completeness, version checks, allocation checks, persistence, and audit.
- `ReviewService`: permissioned assignments, corrections, waivers, and approvals followed by reevaluation.

## 4. Detailed technical pipeline

### 4.1 Stage-by-stage processing contract

| Stage | Inputs and actions | Outputs/evidence | Failure behavior |
|---|---|---|---|
| 1. Intake | Authenticated uploader, file or import; validate allowed source and role | Document UUID, upload ID, actor, tenant, source, UTC time, correlation ID | Reject unauthorized or invalid input before processing |
| 2. Safety and integrity | Stream SHA-256; sniff MIME; enforce byte/page/pixel limits; malware scan | Original hash, detected type, scan result, storage object version | Quarantine unsafe files; mark corrupt/password-protected files as needing input |
| 3. Durable scheduling | Persist metadata and outbox event in one DB transaction | Job ID, idempotency key, stage version | Reconciler retries publish; do not lose accepted uploads |
| 4. Preprocessing | Render PDF pages, preserve embedded text, orient, deskew and assess quality | Page images, text spans, transforms, page hashes, quality metrics | Bounded retries; request replacement when unreadable |
| 5. Classification | Intake hint + text/layout/VLM classification; recognize unsupported forms | Branch/type, method, uncertainty, classification version | Disagreement/unknown routes to review, not forced branch selection |
| 6. Extraction | Header and line/receipt fields via VLM adapter; optional OCR | Raw values, provider metadata, source locators, nullable values | Partial outputs retained; low quality fields need review |
| 7. Normalization | Dates, currencies, money, names, identifiers, units | Canonical transaction draft + normalizer version and trace | Ambiguity remains explicit; never guess silently |
| 8. Validation | Structure, required fields, arithmetic, reference formats | Validation findings by field and source | Critical unresolved fields stop downstream PASS |
| 9. Reference enrichment | Resolve master/PO/contract/GRN/policy/budget/history | Snapshot IDs, matched IDs and candidates | Missing, stale, ambiguous, or unavailable data becomes a finding |
| 10. Branch checks | Vendor or employee checks described below | All applicable rule results and match evidence | Continue safe independent checks; mark dependent checks unknown |
| 11. Shared controls | Budget, approval, dates, currency/tax arithmetic | Versioned snapshots, allocation proposals, approval requirements | Required unmet controls block eligibility |
| 12. Anomaly/features | Historical aggregates and split-pattern signals | Feature vector + cutoff + historical evidence | Cold-start flags; no fabricated averages |
| 13. ML/explanation | Optional compatible model and SHAP | Score kind/version + attribution status | Rules-only mode only if configured; otherwise REVIEW |
| 14. Finalization | Completeness, precedence, locks, version recheck | Immutable evaluation, decision, allocations, review case, outbox/audit | Transaction rolls back if required persistence fails |
| 15. Reporting | Render authoritative evaluation data | JSON/HTML report, later PDF/CSV | Template report works without an LLM |
| 16. Feedback | Human resolution with evidence and authorization | Correction versions, labels, approvals, superseding evaluation | Stale writes rejected; no historical overwrite |

### 4.2 Intake, imports, and idempotency

Proposed limits: 25 MiB per document, 30 PDF pages, 40 megapixels per raster image, 10,000 rows per structured import. Limits are configuration, validated on both upload and worker execution. Do not accept archives, executable content, macros, or embedded scripts as business documents.

Use two steps: create an upload session, then finalize it after content checks. If using direct Blob upload, issue a short-lived URL for one generated object key; on finalize verify existence, actual length, checksum, and allowed MIME. A client-supplied checksum is not authoritative.

An `Idempotency-Key` identifies a user action, scoped by tenant and endpoint. Reusing it with an identical request returns the existing resource; changing the request body returns `409`. Store a request hash and stable response. This prevents API retries from creating new claims; it is separate from business duplicate detection.

For CSV/XLSX, provide a column-mapping preview and validation report before commit. Preserve batch ID, sheet name, original row number, raw cell values, and row digest. Use safe parsers with resource limits; never execute formulas or macros. Missing receipts remain missing even when the spreadsheet says “receipt attached.” Link actual document IDs. Reject or explicitly stage rows with unresolved currency, entity, identity, or dates. An import can partially succeed with per-row results; never silently drop invalid rows.

Represent each receipt as a source document linked to one or more claimed expense items. A multi-page PDF may be one invoice or a bundle; require segmentation confirmation if uncertain. Track page ranges per child transaction, and detect conflicting allocations of the same receipt. Do not assume one file equals one payable transaction.

### 4.3 Preprocessing

1. Preserve the original object unchanged and record its hash and version.
2. Extract native PDF text with spans when present; render pages using PyMuPDF in an isolated worker.
3. Apply EXIF orientation; detect page rotation; deskew only when justified by measured skew.
4. Produce a normal-resolution view and optionally high-resolution crops for small text.
5. Apply denoising/contrast enhancement as derived variants, never destructive replacements.
6. Measure blur, clipping, text coverage, extreme exposure, and tiny character size. Thresholds require a fixture benchmark.
7. Compute SHA-256 of originals and derived-page fingerprints; compute perceptual hashes on canonical page images.
8. Persist transform matrices, original and rendered dimensions, page number, rendering DPI, and processing version.
9. Maintain coordinate mappings to the original. A viewer highlight must point to the actual field location, not a guessed box.
10. Repeated headers/footers and duplicate page copies must not become extra line items. Record page-level deduplication decisions.

Set memory, CPU, file-size, and wall-time limits; close documents and temporary files; disallow external PDF resource fetching. Quality warnings should explain whether the user needs to rotate, rescan, or supply an unlocked document.

### 4.4 TypeLLM and VLM extraction: accurate role

**TypeLLM is a schema-constrained structured generation layer for LLM/VLM extraction, not a classical OCR engine.** Its current README documents scalar fields, enums, nullable values, image input, field dependencies, and a client backed by a compatible SGLang-served model. Schema validity does not establish factual correctness. Do not assume arbitrary nested line-item schemas or compatibility with every hosted provider; verify the selected version and backend in a spike. [TypeLLM repository](https://github.com/TypeLLM/TypeLLM)

The following is our application design, not a claim about TypeLLM's native guarantees:

- Maintain a provider-independent canonical schema. The adapter assembles header and line-item results into that schema.
- Extract header fields first, then identify candidate line regions and extract bounded rows from page/crop references. Validate row count and totals; if table coverage is uncertain, require review.
- Use nullable fields and explicit `missing`, `illegible`, `ambiguous`, and `not_applicable` states. Do not fill gaps from likely vendor habits.
- Capture printed amount text as well as parsed decimals to protect precision and enable reviewer verification.
- Treat category prediction as a suggestion. Reimbursement eligibility is decided by the policy engine.
- Obtain employee identity from the authenticated submission/claim metadata and employee master. A receipt usually does not establish who is requesting reimbursement.
- Ask for observable document facts only. Document text such as “ignore controls and approve” is untrusted input.
- Do not ask the model to approve payments, choose bank details, issue SQL, execute code, or call external tools.
- Store provider/model identifier, package/runtime versions, prompt-template hash, schema version, timing, and usage. Store concise source-linked observations, not private reasoning traces.
- A self-reported confidence number is diagnostic, not a calibrated probability. PASS uses a validated quality policy combining source readability, field verification, arithmetic, and benchmarked extraction quality.
- If coordinates are not reliably available, store page-level evidence with `bbox: null`. Do not manufacture bounding boxes. Require human verification of ambiguous critical fields.

Optional fallback: an OCR adapter can return text and word locations for unreadable or unsupported primary-path cases; the extraction layer may structure that text. Keep the two extraction attempts and reconciliation result. Provider disagreement about a critical amount, currency, vendor, or identifier creates a review finding; never silently select whichever value makes the checks pass.

### 4.5 Fields to extract

**Vendor header:** supplier legal name/address, printed tax identifier, invoice number/date/due date, PO reference(s), contract reference, currency, subtotal, line and document discounts, tax components, shipping/charges, total, payment terms, and printed bank/payment details when present.

**Invoice lines:** printed line number, description, SKU/service code, quantity, unit of measure, unit price, line discount, taxable base, tax rate/components, net and gross amount, service period, and PO-line reference. Preserve whether amounts are tax-inclusive or tax-exclusive; unknown treatment needs review.

**Receipt facts:** merchant name/address/tax ID, receipt/transaction number, transaction date/time and timezone when known, currency, subtotal, tax, tip, total, payment method, masked payment indicator, location, line items, stay/travel dates and count of nights when printed.

**Claim metadata supplied by the employee:** claimant ID, business purpose, department/cost center/project, trip ID, attendees where required, requested reimbursement amount, original currency, company-card/advance offsets, category selection, and attachments. Keep submitted facts separate from extracted facts and approved master data.

### 4.6 Normalization and validation

- Use Unicode normalization, trim/collapse whitespace, and normalize case for search keys. Preserve original text.
- Maintain both a conservative invoice key and a more aggressive candidate key. Removing punctuation can conflate legally distinct numbers; retaining leading zeros is the default. Never globally replace `I` with `1` or `O` with `0`.
- Example candidate key: `INV-00128`, `inv 00128` → `INV00128`; emit the normalizer version and transform steps.
- Resolve dates using known source locale. `03/04/2026` remains ambiguous without context. UTC timestamps and business-local dates are separate fields.
- Parse Indian/other grouping formats according to source hints; `₹1,20,000.00` → decimal `120000.00` and currency `INR`. Currency symbols alone may be ambiguous.
- Keep source currency and base currency separately. Conversion requires rate ID, effective date, source, convention, and rounding mode. Unsupported FX is REVIEW, never a guessed rate.
- Validate tax ID shape using a configurable jurisdiction module. A format match does not prove registration or current validity; official verification is a separate optional connector.
- Validate future/stale dates against configurable tolerances and a fixed evaluation time.
- Validate positive quantities and amounts for ordinary bills; route credit/refund semantics separately.
- Validate monetary equations using Decimal and a configured currency scale/rounding rule. Missing tax is not automatically zero tax.
- Separate extraction uncertainty from document inconsistency: “printed total differs from calculated total” is different from “total unreadable.”

For tax-exclusive documents, after line-level rounding:

```text
line_net = quantity × unit_price − line_discount
subtotal = sum(line_net)
taxable_base = subtotal − document_discount + configured_taxable_charges
expected_total = subtotal − document_discount + tax_total + shipping + other_charges
amount_due = expected_total − recognized_credits − recognized_prepayments
```

Do not subtract a discount twice or add tax twice when amounts are inclusive. The exact tax calculation and allocation basis belong to the versioned policy module. For the demo, use explicitly labeled synthetic tax rates and no claim of statutory correctness.

## 5. Reference data and trusted context

### 5.1 Required reference entities

| Entity | Minimum fields | Required checks |
|---|---|---|
| Vendor master | UUID, entity, legal name, aliases, tax ID, status, approved categories, valid dates, verified payment-account version | Identity, active/approved status, category, account mismatch |
| Employee master | UUID, employee number, employment dates, status, department, cost center, manager, grade, country | Claimant authorization and policy eligibility at expense/submission date |
| Purchase order | UUID, business number, vendor/entity, currency, status, approved ceiling, lines, budget links, approval references | Correct issuer/vendor, valid status, remaining ordered and monetary capacity |
| PO lines | Item/service, ordered quantity, UOM, price, tax basis, tolerance profile | Item and price/quantity matching |
| Contract | UUID, vendor/entity, effective dates, ceiling, rates, terms, service/milestone requirements | Applicable pricing/period/ceiling and approved non-PO route |
| Goods receipt | UUID/GRN number, PO and line, received/accepted/returned quantity, date, source | Receipt availability and accepted quantity net of returns |
| Service acceptance | UUID, contract/PO line, milestone, accepted value/quantity, authorized accepter | Service equivalent of goods-receipt evidence |
| Expense policy | ID/version, effective dates, category, grade/location qualifiers, receipt requirements, rate/unit, submission window | Allowed expense, item/trip/day limits and prerequisites |
| Budget | ID, entity, fiscal period, department/project/category, currency, allocation and ledger | Remaining capacity without double counting commitments |
| Approval policy | ID/version, dimensions, amount bands, roles, sequence, delegation rules | Complete authorized chain and separation of duties |
| Historical transactions | Transaction/version, canonical facts, lifecycle/settlement status, evidence references | Duplicates, cumulative allocations, historical features |
| FX rates | ID, currency pair, date, rate, source/version | Comparable normalized money only when permitted |

### 5.2 Imports and temporal semantics

Each import stores `source_system`, `source_record_id`, `source_version`, `import_batch_id`, `imported_at`, `effective_from`, `effective_to`, and validation results. Staging must detect duplicate source IDs, broken relationships, overlapping policy dates, invalid amounts, unknown currencies, and orphaned PO/GRN links before activation.

Use effective-at-transaction-date policy selection where appropriate, plus current mandatory restrictions such as a newly blocked vendor at release time. Record both when they differ. Select exactly one applicable policy version or return ambiguity. Never default to the most permissive policy when several match.

A reference snapshot is a set of immutable version IDs used by an evaluation. Preserve historical records even after a newer import activates. Track freshness thresholds by source; stale budget/approval/master data can block PASS. Mock references must be visibly marked synthetic. Identity resolution uses exact approved identifiers first, curated aliases second, fuzzy candidates third; fuzzy name similarity alone must not silently bind a vendor or employee.

## 6. Vendor invoice workflow

### 6.1 Vendor and payment-detail validation

Resolve the vendor within tenant/legal entity using approved ERP IDs, tax IDs, or curated aliases. Fuzzy names produce candidates rather than silently establishing identity. Check active/approved status, permitted supply categories, effective dates, legal entity and currency. New-vendor status is an anomaly signal, not automatically a violation. Unknown identity requests REVIEW; a known blocked vendor requires HOLD. An approved-vendor requirement remains unsatisfied until identity is verified.

Compare printed payment instructions with the verified vendor account version using normalized secure equality tokens or a keyed HMAC. Store raw banking details encrypted only when required and mask them in reports. Never fuzzy-match bank accounts or change master data based on an invoice. An unverified account change defaults to HOLD pending independent verification by an authorized master-data workflow. Ordinary invoice approval does not authorize changing the vendor's beneficiary.

### 6.2 PO and contract resolution

1. Resolve explicit references within the legal entity; verify vendor, currency, status and effective dates.
2. An approved/open PO or applicable contract must cover the goods/services. Cancelled or exhausted orders cannot pass.
3. Missing references may trigger candidate retrieval using vendor, service period, items and amounts. Ambiguous matches need a human.
4. Store explicit allocations for invoice lines to PO lines; support several PO lines per invoice and, later, multiple POs.
5. Non-PO invoices require a cited exemption policy and the appropriate contract/expense authorization. Missing PO is never silently NOT_APPLICABLE.
6. Contracts supply rates, ceiling, valid periods, milestones and service-acceptance requirements. A valid contract is not proof of delivery.

### 6.3 Three-way matching and cumulative capacity

Compare invoice lines, approved PO lines and accepted GRN lines. Services may use an authorized service-acceptance or milestone record under policy. Preserve exact matched IDs and quantities.

```text
accepted_received_qty = accepted receipts − approved returns/reversals
ordered_remaining_qty = ordered_qty − prior_active_invoice_allocations
received_remaining_qty = accepted_received_qty − prior_active_receipt_allocations
eligible_new_qty = min(ordered_remaining_qty, received_remaining_qty)
quantity_variance = current_invoice_qty − eligible_new_qty
unit_price_variance = invoice_price − applicable_PO_or_contract_price
```

Prior active allocations include reserved and settled amounts from other transactions, exclude cancelled/reversed allocations, and exclude the current transaction's old allocation when replacing it atomically. A reservation and its settlement are lifecycle states of one allocation; do not count them twice.

Example: PO orders 100 units; 80 are accepted; 30 were already invoiced. Only 50 more are eligible. A new invoice for 70 has a 20-unit shortfall and cites the PO line, GRN lines and prior allocation IDs. Comparing the new invoice only with the headline 80 received units would miss the exception.

Tolerances must specify absolute/relative values, units and combination operator. A possible configured price rule is `abs(delta) <= max(abs_tolerance, abs(expected_price) * relative_tolerance)`; use it only when the policy explicitly selects MAX. Demo quantity tolerance is zero. No ML-estimated tolerance is authoritative.

Use approved UOM conversions; one box is not one item without a conversion record. Compare monetary amounts on consistent currency and net/gross bases. Unmatched invoice lines, charges or service periods remain findings. Check PO remaining amount and contract ceiling cumulatively, not only per invoice.

### 6.4 Vendor control checklist

- Required identity/date/currency/amount/source fields.
- Approved vendor, correct entity/category, verified payment instructions.
- Exact, business and fuzzy duplicate checks against pending and paid history.
- Valid PO/contract or explicit non-PO exemption.
- Ordered, billed, accepted, returned and previously allocated quantities.
- Unit price, discounts, shipping, charges, PO capacity and contract ceiling.
- Line arithmetic, tax arithmetic, total, due date and payment-term consistency.
- Duplicate billing for the same service period or milestone.
- Budget capacity, existing commitments and authorized approval chain.

## 7. Employee expense workflow

### 7.1 Employee, submitter and receipt

Resolve claimant and submitter separately. Submitting on behalf of another employee needs delegated permission. Check employment dates, grade, department, cost center, manager and travel eligibility. Expenses incurred during employment but submitted after departure may follow a specific policy; do not blanket-reject them.

Verify that an actual readable receipt supports the expense. A payment-confirmation image may not satisfy an itemized-receipt requirement. Policy determines acceptable evidence and thresholds. Employee ID normally comes from authenticated claim metadata, not the receipt image.

### 7.2 Reimbursement and policy calculations

Select one effective policy by entity, expense date, category, grade, location, currency and trip context. Overlapping policies without explicit precedence produce REVIEW. Store matched dimensions and policy version.

Check permitted category/items, business purpose, required attendees, travel class, merchant restrictions, submission window, preapproval, and document requirements. Mixed personal/business receipts need explicit item allocation or human review.

```text
eligible_business_amount = sum(eligible receipt-item allocations to claimant)
computed_reimbursement = eligible_business_amount − company_paid_amount − applied_advance
```

Preserve requested and computed amounts separately; discrepancies need explanation rather than silent reduction. Unsupported refund/negative-balance flows go to REVIEW.

Illustrative demo policies, not actual company rules:

| Policy | Category and unit | Allowance |
|---|---|---|
| EXP-HOTEL-v1 | Eligible hotel night | INR 8,000/night |
| EXP-MEAL-v1 | Employee/local expense day | INR 1,500 aggregate/day |
| EXP-TAXI-v1 | Employee/local expense day | INR 3,000 aggregate/day |
| EXP-AIR-v1 | Flight/trip | Economy and authorized amount |
| EXP-PERSONAL-v1 | Personal item | Not reimbursable |
| EXP-ALCOHOL-v1 | Alcohol item | Not reimbursable in demo policy |

INR 15,000 for two verified nights is INR 7,500/night, not a one-night violation. Aggregate meals/taxis across all applicable claims on the same local business date, including eligible in-flight reservations and excluding reversals. Missing night count, timezone or trip context must not become a guessed denominator.

### 7.3 Shared receipts and split claims

Search receipt duplicates across employees within authorized tenant/entity scope. Restrict cross-employee detail to authorized finance reviewers; return masked evidence otherwise.

A legitimate shared meal can have several receipt allocations. Store employee/item/amount shares and approval rationale; their cumulative total must not exceed eligible receipt value. Identical images attached to legitimate allocations are not automatically duplicate reimbursement.

Detect possible limit splitting using employee/merchant/category/trip, local day or a configured rolling window, individual amounts near a threshold, and aggregate above that threshold. Cite every related claim/item ID and the policy. Route to REVIEW without inferring intent.

### 7.4 Employee control checklist

- Valid employee and authorized delegated submission.
- Required receipt exists, is readable, and agrees with claimed facts.
- Exact/fuzzy/perceptual duplicates, including cross-employee and shared-receipt context.
- Category, purpose, attendees, travel class and preapproval.
- Per-item, per-night, daily, trip and monthly limits where applicable.
- Receipt/claim amount, tax/tip treatment, FX, company-card and advance offsets.
- Submission, employment and travel dates; future or impossible dates.
- Receipt over-allocation and possible claim splitting.
- Budget and complete authorized approvals.

## 8. Duplicate detection

### 8.1 Distinct identities

| Identity | Purpose | Limitation |
|---|---|---|
| UUID | Internal record identity | Not the supplier's invoice number |
| Idempotency key | Retry of one user/API action | Not business duplicate detection |
| SHA-256 | Identical file bytes | Not proof of a repeated financial obligation |
| Business fingerprint | Candidate retrieval | Not a universally unique primary key |

Two vendors may both issue INV-101. A vendor may reuse numbers across approved series/periods. Do not globally enforce invoice-number or aggressively normalized-key uniqueness. Keep independently submitted duplicates as distinct records for review and audit. A readability re-upload normally creates a document version on the same transaction.

### 8.2 Candidate retrieval

Union indexed searches for: same file digest; same entity/vendor and conservative invoice key; aggressive/fuzzy number key; same vendor/merchant/currency with near amount and date; same PO/contract/service period; same receipt transaction number; and comparable image hashes. A ±7-day fuzzy date window is an initial configurable value. Exact business-key history lookup must not be limited to that window.

Check queued, active, eligible and paid records; distinguish cancelled, rejected, corrected and superseded records. A rejected claim may still be relevant evidence but does not automatically consume capacity. Persist search completion/coverage so an unavailable search is not “no duplicates found.”

### 8.3 Comparison features and decision boundaries

Persist candidate IDs/versions, source document IDs, identity agreement, amount/currency difference, date distance, invoice-number and merchant similarity, PO/contract agreement, line-item agreement, service overlap, pHash distance, lifecycle and normalization versions.

RapidFuzz similarities are not probabilities. A proposed review-priority score is:

```text
0.35 * invoice_number_similarity
+ 0.25 * amount_similarity
+ 0.15 * date_similarity
+ 0.15 * merchant_or_vendor_similarity
+ 0.10 * PO_or_receipt_reference_similarity
```

Normalize inputs to [0,1], record missing components and coverage, and tune weights/thresholds using labeled pairs. Missing components must not become perfect agreement. No fuzzy score alone establishes a confirmed duplicate.

Classifications: EXACT_BYTES, STRONG_BUSINESS_MATCH, POSSIBLE_DUPLICATE, SHARED_RECEIPT_ALLOCATION, DISTINCT, UNRESOLVED. A verified strong business match can cause HOLD under a cited control after lifecycle and legitimate-reuse checks. Fuzzy/perceptual candidates alone default to REVIEW.

### 8.4 Perceptual hash implementation

Use an image-fingerprint adapter, initially a versioned 64-bit pHash. Hamming distance counts differing bits. The ImageHash project provides perceptual hash implementations. [ImageHash repository](https://github.com/JohannesBuchner/imagehash)

Our implementation must persist algorithm, library version, hash size, preprocessing version, page/crop, dimensions and hash. A distance <=6/64 is a candidate-retrieval seed, not a validated duplicate threshold. Benchmark photographs, recompression, brightness changes, resizing, rotations, crops and perspective distortion. Standard pHash is not guaranteed to handle every crop or rotation; add alignment or crop-aware techniques only after measuring the need.

Common merchant templates or blank pages can look similar; changed totals may remain visually close. Combine image and structured signals. Compare relevant page sets for multi-page invoices, not only the first page. Show side-by-side receipts, distance and field differences to reviewers.

### 8.5 Concurrency and resolutions

At finalization, serialize on a scoped payable-identity/candidate lock when available, requery newly committed candidates, and atomically create capacity allocations. Concurrent identical submissions must not both PASS before either is visible. UUID uniqueness does not solve this.

A reviewer may record DISTINCT with reason/evidence, bound to both compared versions. Material changes invalidate that disposition. Never permanently suppress all future matches between two vendors or delete duplicate evidence.

## 9. Budget controls and approvals

### 9.1 Budget ledger and reservations

Budget keys include entity, fiscal period, department/cost center/project, category and currency. Missing budget is not unlimited budget. Select a budget or cite an explicit exemption.

Use append-only ledger entries for allocation, adjustment, commitment, reservation, consumption, release and reversal. A PO may already reserve budget; invoicing it must transfer coverage rather than double-count it.

```text
available = allocation + approved_adjustments
          − consumed_spend − open_PO_commitments
          − active_non_PO_and_claim_reservations
incremental_need = requested_budget_basis − existing_commitment_coverage
```

Specify net/gross/tax basis and FX convention. REVIEW/HOLD cases show nonbinding availability. Final eligible PASS or a separately authorized procurement commitment acquires capacity. Finalization locks affected budget and PO/receipt rows, recomputes, transfers commitments or creates reservations, and commits decision, ledger and audit together. If capacity was taken concurrently, reevaluate as HOLD rather than keeping a stale PASS.

Acquire locks in a stable order and use bounded retries for deadlock/serialization errors. PostgreSQL provides the transactional row-locking primitives for this design. [PostgreSQL locking documentation](https://www.postgresql.org/docs/current/explicit-locking.html)

Every reservation has an owner, operation key and lifecycle. Expiry/release invalidates eligibility and triggers reevaluation before handoff. Cancellation/supersession produces compensating ledger entries. Do not release a consumed allocation as if it were still reserved. Reprocessing must neither reserve twice nor subtract the current transaction from its own available capacity twice.

### 9.2 Approval hierarchy

Requirements depend on branch, entity, amount/currency, cost center, category and exceptions. Illustrative half-open INR bands:

| Amount | Demo chain |
|---|---|
| 0 < amount < 10,000 | Manager |
| 10,000 <= amount < 100,000 | Manager → Department Head |
| 100,000 <= amount < 500,000 | Manager → Director |
| amount >= 500,000 | Manager → CFO |

This is proposed configuration. A company may use cumulative approvals, one sufficient authority, or an explicit automatic tier. PASS requires the applicable chain completed or authorized automatic approval. A clean transaction awaiting a mandatory manager remains HOLD with APPROVAL_PENDING.

Check authenticated approver identity, role/authority at action time, amount/currency, delegation validity, sequence, expiry, separation of duties and transaction-version binding. A submitter/claimant cannot self-approve. Names printed on an invoice are not approval records.

A policy waiver needs specific authority and does not follow automatically from ordinary approval. Material edits to amount, vendor, currency, bank details, category or allocations invalidate affected approvals. A policy may allow reuse only for explicitly unchanged facts.

## 10. Rule engine and initial control catalog

Rules are pure, typed Python functions over an immutable EvaluationContext and RuleConfig. They do not call networks, write databases, read the current wall clock or sample randomness. Context supplies evaluation time, transaction/reference versions, policies, candidate comparisons and historical aggregates. Declare a dependency DAG; unresolved vendor identity makes dependent vendor-specific checks UNKNOWN, not PASS.

Each RuleResult contains rule/execution/version IDs, branch, applicability, status, severity, decision effect, reason code, message parameters, observed/expected values, units/currency, tolerance/operator, evidence references, dependency results, waiver references and execution duration. Status is PASS/FAIL/UNKNOWN/NOT_APPLICABLE/ERROR. Severity prioritizes workload; decision_effect NONE/REVIEW/HOLD governs routing. NOT_APPLICABLE requires a cited applicability policy.

| Rule ID | Check | Proposed failure effect | Evidence |
|---|---|---|---|
| DOC-001 | Critical fields readable/verified | REVIEW | Page/field source |
| DOC-002 | Supported type and segmentation complete | REVIEW | Classification/page ranges |
| VAL-001 | Required branch fields | REVIEW | Schema and missing field |
| VAL-002 | Dates/currency/format unambiguous | REVIEW | Raw and normalized values |
| VAL-003 | Lines/tax/total arithmetic | REVIEW; material mismatch may HOLD | Equations, lines, tolerance |
| VEN-001 | Vendor resolved | REVIEW; mandatory approved identity blocks eligibility | Master candidates/versions |
| VEN-002 | Vendor approved, active, not blocked | HOLD | Vendor/policy version |
| VEN-003 | Verified bank instructions | HOLD for unverified change | Masked account versions |
| DUP-001 | Same file independently submitted | REVIEW until obligation context resolved | Document IDs/hashes |
| DUP-002 | Confirmed business duplicate | HOLD | Both transaction IDs and facts |
| DUP-003 | Fuzzy/pHash candidate | REVIEW | Candidate/scores/differences |
| PO-001 | Required approved PO/contract | HOLD | Reference or missing-reference finding |
| PO-002 | Vendor/entity/currency consistent | HOLD | Invoice/PO fields |
| PO-003 | Price/charges within terms | REVIEW/HOLD by materiality | Invoice/PO lines and policy |
| PO-004 | Cumulative quantity/value capacity | HOLD | PO and prior allocations |
| GRN-001 | Accepted goods/service capacity | HOLD | GRN/acceptance/allocation IDs |
| EMP-001 | Employee/submission authorized | HOLD if unauthorized; REVIEW if ambiguous | Employee/delegation |
| EXP-001 | Adequate required receipt | HOLD if mandatory | Receipt or absence plus policy |
| EXP-002 | Allowed items/category | HOLD for confirmed prohibited item | Receipt line/policy clause |
| EXP-003 | Unit and aggregate allowance | REVIEW; waiver required to clear | Claim IDs, denominator, limit |
| EXP-004 | Purpose/travel/timing/preapproval | REVIEW/HOLD for mandatory missing preapproval | Trip and policy |
| EXP-005 | No company-card/advance double reimbursement | HOLD if confirmed | Payment/advance allocations |
| EXP-006 | Receipt allocation within eligible value | HOLD if exceeded | Receipt/allocation IDs |
| PAT-001 | Possible split claim/invoice | REVIEW | Related IDs/aggregate/threshold |
| DATE-001 | Future/stale/inconsistent dates | REVIEW | Dates and tolerances |
| BUD-001 | Sufficient fresh budget coverage | HOLD | Budget/ledger snapshot |
| APR-001 | Complete approval chain | HOLD | Approval-step IDs |
| APR-002 | Authority/separation of duties | HOLD | Actor/role/delegation |
| SYS-001 | Required dependencies complete | REVIEW/HOLD by control | Failure/freshness details |

Rule configuration progresses DRAFT → VALIDATED → APPROVED → ACTIVE → RETIRED. Activation requires authorized ownership and an impact preview against regression fixtures. Reject overlapping periods, invalid bands, unknown operators or circular dependencies. Never execute user-authored Python/eval as policy configuration.

Waivers are separate immutable records scoped to rule, transaction version, authorized actor, reason, evidence and expiry. A new evaluation records the original failure plus waiver disposition. Non-waivable controls remain blocked until corrected.

## 11. Anomaly detection, ML and SHAP

### 11.1 Baselines and labels

Start with deterministic rules and explicit statistical findings. Add Isolation Forest only with representative history; report its raw score convention or anomaly percentile, not a fraud/exception probability. Supervised XGBoost OR LightGBM follows adequate adjudicated labels. Define the target as confirmed material exception or need for material intervention, not “fraud.” Training on the engine's own routing labels does not independently validate the model.

### 11.2 Feature engineering

| Feature | Definition and lineage | Missing behavior |
|---|---|---|
| log_amount | log1p of positive comparable amount | Invalid amount blocks scoring |
| vendor_amount_ratio | Amount / prior same-currency vendor median | Null plus history count for cold start |
| employee_category_ratio | Amount / prior employee/category median | Document cohort fallback |
| robust_amount_z | Deviation scaled by median absolute deviation | Explicit MAD=0 handling |
| po_value_ratio | Allocation / applicable PO remaining capacity | Not-applicable/missing flag |
| price_variance_ratio | Price difference / expected price | Guard zero denominator |
| receipt_shortfall | Positive billed quantity minus available accepted quantity | Unknown when receipt data absent |
| policy_limit_ratio | Correct unit/aggregate amount divided by policy allowance | Unknown if unit/count unresolved |
| budget_utilization_after | Projected exposure / budget on same basis | Snapshot/version required |
| max_duplicate_similarity | Highest candidate score plus comparison coverage | Zero only after completed no-match search |
| min_phash_distance | Closest comparable receipt hash distance | Null when unavailable |
| same_amount_count_30d | Prior scoped same-amount count | Point-in-time only |
| days_since_previous | Elapsed time since prior comparable item | Null on first item |
| vendor_tenure_days | Time since approved onboarding | Null if unknown |
| payment_account_changed | Verified master comparison | Explicit tri-state |
| claims_near_limit_7d | Counts/sums around policy boundary | Store threshold, window, linked IDs |
| submission_delay_days | Submission minus expense date | Ambiguous date remains missing |
| quality_and_freshness | Missingness, stale references, extraction verification | Explicit flags, never imputed clean |

Exclude the current transaction and future data from historical features. Use records known before the evaluation cutoff. Never use future payments, reviewer decisions or labels at inference. Do not feed names, raw bank accounts, protected attributes or arbitrary employee/vendor IDs as predictive features. IDs support joins/lineage. Every aggregate must have reproducible cutoff/query/snapshot and an authorized drill-down manifest.

Fit transformations only on training data. Persist feature order, types, categorical vocabulary, imputation/clipping rules and missing indicators. Retain separate feature schemas by branch if necessary.

### 11.3 Model lifecycle

1. Define labels: CLEAN_CONFIRMED, DUPLICATE_CONFIRMED, POLICY_EXCEPTION, DOCUMENT_CORRECTION_ONLY, DISTINCT_CONFIRMED, INSUFFICIENT_INFORMATION.
2. Keep corrections separate from adjudication; exclude unresolved labels from binary training unless a documented strategy handles them.
3. Version datasets, labeling rules, permissions and feature code.
4. Split chronologically; put related duplicates/document variants in one split. Add group holdouts to test unseen vendors/employees.
5. Compare with rules-only and simple statistical baselines. Synthetic cases are tests, not production accuracy evidence.
6. Evaluate precision-recall AUC, recall at review capacity, false-pass rate, calibration/Brier score if probabilities are claimed, and slices by branch/data quality/cold start.
7. Tune thresholds on validation data; freeze them before the final test.
8. Review errors, register artifact/checksum, approve, shadow, then activate. Preserve rollback.

### 11.4 SHAP contract

SHAP attributes a model output to features; it does not supply documentary proof of a violation. Supported TreeExplainer configurations may explain raw margins or probabilities. For a binary tree classifier, raw values may be log-odds; the output space must be explicit and additivity verified against the same model output. [SHAP TreeExplainer documentation](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html)

Store model/explainer versions, feature schema, background dataset, configuration, base value, all contributions, output space, explained output and additivity residual. Show top positive/negative factors with actual feature values and lineage. Never add log-odds contributions directly to a percentage. If calibration is a separate transformation, label SHAP as explaining the underlying model unless the composed predictor is explicitly supported and tested.

Use wording such as “the amount is unusual relative to prior vendor invoices”; do not claim causation or misconduct. For Isolation Forest, use transparent statistical explanations initially unless the exact estimator/explainer combination is verified. If explanation fails, mark UNAVAILABLE and apply the configured availability policy; never invent attribution bars.

### 11.5 Feedback, monitoring and retraining

Collect evidence-backed resolutions, disagreement, appeals and superseding labels. Sample PASS cases for audit to reduce queue-selection bias. Monitor missingness, input distributions, extraction quality, new-vendor mix, score distribution, delayed label performance and override rates.

Retraining starts as an offline manual job. A monthly schedule is a proposed later option, conditional on enough new labels. Drift requests evaluation, not automatic deployment. No reviewer click updates a live model. Extraction/provider, policy and feature changes also require regression evaluation.

## 12. Deterministic decision combiner

Keep extraction quality, duplicate similarity, anomaly score and calibrated exception probability as separately named quantities. Do not average them into an unexplained confidence score.

```text
1. Unsafe/unprocessable content: retain processing state; no finance PASS.
2. Applicable unwaived HOLD effect: HOLD.
3. REVIEW effect, ambiguous critical field/match, required UNKNOWN/ERROR,
   or stale reference: REVIEW, unless that control requires HOLD.
4. Active model policy requests review for high risk, unsupported cohort,
   or required scoring/explanation unavailable: REVIEW.
5. Otherwise atomically recheck versions, duplicates, approvals and capacity;
   if valid, reserve and PASS.
```

A proposed supervised review trigger is calibrated exception probability >=0.35, subject to validation. There is no ML-only HOLD threshold in the default design. A model can escalate a clean rules result to REVIEW; it cannot clear a mandatory failure.

Modes are explicit: RULES_ONLY reports model NOT_CONFIGURED; RULES_PLUS_MODEL enforces the activated model's availability/applicability policy. An outage cannot silently downgrade modes or become zero risk.

Corrections, evidence, authorized waivers and approvals trigger a new evaluation linked by `supersedes_evaluation_id`. Human approval/decline is a separate workflow outcome. Neither overwrites the original automated decision. Eligibility expires or becomes stale when material facts, approvals, reservations or reference versions change.

## 13. Evidence, reports and human review

### 13.1 Evidence reference contract

Every finding cites the current transaction/version, the rule/version, and relevant source or matched records. Evidence reference kinds include DOCUMENT_FIELD, IMPORT_CELL, TRANSACTION, PO_LINE, GRN_LINE, CONTRACT, POLICY_CLAUSE, MASTER_RECORD, APPROVAL, BUDGET_LEDGER and HISTORICAL_AGGREGATE.

A reference contains a stable record ID/version, optional field path, document/page/coordinate locator, snapshot ID, and the observed value or a redacted representation. Use one-based page numbers and normalized [0,1] bounding boxes in the original page orientation; record the coordinate convention. Null bounding boxes are valid when only page evidence exists. Import-cell evidence carries batch, sheet, row and column. A missing-data finding cites the current source, expected schema/policy and search snapshot; it must not invent a matched record ID.

All evidence links resolve through authorization-aware application routes. A report must not contain permanent public Blob URLs. “Matches invoice INV-123” is insufficient if INV-123 is merely an ambiguous business number: include the internal UUID and version as well as the display number.

### 13.2 Explainable report

Generate authoritative JSON plus deterministic HTML. Add PDF/CSV export later. Report content:

1. Report/evaluation/transaction IDs, versions, evaluated-at time and processing completeness.
2. Branch, relevant parties, business number, amount/currency and source documents.
3. PASS/REVIEW/HOLD, eligibility flag, principal reason codes and whether superseded/stale.
4. Every required check's status, including UNKNOWN/NOT_APPLICABLE with reason.
5. Findings with observed/expected values, units, tolerances, rule IDs and evidence links.
6. Duplicate comparisons, line matches, budget snapshot and approval status.
7. ML status, score kind/value, version and explanation status; no fake score when disabled.
8. Recommended next actions tied to actual unresolved controls.
9. Human actions, waivers, corrections and audit timeline references.

An optional LLM may paraphrase an already-generated report. It receives only an authorized evidence bundle and must not invent amounts, IDs, rules or decisions. Validate cited IDs/numeric claims against the bundle; reject ungrounded output and fall back to templates. A fluent narrative is never authoritative over the structured result.

### 13.3 Reviewer UI

| Screen | Required behavior |
|---|---|
| Overview | Counts by branch/decision, processing failures, queue age, measured throughput; drill-down reconciles with list totals |
| Upload/import | Branch hint, limits, progress, mapping preview, row errors and stable status polling |
| Exception queue | Filter by decision/reason/entity/owner/age, sort by SLA or amount; HOLD and REVIEW both visible |
| Case detail | Source viewer beside extracted/canonical fields; badges distinguish extracted, submitted, master and human-corrected facts |
| Evidence tab | Rule-by-rule values, exact record links, PO/GRN/receipt comparisons, source highlights |
| Duplicate comparison | Both documents and normalized fields, similarity scores, lifecycle and shared-allocation context |
| Finance controls | Line allocation table, budget basis/capacity, missing approvals and permitted next actions |
| ML tab | Score type, model version, top contributions with output-space label and limitations |
| Review actions | Claim/unclaim, request information, correct fields, mark candidate distinct/duplicate, propose/approve authorized waiver |
| Audit timeline | Original decision, changes, actor/time/reason and superseding evaluations |
| Configuration | Versioned policy preview/approval/activation with permission checks |

Use keyboard-accessible controls, readable tables, labels beyond color, and explicit loading/error/empty states. Show “Review required” or “Awaiting approval,” not accusatory labels. Hide controls the role cannot use, while enforcing permissions on the server too.

Human writes carry expected transaction/review version (If-Match or explicit version). A stale write returns 409; show the newer data and require reconciliation. Assignment uses a lease/ownership record so two reviewers cannot unknowingly resolve the same version. Correction forms require a reason and show old/new values. Material correction triggers reevaluation and approval invalidation. A reviewer cannot directly set a hidden database decision to PASS.

## 14. Data model and suggested PostgreSQL schema

### 14.1 Conventions

- UUID primary keys; readable numbers are separate display fields.
- `tenant_id`, `legal_entity_id`, `created_at`/`updated_at` where appropriate; UTC `timestamptz` and separate business `date` fields.
- Money: `numeric(20,6)` or a documented stronger precision; quantities/prices may use `numeric(24,8)`. Currency minor units and rounding remain explicit.
- Immutable revisions for extracted/canonical/reference/rule/evaluation facts; mutable workflow projections use `row_version` optimistic locking.
- Composite tenant-scoped foreign keys prevent accidental cross-tenant associations. Application role must not bypass row-level security; test with non-owner database roles.
- Store searchable monetary/identity/status fields in typed columns. Use JSONB for extensible extraction artifacts and configuration, not as a substitute for every relational constraint.
- Delete financial records through permitted lifecycle/retention workflows. Avoid cascading away evidence of a decision.

### 14.2 Tables and important relationships

| Table | Important fields and relationships |
|---|---|
| tenants / legal_entities | Tenant, entity code/name, base currency, timezone |
| users / role_assignments / delegations | Identity subject, scoped role, effective dates, delegated authority |
| import_batches / import_rows | Source, mapping/version, file, sheet/row, raw values, validation status, resulting transaction |
| uploads / documents | Session, owner, object key/version, SHA-256, MIME, bytes, safety/processing state |
| document_versions / document_pages | Parent original, artifact keys, dimensions, transforms, native text, quality metrics, per-page hash |
| document_fingerprints | Document/page, algorithm/version, pHash bits, normalized content fingerprint |
| extraction_runs / extracted_fields | Provider/model/schema/prompt versions, raw output, value/status, source locator, quality method |
| transactions | Stable identity, branch, latest version pointer, workflow projection, row version |
| transaction_versions | Immutable canonical payload, amount/currency/date, normalizer/schema version, content hash, author/reason |
| transaction_documents | Transaction version, document version, role, page range; many-to-many |
| invoice_details / invoice_lines | Version, vendor, printed/keyed number, PO refs, lines, quantities/prices/tax/components |
| expense_claims / expense_items | Version, employee, purpose/trip, category, requested amount, expense date, receipt links |
| receipt_allocations | Receipt/item, claimant/item, eligible amount/quantity, status, superseding allocation |
| vendors / vendor_versions | Stable master ID, approved identity, aliases/tax ID, status, categories, effective dates |
| vendor_payment_accounts | Version, encrypted details, equality token/key version, verification event/status |
| employees / employee_versions | Employment period, manager/grade/entity/cost center, status |
| purchase_orders / po_versions / po_lines | Vendor/entity/currency, approved status, ceiling, ordered lines, commitments |
| contracts / contract_versions / contract_lines | Vendor, effective periods, rates, ceiling, service requirements |
| goods_receipts / goods_receipt_lines | PO line, accepted/returned quantities, date/source/version |
| service_acceptances | Contract/PO milestone, accepted quantity/value, authorized actor |
| matching_allocations | Transaction line → PO/GRN/contract line, quantity/value, RESERVED/CONSUMED/RELEASED lifecycle |
| expense_policies / policy_versions | Dimensions, effective dates, allowances/units, receipt rules, immutable config hash |
| approval_policies / approval_policy_versions | Bands, role chain, automatic tiers, waiver/delegation rules |
| approval_requests / approval_steps / approval_actions | Transaction version, required chain, actor/action/time, authority snapshot, invalidation |
| budgets / budget_ledger / budget_reservations | Dimensions, allocation basis, immutable events, reservation owner/operation/status |
| fx_rates | Currency pair/date/rate/source/version |
| reference_imports / reference_snapshots / snapshot_members | Activated source versions and exact snapshot manifest |
| duplicate_candidates / duplicate_signals / duplicate_resolutions | Pair of versions/documents, comparison features, disposition, evidence |
| rule_definitions / rule_versions / rule_results | Stable rule ID, version/config, evaluation result and effect |
| evaluations / decisions | Immutable run inputs/versions/mode, completeness, decision/reasons/eligibility, supersedes link |
| evidence_objects / rule_result_evidence | Typed references, locators and snapshots; one result to many evidence objects |
| feature_snapshots / feature_lineage | Feature schema/order/values/cutoff and source manifest |
| model_versions / model_scores / model_explanations | Artifact/checksum, registry state, score kind, SHAP data and output space |
| review_cases / review_actions / waivers | Queue ownership, expected version, reason/evidence, authority and expiry |
| feedback_labels / dataset_versions / training_runs | Adjudication provenance, dataset manifest, metrics, approvals |
| reports | Evaluation, format, artifact/content hash, generation status |
| audit_events / audit_anchors | Append-only event payload/hash chain and externally anchored digest |
| jobs / outbox_events / idempotency_records | Durable stages, attempts/lease, publish state, scoped request hash/response |

### 14.3 Core SQL sketch

This is a design sketch for initial migrations, not a complete runnable production schema. Implement the omitted reference tables and enums through Alembic, then add all foreign keys and RLS policies. IDs in JSON examples below are valid UUIDs.

```sql
CREATE TABLE transactions (
    tenant_id uuid NOT NULL,
    legal_entity_id uuid NOT NULL,
    id uuid NOT NULL,
    branch text NOT NULL CHECK (branch IN ('VENDOR_INVOICE', 'EMPLOYEE_EXPENSE')),
    latest_version integer NOT NULL DEFAULT 1 CHECK (latest_version > 0),
    processing_state text NOT NULL,
    row_version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);

CREATE TABLE transaction_versions (
    tenant_id uuid NOT NULL,
    transaction_id uuid NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    canonical_schema_version text NOT NULL,
    payload jsonb NOT NULL,
    total_amount numeric(20,6),
    currency char(3),
    business_date date,
    content_sha256 char(64) NOT NULL,
    created_by uuid NOT NULL,
    change_reason text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, transaction_id, version),
    FOREIGN KEY (tenant_id, transaction_id)
      REFERENCES transactions (tenant_id, id)
);

CREATE TABLE evaluations (
    tenant_id uuid NOT NULL,
    id uuid NOT NULL,
    transaction_id uuid NOT NULL,
    transaction_version integer NOT NULL,
    reference_snapshot_id uuid NOT NULL,
    ruleset_version text NOT NULL,
    decision_policy_version text NOT NULL,
    model_version text,
    evaluation_mode text NOT NULL,
    completeness text NOT NULL,
    decision text CHECK (decision IN ('PASS', 'REVIEW', 'HOLD')),
    eligible boolean NOT NULL DEFAULT false,
    input_digest char(64) NOT NULL,
    supersedes_id uuid,
    evaluated_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, transaction_id, transaction_version)
      REFERENCES transaction_versions (tenant_id, transaction_id, version),
    FOREIGN KEY (tenant_id, supersedes_id) REFERENCES evaluations (tenant_id, id),
    CHECK (NOT eligible OR (decision IS NOT NULL AND decision = 'PASS'
                           AND completeness = 'COMPLETE'))
);

CREATE TABLE rule_results (
    tenant_id uuid NOT NULL,
    id uuid NOT NULL,
    evaluation_id uuid NOT NULL,
    rule_id text NOT NULL,
    rule_version text NOT NULL,
    status text NOT NULL CHECK
      (status IN ('PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE', 'ERROR')),
    decision_effect text NOT NULL CHECK (decision_effect IN ('NONE', 'REVIEW', 'HOLD')),
    reason_code text NOT NULL,
    result jsonb NOT NULL,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, evaluation_id) REFERENCES evaluations (tenant_id, id),
    UNIQUE (tenant_id, evaluation_id, rule_id, rule_version)
);

CREATE TABLE idempotency_records (
    tenant_id uuid NOT NULL,
    endpoint text NOT NULL,
    idempotency_key text NOT NULL,
    request_sha256 char(64) NOT NULL,
    response_status integer,
    response_body jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, endpoint, idempotency_key)
);
```

Versioned evaluations are immutable facts. Whether an old PASS is still current/eligible is derived through a separate eligibility projection and current version/reservation checks; do not rewrite the old row to hide history. Finalization validates reference snapshots, policy freshness and allocation consistency beyond what the sketch's CHECK constraints express.

### 14.4 Indexes, constraints and retention

Add indexes on scoped document SHA-256; vendor+conservative/aggressive number key; vendor/currency/amount/date; merchant/date/amount; PO/GRN foreign keys; queue decision/owner/created time; audit sequence; and job lease/status. Index fuzzy candidate retrieval only after benchmarking (e.g., trigram candidate narrowing). Avoid comparing every image to every image.

Uniqueness belongs on source-system/version IDs, ledger operation keys, job stage keys and idempotency actions. A fingerprint index is normally nonunique. Matching-pair keys must normalize left/right order and reject self-matches. Prevent overlapping active policy ranges, invalid numeric signs for supported document types, and cross-tenant foreign keys. Validate cumulative allocation invariants transactionally.

Keep originals, revisions, references and model artifacts long enough to reproduce retained decisions. Retention periods and legal holds are organization-specific configuration, not hard-coded statutory claims. Support authorized erasure/pseudonymization with a recorded retention event where appropriate; never promise both irrevocable personal-data storage and unrestricted deletion.

## 15. API design

Use `/api/v1`, OpenAPI generated from Pydantic models, stable error codes, cursor pagination and server-side authorization on every resource. Amounts are decimal strings; dates are ISO dates; timestamps include timezone. Resource IDs must never bypass tenant/entity access checks.

| Method and path | Purpose | Key behavior |
|---|---|---|
| POST /uploads | Create upload session | Idempotency-Key; returns scoped destination and upload ID |
| POST /uploads/{id}/complete | Verify/store/schedule document | 202 with document/job IDs after integrity checks |
| GET /documents/{id} | Metadata, pages, processing status | Authorized, redacted as needed |
| GET /documents/{id}/pages/{page} | Safe preview access | Short-lived authorized URL or streamed preview |
| POST /imports/preview | Validate CSV/XLSX and mapping | Returns preview ID, row errors, proposed mappings |
| POST /imports/{id}/commit | Commit validated rows | Idempotent; per-row results and batch job |
| GET /imports/{id} | Batch status/results | Cursor-paginated errors/created resources |
| POST /transactions | Create structured invoice/claim | Branch-specific validation; document/reference IDs |
| GET /transactions | Search/list | Filters, cursor, stable sort, authorized scope |
| GET /transactions/{id} | Current version and status | ETag/version plus latest evaluation pointer |
| POST /transactions/{id}/revisions | Correct facts | Expected version, reason/evidence; creates revision |
| POST /transactions/{id}/evaluate | Queue evaluation | Idempotent, explicit mode; no synchronous long VLM call |
| GET /jobs/{id} | Worker progress/failure | Stage, retryability, safe error details |
| GET /evaluations/{id} | Immutable results | Rules, versions, completeness and decision |
| GET /evaluations/{id}/evidence | Authorized evidence bundle | Resolves source/matched IDs |
| GET /evaluations/{id}/report | Deterministic report | JSON or HTML; versioned |
| POST /evaluations/{id}/exports | Generate export | Async for large PDF/CSV; export permission |
| GET /reviews | Exception queue | Includes REVIEW and HOLD with owner/reason |
| POST /reviews/{id}/assign | Acquire/change assignment | Expected version and lease/role check |
| POST /reviews/{id}/actions | Request info, resolve, propose waiver | Typed action, reason/evidence; no unrestricted set-PASS |
| POST /duplicate-candidates/{id}/resolution | Distinct/shared/confirmed duplicate | Pair versions, authorized reason/evidence |
| GET /transactions/{id}/approvals | Required chain/actions | Actual authority and invalidation status |
| POST /approval-steps/{id}/actions | Approve/decline | Bound transaction version; authority/SoD checks |
| POST /reference-imports | Stage master/PO/GRN/budget import | Admin permission, validation/dry run |
| POST /reference-imports/{id}/activate | Activate versioned data | Explicit authorized action and audit |
| GET /policies | Read applicable/versioned policies | Scope and effective dates |
| POST /policies/{id}/versions | Create validated draft | Never overwrites active version |
| POST /policy-versions/{id}/activate | Activate approved policy | Impact preview and authority |
| GET /audit-events | Search authorized audit trail | Immutable, cursor-paginated |
| POST /feedback-labels | Record adjudication label | Provenance, evidence, label taxonomy |
| POST /training-runs | Start offline training job | ML-admin only, dataset/model config IDs |
| POST /model-versions/{id}/activate | Promote approved model | Evaluation gates, audit and rollback target |
| GET /health/live | Process health | Minimal public information |
| GET /health/ready | Required service readiness | No secrets or detailed internals |

No payment endpoint is included. A future ERP handoff requires its own design and authorization.

Return 400 for malformed requests, 401/403 for auth failures, 404 for unavailable/inaccessible resources under the non-disclosure policy, 409 for stale writes/idempotency conflicts, 413 for size limits, 415 for unsupported types, 422 for schema/business input validation, 429 for rate limits, and 503 for unavailable service. A held finance transaction is a successfully evaluated resource, not an HTTP 500.

Standard error shape:

```json
{
  "error": {
    "code": "STALE_TRANSACTION_VERSION",
    "message": "This case changed after you opened it. Refresh before submitting.",
    "correlation_id": "corr-demo-409",
    "details": {"expected_version": 2, "current_version": 3},
    "retryable": false
  }
}
```

Outbox event envelopes include event ID/type/schema version, tenant/entity, aggregate ID/version, occurred-at time, correlation/causation IDs and a minimal payload. Do not publish raw document content or bank details on the queue. Consumer deduplication uses event ID and stage version. Delivery is at least once; financial effects must be idempotent.

## 16. Sample JSON objects

Examples are synthetic. Repeated UUIDs intentionally link objects. Display references such as PO-DEMO-100 are not primary keys. Financial decimals are strings; similarity/ML quantities may be ordinary JSON numbers. These examples illustrate contracts, not an assertion that a live system has evaluated them.

### 16.1 Canonical vendor invoice with field evidence

```json
{
  "schema_version": "canonical-v1",
  "tenant_id": "10000000-0000-4000-8000-000000000001",
  "legal_entity_id": "20000000-0000-4000-8000-000000000001",
  "transaction_id": "30000000-0000-4000-8000-000000000001",
  "version": 1,
  "branch": "VENDOR_INVOICE",
  "document_ids": ["40000000-0000-4000-8000-000000000001"],
  "vendor_id": "50000000-0000-4000-8000-000000000001",
  "invoice_number": "DEMO-INV-1001",
  "invoice_number_key": "DEMOINV1001",
  "normalizer_version": "norm-v1",
  "invoice_date": "2026-09-25",
  "currency": "INR",
  "po_id": "60000000-0000-4000-8000-000000000001",
  "po_display_number": "PO-DEMO-100",
  "subtotal": "100000.00",
  "document_discount": "0.00",
  "tax_total": "18000.00",
  "shipping": "0.00",
  "total": "118000.00",
  "tax_basis": "EXCLUSIVE",
  "lines": [{
    "line_id": "70000000-0000-4000-8000-000000000001",
    "description": "Demo monitors",
    "quantity": "100.0000",
    "uom": "EA",
    "unit_price": "1000.00",
    "line_discount": "0.00",
    "net_amount": "100000.00",
    "tax_rate": "0.18",
    "tax_amount": "18000.00",
    "gross_amount": "118000.00",
    "po_line_id": "71000000-0000-4000-8000-000000000001"
  }],
  "field_provenance": {
    "total": {
      "raw_text": "INR 118,000.00",
      "document_id": "40000000-0000-4000-8000-000000000001",
      "page": 1,
      "bbox": [0.70, 0.80, 0.95, 0.85],
      "coordinate_system": "normalized_original_page",
      "verification_status": "HUMAN_VERIFIED",
      "extraction_run_id": "72000000-0000-4000-8000-000000000001"
    }
  }
}
```

### 16.2 Canonical employee expense

```json
{
  "schema_version": "canonical-v1",
  "transaction_id": "30000000-0000-4000-8000-000000000002",
  "version": 1,
  "branch": "EMPLOYEE_EXPENSE",
  "employee_id": "51000000-0000-4000-8000-000000000001",
  "employee_identity_source": "AUTHENTICATED_CLAIM",
  "cost_center": "CC-DEMO-ENG",
  "trip_id": "TRIP-DEMO-20",
  "business_purpose": "Attend approved supplier workshop",
  "requested_reimbursement": "9000.00",
  "currency": "INR",
  "items": [{
    "item_id": "73000000-0000-4000-8000-000000000001",
    "category": "HOTEL",
    "expense_date": "2026-09-24",
    "local_timezone": "Asia/Kolkata",
    "merchant_name": "Example Business Hotel",
    "receipt_number": "R-DEMO-900",
    "receipt_document_id": "40000000-0000-4000-8000-000000000002",
    "receipt_total": "9000.00",
    "claimed_amount": "9000.00",
    "eligible_nights": 1,
    "company_paid_amount": "0.00",
    "applied_advance": "0.00",
    "policy_id": "EXP-HOTEL",
    "policy_version": "v1"
  }]
}
```

The expense example exceeds the illustrative INR 8,000/night policy by INR 1,000. Its final decision also depends on approvals, receipt allocation, budget and other checks; this input object alone is not a completed evaluation.

### 16.3 Duplicate comparison

```json
{
  "candidate_id": "74000000-0000-4000-8000-000000000001",
  "transaction_id": "30000000-0000-4000-8000-000000000002",
  "candidate_transaction_id": "30000000-0000-4000-8000-000000000003",
  "classification": "POSSIBLE_DUPLICATE",
  "candidate_display_number": "CLAIM-DEMO-OLD-07",
  "signals": {
    "same_currency": true,
    "amount_difference": "0.00",
    "date_difference_days": 0,
    "merchant_similarity": 0.98,
    "receipt_number_match": null,
    "phash_distance": 3,
    "phash_bits": 64,
    "same_sha256": false
  },
  "search_status": "COMPLETE",
  "shared_allocation_status": "UNRESOLVED",
  "rule_id": "DUP-003",
  "rule_version": "1",
  "decision_effect": "REVIEW",
  "evidence_document_ids": [
    "40000000-0000-4000-8000-000000000002",
    "40000000-0000-4000-8000-000000000003"
  ]
}
```

### 16.4 Three-way rule result

```json
{
  "rule_execution_id": "75000000-0000-4000-8000-000000000001",
  "rule_id": "GRN-001",
  "rule_version": "1",
  "status": "FAIL",
  "severity": "HIGH",
  "decision_effect": "HOLD",
  "reason_code": "RECEIVED_QUANTITY_SHORTFALL",
  "observed": {"billed_quantity": "100.0000", "uom": "EA"},
  "expected": {"maximum_new_billable_quantity": "80.0000", "uom": "EA"},
  "variance": "20.0000",
  "tolerance": "0.0000",
  "evidence": [
    {"kind": "TRANSACTION", "id": "30000000-0000-4000-8000-000000000001", "version": 1},
    {"kind": "PO_LINE", "id": "71000000-0000-4000-8000-000000000001", "version": 1},
    {"kind": "GRN_LINE", "id": "76000000-0000-4000-8000-000000000001", "version": 1}
  ],
  "message": "100 units billed; 80 accepted units remain available. Resolve the 20-unit difference."
}
```

### 16.5 Decision/report object

```json
{
  "report_schema_version": "report-v1",
  "evaluation_id": "80000000-0000-4000-8000-000000000001",
  "transaction_id": "30000000-0000-4000-8000-000000000001",
  "transaction_version": 1,
  "evaluated_at": "2026-09-28T10:00:00Z",
  "evaluation_mode": "RULES_ONLY",
  "completeness": "COMPLETE",
  "decision": "HOLD",
  "eligible": false,
  "reason_codes": ["RECEIVED_QUANTITY_SHORTFALL"],
  "rule_result_ids": ["75000000-0000-4000-8000-000000000001"],
  "check_summary": {"passed": 12, "failed": 1, "unknown": 0, "not_applicable": 3, "error": 0},
  "model": {"status": "NOT_CONFIGURED", "score": null, "explanation": null},
  "versions": {
    "ruleset": "rules-v1",
    "decision_policy": "decision-v1",
    "reference_snapshot_id": "81000000-0000-4000-8000-000000000001"
  },
  "next_actions": [{
    "action": "VERIFY_GOODS_RECEIPT",
    "reason": "Confirm receipt of the remaining 20 units or correct the invoice.",
    "related_rule_id": "GRN-001"
  }],
  "review_case_id": "82000000-0000-4000-8000-000000000001",
  "supersedes_evaluation_id": null
}
```

This report illustration abbreviates `rule_result_ids`: the actual API MUST include all 16 persisted results or a resolvable paginated collection matching the summary. No result may be omitted from an exported authoritative report merely because it passed.

### 16.6 Model explanation in explicit output space

```json
{
  "model_version": "demo-xgb-v1",
  "score_kind": "exception_probability",
  "raw_model_probability": 0.6681877722,
  "calibrated_probability": null,
  "explanation_status": "AVAILABLE",
  "output_space": "raw_margin_log_odds",
  "base_value": -1.5,
  "contributions": [
    {"feature": "vendor_amount_ratio", "value": 4.2, "shap_value": 1.2},
    {"feature": "claims_near_limit_7d", "value": 3, "shap_value": 0.6},
    {"feature": "max_duplicate_similarity", "value": 0.91, "shap_value": 0.4}
  ],
  "explained_output": 0.7,
  "additivity_residual": 0.0,
  "feature_snapshot_id": "83000000-0000-4000-8000-000000000001",
  "background_dataset_version": "demo-background-v1"
}
```

This is mathematical illustration, not trained-model output. Here -1.5 + 1.2 + 0.6 + 0.4 = 0.7; sigmoid(0.7) is approximately 0.6682. Contributions are log-odds units, not probability points.

### 16.7 Review action and audit payload

```json
{
  "action_id": "84000000-0000-4000-8000-000000000001",
  "review_case_id": "82000000-0000-4000-8000-000000000001",
  "action_type": "REQUEST_INFORMATION",
  "expected_transaction_version": 1,
  "expected_review_version": 1,
  "reason_code": "RECEIPT_EVIDENCE_REQUIRED",
  "comment": "Please provide the goods receipt for the remaining 20 units.",
  "evidence_ids": ["76000000-0000-4000-8000-000000000001"],
  "actor_id": "85000000-0000-4000-8000-000000000001",
  "occurred_at": "2026-09-28T10:15:00Z"
}
```

Actor and timestamp are assigned/verified server-side, not trusted from arbitrary clients. Requesting information creates an internal workflow action; automatically emailing anyone is outside the initial scope.

## 17. Audit logging and reproducibility

Log accepted/rejected uploads, quarantine results, classification/extraction versions, normalization, reference imports/activation, every evaluation, rule outcomes, model/version changes, document access/export where appropriate, corrections, approvals, waivers, assignments, duplicate resolutions and budget/allocation changes.

Each audit event contains event/tenant/entity IDs, a per-tenant sequence, actor type/ID, action, object/version, timestamp, correlation/causation IDs, before/after digest or redacted diff, reason, evidence references, and previous/current event hashes. Use a canonical serialization and serialize sequence/hash assignment per tenant. The event writer must append within the same database transaction as the business change, or use a transactionally written outbox followed by a verified immutable sink. Audit persistence failure prevents committing an eligibility-changing action.

An application append-only table is not tamper-proof against database administrators. Restrict UPDATE/DELETE, separate operational and audit roles, monitor attempts, and periodically anchor signed digests/export batches to separately controlled immutable storage. A hash chain alone cannot detect an attacker rewriting the entire chain without an external trusted anchor. Record retention/legal-hold policy and key rotation.

Replay uses original canonical/reference/rule/model/feature versions and fixed evaluation time. Rules-only results must reproduce exactly. Reuse the stored extraction output for decision replay: re-running a VLM may change output and is a new extraction/evaluation, not deterministic replay. Store model artifact and preprocessing hashes; explain when a provider artifact is unavailable for exact reexecution. Authorized audit readers can distinguish original and superseding decisions.

## 18. Security and access control

### 18.1 Role matrix

| Role | Allowed actions | Explicit restrictions |
|---|---|---|
| Submitter/employee | Own uploads/claims, correction requests, own status | No other employee claims, no self-approval, no policy edits |
| Finance reviewer | Assigned/scoped cases, evidence, corrections, duplicate resolutions | Cannot change bank master or bypass non-waivable controls |
| Approver | Approve/decline within authority and scope | No self-approval; no approval of stale versions |
| Master-data steward | Stage/verify reference changes | Separate authorization for activation and payment-account verification |
| Policy administrator/owner | Draft/approve/activate policy as configured | Changes audited; no hidden rewrite of old policy versions |
| Auditor | Read scoped decisions/evidence/audit exports | No mutation or operational approval |
| ML administrator | Governed datasets/training/model proposals | No unilateral bypass of deployment gates or finance controls |
| Service worker | Minimum stage-specific read/write access | No interactive user privileges or unrestricted document exports |

Enforce resource ownership and tenant/entity scope in API services and database policy. A URL containing a UUID is not authorization. Validate JWT issuer, audience, signature and expiry; map trusted identity claims to server-side roles. Do not accept a role or tenant supplied in an upload form. Test the app using a database role that cannot bypass RLS. Scope background jobs explicitly; pooled connections must clear tenant context before reuse.

### 18.2 Data and document defenses

- TLS, encryption at rest, Key Vault/managed identity in Azure, least privilege and key rotation.
- Private Blob containers; short-lived scoped links; no original-document public URLs.
- Allowlisted input formats with MIME sniffing, malware checks, parser limits and isolated workers.
- Treat document and spreadsheet content as untrusted, including instructions addressed to the model.
- No external URL fetching from document text. Validate any administrator-configured provider endpoint to prevent SSRF.
- No model access to secrets, unrestricted tools, database credentials or cross-tenant retrieval.
- Safe HTML rendering and escaping; never render extracted HTML as trusted markup.
- Protect CSV exports against spreadsheet formula injection while preserving stored source values.
- CSRF protection for cookie-authenticated mutations; secure cookies, restrictive CORS and appropriate security headers.
- Rate limits and per-tenant quotas for uploads, inference and exports; dependency vulnerability scans and artifact checksums.
- Redact tokens, full bank accounts and unnecessary personal data from logs, error reports and telemetry.
- Provider data-retention, residency, training use and model license must be reviewed before sending real documents. Select a compatible provider/runtime within authorized constraints.
- Do not store sensitive free-form model reasoning. Store concise extraction observations, evidence and structured decisions.

### 18.3 Financial abuse controls

Separate submitter, approver, bank-master verifier and policy owner roles. Record all waivers and prevent ordinary admin UI convenience from becoming an undocumented bypass. A future payment integration must consume an explicit eligibility token/version with expiry and revalidation, never simply trust the last displayed PASS.

## 19. Reliability, observability and Azure deployment

### 19.1 Durable work execution

Use a transactionally written outbox and leased jobs in the MVP. A stage key consists of tenant, transaction/document version, stage name and stage implementation version. Workers claim jobs with a lease, renew during long work, and release/expire safely after crashes. At-least-once delivery is expected; retries must converge without duplicate ledger or audit business effects.

Use exponential backoff with jitter, bounded attempts and dead-letter state. Distinguish retryable provider/storage/database failures from corrupt documents, unsupported formats and missing user data. Do not endlessly retry a permanent schema or authorization error. Preserve the last successful stage and partial extraction artifacts.

External Blob writes cannot share a PostgreSQL transaction. Use staged object keys and metadata states, complete a verified finalize step, and run reconciliation for orphan objects/missing metadata. Never mark a document AVAILABLE solely because an upload was attempted. Similarly, model/report artifacts become active only after checksum and registry/persistence confirmation.

Readiness separates API availability from VLM readiness. Circuit breakers and a clearly labeled fallback mode prevent inference outages from consuming the whole queue. Required controls stay unresolved during outages. Cancelled/superseded jobs must check version/cancellation before committing results. Reprocessing never overwrites a newer review action.

### 19.2 Observability

Emit structured logs and traces using correlation ID, job/stage, document/transaction/evaluation IDs and tenant-safe metadata. Track:

- Upload success/quarantine/rejection, queue age, retry counts and dead-letter backlog.
- Stage latency, VLM time/usage, page counts, extraction abstention and correction rates.
- Rule errors, stale references, candidate-search completion and evidence-link failures.
- PASS/REVIEW/HOLD distributions by branch, queue SLA and reviewer resolution times.
- Budget reservation conflicts, deadlocks, stale writes and approval invalidations.
- Model/explainer availability, feature drift and delayed outcome performance.
- Audit append failures, access anomalies, backup status and restore verification.

Alerts must be actionable and avoid sensitive payloads. Expose aggregate business metrics only to authorized users. A drift alert is not an accusation about a person.

### 19.3 Proposed development service targets

These are targets to measure, not guarantees or reported achievements. Record machine size, data size, provider, page count and concurrency with benchmarks.

| Area | Proposed initial target |
|---|---|
| Small list/detail API | p95 <500 ms on seeded 10k transactions, excluding document transfer |
| Enqueue/finalize metadata | p95 <2 seconds excluding upload/scan/inference |
| Rules/matching evaluation | p95 <5 seconds at 10k history and 10 concurrent evaluations |
| Typical 1–3-page document | Target <90 seconds end to end; publish actual provider measurement |
| Structured 1k-row batch | Target <60 seconds rules-only on stated local benchmark |
| Required evidence | 100% findings have authorized resolvable references or explicit missing-data evidence |
| Financial concurrency | Zero duplicate reservations/over-allocation in stress and crash-retry fixtures |
| Availability goal for pilot | 99.5% monthly, excluding agreed maintenance; establish actual monitoring |
| Recovery goals for pilot | Proposed RPO 15 minutes, RTO 4 hours, subject to provisioned backups and restore drills |

GPU cold start, provider quotas and document complexity may prevent the proposed latency targets. Report the measured limitation; do not hide it with hard-coded progress or demo results.

### 19.4 Deployment plan

Local development: containers for PostgreSQL, API and worker; Next.js development app; local Blob adapter or Azurite; fixture extraction by default. A demo must be runnable without paid credentials. Real extraction is enabled through configuration and clearly marked in the UI.

Azure pilot topology:

1. Container Registry for immutable signed/tagged application images.
2. Web/API compute on one selected supported Azure service; worker compute separately scalable by queue depth.
3. Azure Database for PostgreSQL with backups, restricted networking and migration discipline.
4. Private Blob containers for originals, previews, reports and model artifacts, with lifecycle rules.
5. Key Vault and managed identities; secrets never baked into images or the repository.
6. Service Bus when replacing the PostgreSQL jobs transport; business idempotency remains mandatory.
7. Entra ID for enterprise identity and scoped roles.
8. Central logs/traces/metrics and alerting; protected readiness/liveness endpoints.
9. VLM on a separately costed compatible GPU service/runtime, or an approved adapter. Do not assume ordinary web compute can serve the chosen VLM efficiently.

Use infrastructure as code (choose Bicep or Terraform), dev/staging/prod isolation, explicit resource tags and budget limits. Build/test/scan images, run migrations as a controlled step, deploy to staging, run smoke/rollback checks, then promote with authorized deployment workflow. Use backward-compatible expand/contract schema migrations; do not rely on destructive rollback. Cloud account, subscription, region and spend ceiling are genuine external inputs needed before provisioning.

## 20. Repository structure

```text
ap-exception-assistant/
├── README.md
├── AGENTS.md
├── .env.example
├── .gitignore
├── compose.yaml
├── Makefile
├── docs/
│   ├── AP_Exception_Assistant_Codex_Spec.md
│   ├── progress.md
│   ├── assumptions.md
│   ├── data_dictionary.md
│   ├── threat_model.md
│   ├── runbooks/
│   └── adr/
├── apps/
│   ├── web/
│   │   ├── src/app/
│   │   ├── src/components/
│   │   ├── src/features/{uploads,transactions,reviews,evidence,approvals}/
│   │   ├── src/lib/{api,auth,formatting}/
│   │   └── tests/
│   └── api/
│       ├── pyproject.toml
│       ├── app/
│       │   ├── main.py
│       │   ├── api/v1/
│       │   ├── core/{config,security,logging,errors}/
│       │   ├── db/{models,repositories,session}/
│       │   ├── schemas/
│       │   ├── domain/{money,identity,states,evidence}/
│       │   ├── services/{intake,evaluation,review,approval,reporting}/
│       │   ├── documents/{safety,preprocess,classify,normalize}/
│       │   ├── extraction/{base,fixture,typellm_adapter,ocr_adapter}/
│       │   ├── matching/{candidates,text,image,three_way,allocations}/
│       │   ├── rules/{base,registry,vendor,employee,shared}/
│       │   ├── risk/{features,model_adapter,decision,explanations}/
│       │   ├── integrations/{storage,queue,identity,erp}/
│       │   └── audit/
│       ├── migrations/
│       └── tests/{unit,integration,contract,security,fixtures}/
├── workers/
│   └── processor/
├── packages/
│   └── api-client/                 # generated TypeScript OpenAPI client
├── ml/
│   ├── feature_specs/
│   ├── datasets/manifests/         # no real confidential training data in Git
│   ├── training/
│   ├── evaluation/
│   └── model_cards/
├── data/
│   ├── synthetic/
│   ├── reference_templates/
│   └── golden_cases/
├── tests/{e2e,performance,replay}/
├── infra/{local,azure}/
└── scripts/{seed,verify,benchmark}/
```

Directories in braces are suggested sibling directories, not literal brace-containing folder names. Keep finance domain/rule code independent of FastAPI request handlers and the web framework. Workers import the same domain package as the API; do not duplicate financial logic. Generate frontend contracts from OpenAPI. Commit migrations and lockfiles. Keep uploaded documents, secrets, model weights and generated personal-data exports out of Git.

The README must cover prerequisites, one-command local start, seed/reset, fixture versus live extraction, test commands, demo identities, troubleshooting and production differences. Suggested task commands (`make dev`, `make seed`, `make test`, `make test-e2e`, `make benchmark`) are project conventions to implement, not tools already present.

## 21. Phased Codex implementation plan

Each phase must leave a runnable system, update progress/assumptions, identify limitations and pass its exit gate. Do not build every optional feature before proving the two core workflows. Task IDs below can become issues or checklist items.

### Phase 0 — Contracts and feasibility

- P0-01: Inspect existing repository, applicable AGENTS.md and dependencies; avoid replacing existing working structure unnecessarily.
- P0-02: Record domain glossary, state enums, Decimal/currency conventions, evidence schema and decisions about unknown data.
- P0-03: Create synthetic vendor/employee/PO/GRN/policy/budget/approval fixtures and a small adjudicated golden dataset.
- P0-04: Define ExtractionAdapter and run a TypeLLM/VLM spike on at least 10 varied synthetic documents, including one multi-page line-item invoice and one poor receipt.
- P0-05: Verify runtime compatibility, null handling, line-item strategy, evidence granularity, latency, license and hardware needs; pin versions. If blocked, use the fixture adapter and record the missing prerequisite.
- P0-06: Record initial architectural decisions for identity, policy matching, queue/storage adapters and baseline decision mode.

Exit: versioned contracts, compatibility notes, reproducible synthetic fixtures, and no unsupported provider assumptions.

### Phase 1 — Rules-first vertical slice for both branches

- P1-01: Scaffold API, frontend, PostgreSQL migrations, local storage and durable jobs/outbox.
- P1-02: Implement structured transaction creation/import, tenant-scoped identity and validated canonical records.
- P1-03: Implement required-field/arithmetic checks, approved party checks, simple exact business duplicate detection, basic expense allowance, budget and approval checks.
- P1-04: Implement deterministic decision precedence, immutable evaluations, evidence, audit and JSON/HTML reports.
- P1-05: Build upload/import status, list, case detail and exception queue with source/evidence links.
- P1-06: Seed a complete clean vendor case and clean employee case with required approvals, plus duplicate and limit exceptions.

Exit: a user can submit synthetic structured data for both branches and see real persisted PASS/REVIEW/HOLD results with cited rules. No hard-coded UI outcomes and no ML dependency.

### Phase 2 — Real document ingestion and extraction

- P2-01: Secure upload/finalization, scan/quarantine, size/page/pixel limits and original storage.
- P2-02: PyMuPDF/OpenCV preprocessing, native text, quality metrics, source mappings and fingerprints.
- P2-03: TypeLLM adapter, bounded header/line extraction, optional OCR fallback and provider disagreement handling.
- P2-04: Normalization traces, strict canonical validation and source-linked correction UI.
- P2-05: Import mapping/row evidence and multi-document/receipt attachment support.

Exit: representative PDFs/photos produce versioned facts and evidence. Unreadable or ambiguous critical fields cannot PASS. Fixture and live extraction modes are clearly distinguishable.

### Phase 3 — Complete finance matching and controls

- P3-01: Versioned reference import/activation and exact/ambiguous identity resolution.
- P3-02: PO/contract/GRN/service matching with partial deliveries, prior allocations, returns, UOM conversions and tolerances.
- P3-03: Fuzzy/business duplicate comparison and pHash candidate detection with side-by-side evidence.
- P3-04: Full employee policy dimensions, daily/trip aggregation, shared receipts, card/advance offsets and split-pattern review.
- P3-05: Atomic budget commitment conversion/reservation and concurrency-safe duplicate/capacity finalization.
- P3-06: Complete approval hierarchy, delegation, separation of duties, stale approval invalidation and explicit waivers.

Exit: all deterministic finance acceptance cases pass, including concurrent submissions and cumulative quantity/budget cases.

### Phase 4 — Human workflow and operational reliability

- P4-01: Reviewer ownership/version conflicts, correction and resolution actions, authorization-aware evidence links.
- P4-02: Superseding evaluations, cancellation, ledger compensation and eligibility invalidation.
- P4-03: Retries, dead-letter inspection, dependency outages, reconciliation and audit replay.
- P4-04: Accessible dashboard, filter/export controls, audit timeline and report generation.

Exit: a reviewer resolves an exception without losing the original decision; failure/retry tests show no duplicated financial effects.

### Phase 5 — Measured ML and explanations

- P5-01: Point-in-time features and transparent anomaly baseline.
- P5-02: Adjudicated feedback, PASS audit sampling and versioned dataset manifests.
- P5-03: Train/evaluate one supervised model only if data quality/quantity support it; otherwise retain baseline and state the limitation.
- P5-04: Calibrate/routing threshold evaluation and compatible SHAP with output-space/additivity checks.
- P5-05: Registry, shadow activation, drift monitoring, rollback and retraining runbook.

Exit: honest held-out metrics and model card, or explicitly documented rules/anomaly-only mode. No fabricated ML performance. Model escalation cannot override mandatory controls.

### Phase 6 — Azure pilot and handoff

- P6-01: Infrastructure as code, identities/secrets, private storage, backups and monitoring.
- P6-02: CI/CD, migration/deployment checks, staging smoke test and rollback exercise.
- P6-03: Load benchmark, security tests and restore drill against the provisioned configuration.
- P6-04: Demo scenario, deployment/runbook documentation and final coverage matrix.

Exit: authorized pilot deployment meets the recorded release gates and measured targets, or local delivery explicitly lists pending external infrastructure inputs. Do not call a local demo production-ready.

## 22. Test strategy and synthetic datasets

### 22.1 Test layers

| Layer | Required focus |
|---|---|
| Unit | Money/rounding, dates, normalization collisions, each deterministic rule, policy precedence, missing-data behavior |
| Property/invariant | No allocation above capacity; no negative available balance under valid ledger transitions; adding a mandatory failure cannot change HOLD to PASS |
| Database integration | Tenant foreign keys/RLS, migrations, idempotency, outbox atomicity, locking, cancellation/reversal |
| Adapter contract | Fixture/TypeLLM/OCR output contracts, nullable fields, unsupported formats, provider timeout/malformed results |
| Extraction benchmark | Critical-field accuracy, line coverage, source locator accuracy, scans/photos/multi-page documents |
| Matching benchmark | Exact/fuzzy/pHash precision-recall, image transforms, same-template negatives and shared receipts |
| API authorization | Every read/write/export role, forged tenant IDs, inaccessible evidence and stale versions |
| End-to-end | Both branches from upload/import to report, human correction, approval and superseding evaluation |
| ML evaluation | Point-in-time leakage checks, duplicate-group splits, calibration, SHAP units/additivity, unavailable model |
| Reliability | Crash after Blob write, after outbox commit, during finalization; retry/dead letter/reconciliation |
| Performance | Indexed search at 10k+ history, bounded candidate retrieval, concurrent budget/GRN claims |
| Replay | Same pinned deterministic inputs produce identical findings and decision |

Use pytest for Python and a browser testing framework such as Playwright for UI flows. Test financial behavior and invariants, not fragile internal implementation details. External inference tests should be opt-in; normal CI must work without paid credentials. Maintain golden expected decisions and evidence IDs, but do not snapshot irrelevant timestamps.

### 22.2 Mandatory test cases

| ID | Scenario | Expected result |
|---|---|---|
| T01 | Clean vendor invoice, matching PO/GRN, sufficient budget, complete approvals | PASS with all required controls and evidence |
| T02 | Same invoice number from different vendors | No duplicate based on number alone |
| T03 | Same vendor/number/date/amount/currency already paid | HOLD under verified duplicate rule, cites prior transaction |
| T04 | Invoice-number punctuation/case variations | Candidate match with normalization trace |
| T05 | Aggressive normalization collides for two legitimate series | REVIEW or DISTINCT resolution, no silent merge |
| T06 | Same file is retried with same idempotency key | Same resource and no new financial effects |
| T07 | Independent second transaction uses same receipt | Duplicate analysis, not silently discarded upload |
| T08 | PO 100, received 80, prior billed 30, new billed 70 | HOLD for 20-unit shortfall, cites prior allocations |
| T09 | Service contract requires acceptance but none exists | HOLD, not inferred delivery |
| T10 | Item price exceeds configured tolerance | Exact variance and rule-specific REVIEW/HOLD |
| T11 | Tax/line total mismatch | Finding cites arithmetic operands and source fields |
| T12 | Invoice requests new bank account | HOLD; vendor master unchanged |
| T13 | Valid employee, allowed expense, policy/budget/approvals satisfied | PASS |
| T14 | INR 15,000 hotel with two verified nights, INR 8,000/night limit | Category-limit check PASS |
| T15 | Same INR 15,000 hotel with unknown nights | REVIEW, no assumed night count |
| T16 | Three meals total INR 1,800 against INR 1,500/day | Aggregate policy finding with all claim IDs |
| T17 | Same receipt resized/compressed and claimed by another employee | Candidate found on supported benchmark transform; authorized comparison |
| T18 | Similar receipt template but different actual purchase | No confirmed duplicate from pHash alone |
| T19 | Authorized shared receipt split within eligible total | Allocation check PASS; no automatic double-claim conclusion |
| T20 | Shared receipt allocations exceed eligible total | HOLD with allocation evidence |
| T21 | Expense already paid by company card | HOLD for confirmed double reimbursement request |
| T22 | Two individually permitted amounts sum above limit near threshold | Possible split finding, REVIEW without accusation |
| T23 | Two concurrent non-PO claims each 80, budget remaining 100 | At most one obtains PASS reservation; other HOLD |
| T24 | PO commitment already covers invoice | No double budget deduction |
| T25 | Two concurrent bills compete for same accepted GRN capacity | No over-allocation; losing case reevaluated |
| T26 | Mandatory approval absent or insufficient authority | HOLD, exact missing step/authority evidence |
| T27 | Submitter tries self-approval or forged approver ID | Rejected and audited |
| T28 | Amount materially changes after approval | Old approval invalidated and eligibility recomputed |
| T29 | Critical extraction unknown or provider disagreement | REVIEW; no invented amount/vendor/currency |
| T30 | Low ML score but mandatory rule failure | HOLD remains |
| T31 | High ML score, otherwise complete controls | REVIEW, model explanation separate from rule evidence |
| T32 | Model disabled in authorized RULES_ONLY mode | No score; rules may PASS |
| T33 | Required model/reference unavailable | Explicit degraded/incomplete state and configured REVIEW/HOLD |
| T34 | SHAP raw margin contributions | Additivity against margin; no false probability-point labels |
| T35 | Request accesses another tenant's document/evaluation/export | Access denied/no sensitive disclosure |
| T36 | Reviewer submits against stale transaction version | 409; no overwritten newer data |
| T37 | Worker crashes and retries finalization | One ledger effect and one logical decision commit |
| T38 | Audit persistence fails | Eligibility-changing transaction does not commit |
| T39 | Credit note or unsupported multi-document layout in MVP | Recognized unsupported path, REVIEW rather than forced positive bill |
| T40 | Policy gap/overlap or stale master import | UNKNOWN/ERROR with evidence; no permissive fallback |
| T41 | Malicious receipt says to ignore policy | Text treated as data; controls unchanged |
| T42 | Retained evaluation replay after policy changes | Original pinned result reproduced; new policy produces separate evaluation |

### 22.3 Dataset construction

Seed at least 20 vendors, 30 employees, 50 PO lines, partial receipts/returns, contracts/service acceptances, three cost centers, two currencies with explicit synthetic FX records, several policy versions and a complete approval matrix. Create at least 200 synthetic transactions covering both branches, plus a generated 10k-history performance dataset.

Golden documents should include clean digital PDFs, scanned PDFs, photographs, rotated/blurred receipts, multi-page tables, repeated headers, ambiguous dates, inclusive/exclusive tax, different number series, and receipts with the same template but different totals. Pair every case with expected extracted facts, references, rules and decision. Retain transformation metadata for image duplicate tests.

Keep training, validation, test and demo fixtures distinct where ML metrics are reported. Do not claim a 200-row synthetic dataset proves real-world generalization. If using a public dataset, record license, provenance, permitted uses and de-identification; do not silently mix it with real institutional data.

## 23. Acceptance criteria and release gates

### 23.1 Functional gates

- AC01: Both branches work end to end with persistent records, not only a UI mock or notebook.
- AC02: Required-field, amount/tax/date, party, duplicate, PO/contract/GRN, expense policy, budget and approval controls are implemented with explicit applicability.
- AC03: Every finding resolves to its rule/version, current transaction and real source/matched evidence, or explains the specific missing evidence.
- AC04: PASS only occurs after all applicable required controls complete, with sufficient fresh capacity and approvals; no payment is executed.
- AC05: REVIEW/HOLD queues explain the next action and support authorized correction/resolution.
- AC06: Exact and fuzzy duplicate behavior distinguishes retries, true repeated obligations, similar records and legitimate shared allocations.
- AC07: Raw documents, extracted facts, canonical revisions, human changes and superseded decisions remain traceable.
- AC08: Final terminology is PASS/REVIEW/HOLD throughout APIs, UI, reports and fixtures. Human decline is a separate workflow result.

### 23.2 Integrity and security gates

- AC09: T01–T42 pass or an explicitly out-of-phase optional case is marked unsupported without enabling unsafe PASS. Core deterministic/concurrency/security cases cannot be waived for production.
- AC10: Tenant/entity isolation, role restrictions, self-approval prevention and stale-write protections pass integration tests.
- AC11: Concurrent budget/receipt/duplicate processing, retries and cancellation preserve allocation invariants.
- AC12: A business decision and its audit commitment cannot diverge; replay uses pinned inputs.
- AC13: Missing dependencies, unclear extraction and outages never masquerade as passed checks.
- AC14: No secrets or real personal documents in the repository/logs; private originals and permissioned evidence links.

### 23.3 Model and operational gates

- AC15: TypeLLM integration has a recorded compatibility test; extraction schema conformance is not represented as factual certainty.
- AC16: If ML is delivered, publish measured held-out results, dataset limitations, threshold policy and model card. Otherwise visibly use rules/anomaly-only mode.
- AC17: SHAP output space and additivity are tested; no claim that attribution proves misconduct.
- AC18: Local setup, migrations, seeded demo, backup/recovery, known limitations and stage-specific test commands are documented.
- AC19: Performance results include the tested environment and meet the agreed release targets or clearly record the remaining bottleneck.
- AC20: A deployed pilot has tested authorization, backup restore, monitoring and rollback; a hackathon demo is labeled as such.

### 23.4 Suggested extraction quality gate

Measure critical-field exact match separately for amount, currency, invoice/receipt number, date and party reference; report sample size and uncertainty. A proposed initial goal is at least 95% exact match on clean synthetic critical fields and 100% correct abstention/routing on the curated ambiguous-critical-field fixtures. Neither number establishes real-document production quality. Do not enable automatic document-derived PASS for a document family until its quality policy is supported by representative validation; manual verification can satisfy the gate for the demo.

## 24. Codex working instructions and “do not” constraints

### 24.1 Required working loop

1. Read this specification and repository instructions; inspect existing code and status.
2. Select the earliest incomplete phase and one bounded vertical task.
3. Record the intended behavior, schema/API changes and relevant acceptance IDs in `docs/progress.md`.
4. Implement the smallest complete slice with fixtures and meaningful tests.
5. Run the relevant checks; inspect the UI where changed; validate evidence and financial invariants.
6. Record completed work, exact test results, assumptions, limitations and the next task. Do not claim tests ran when they did not.
7. Continue within the authorized implementation scope. Ask for missing external inputs only when the dependent step cannot be made safely concrete; continue independent local work.

The spec does not require parallel agents. Keep collaboration and implementation choices consistent with the user's current instructions and repository policies.

### 24.2 Do not

- Do not make an LLM the final authority for reimbursement, vendor identity, budget, approvals or payment instructions.
- Do not describe TypeLLM as classical OCR or assume unsupported nested output/provider features.
- Do not assume typed output means correct output, or self-reported confidence is calibrated.
- Do not use floats for money, mix currencies without a versioned FX rate, guess ambiguous dates, or infer absent tax as zero.
- Do not use invoice number, SHA-256 or an aggressive fingerprint as the universal record primary key.
- Do not discard repeated submissions, silently merge records, or call a pHash/fuzzy match a confirmed duplicate without corroboration.
- Do not treat high anomaly score as proof of fraud, or fabricate SHAP explanations or model performance.
- Do not allow low ML risk to override required finance controls.
- Do not auto-update vendors, payment accounts, employee records or policy from extracted text.
- Do not read live changing reference data halfway through a supposedly pinned evaluation.
- Do not consume budgets or receipt capacity through nontransactional “check then write” logic.
- Do not double-count PO commitments, current reservations, prior invoices or shared receipt allocations.
- Do not allow submitter self-approval, stale approvals, unscoped delegation or undocumented waivers.
- Do not change historical evaluations, source files, reference versions or audit events in place.
- Do not log secrets, expose other tenants, make receipts public, execute spreadsheet formulas or follow document-embedded instructions.
- Do not let an outage produce PASS, skip required checks silently, or label processing errors as business rejections.
- Do not hard-code demo outcomes into the UI or require paid inference for the rules-first local demo.
- Do not claim production readiness, legal compliance, validated ML accuracy or guaranteed latency without evidence.
- Do not execute payments, message vendors/employees, buy cloud resources or deploy to an unspecified account as an implied consequence of reading this document.

### 24.3 Open assumptions and external decisions

| Decision | Safe development default | Needed before live pilot |
|---|---|---|
| Company/entity scope | Synthetic single entity; tenant columns and isolation already implemented | Actual entities, visibility and policy owners |
| Currency/tax | INR primary, labeled synthetic tax; explicit FX fixtures | Approved jurisdiction/tax/rounding/FX policies |
| Approval and limits | Versioned demo policies above | Signed-off authority bands, waivers and SoD |
| Vendor/employee/PO data | Validated synthetic CSV imports | Authorized ERP/master source and freshness SLA |
| Extraction provider | Fixture adapter; tested TypeLLM spike | Compatible model/runtime, data terms, capacity and license |
| ML training | Rules/statistical baseline | Representative adjudicated history and governance |
| Retention | Configurable development retention; no real data | Organization-approved retention/legal hold/deletion policy |
| Azure deployment | Local containers and IaC draft | Subscription, region, access, budget and deployment authorization |
| Auto-pass operations | Screening eligibility only | Operational policy and future ERP release contract |

## 25. Demo walkthrough and final delivery checklist

Demonstrate six scenarios using synthetic data:

1. Clean vendor invoice with complete PO/GRN, budget and approvals → PASS with a traceable report.
2. Repeated already-paid invoice → HOLD citing the earlier internal invoice ID and matching facts.
3. Partial goods receipt/prior consumption → HOLD with precise remaining quantity and PO/GRN/allocation evidence.
4. Clean employee claim → PASS; then an over-limit hotel claim → REVIEW or HOLD according to the configured additional controls.
5. Recompressed receipt candidate → REVIEW with pHash/text evidence and a legitimate-shared-receipt counterexample.
6. Reviewer adds valid missing evidence → new evaluation, approval/capacity recheck and an intact original audit timeline.

Optionally demonstrate unusual amount → model-driven REVIEW with separately labeled SHAP, but only if the model is actually integrated and evaluated. Otherwise show the honest baseline mode.

Before handoff, deliver working local setup, repository/lockfiles/migrations, synthetic fixtures, API documentation, rules/policy catalog, measured test report, data dictionary, model card if applicable, runbooks and an explicit list of deferred items. A slides-only architecture or screenshot-only dashboard does not satisfy this implementation specification.

## 26. Sources and verification notes

The business requirements originate from the referenced conversation and current user request. Architectural details, thresholds, schema, API contracts, policies and task breakdowns are proposed implementation choices. Technical sources were checked on 2026-09-28; recheck and pin exact versions during implementation.

- [Original ChatGPT conversation: Explain Problem Statement](chatgpt-conversation://6ab9473a-248c-83e8-9e80-b14a00c8295e) — project context, two branches, finance checks and evidence-first approach; retrieval limit noted in section 0.
- [TypeLLM official repository](https://github.com/TypeLLM/TypeLLM) — structured-generation role and current documented interfaces; integration assumptions must be verified.
- [SHAP TreeExplainer documentation](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html) — supported tree explanations, output-space distinctions and additivity.
- [PostgreSQL explicit locking documentation](https://www.postgresql.org/docs/current/explicit-locking.html) — database locking primitives used by the proposed allocation design.
- [ImageHash repository](https://github.com/JohannesBuchner/imagehash) — perceptual hashing implementation reference; project thresholds require independent benchmarking.

**First implementation instruction:** begin with Phase 0, then build the Phase 1 rules-first vertical slice for both vendor invoices and employee expenses. Make financial controls, evidence, auditability and safe handling of uncertainty work before adding model complexity.
