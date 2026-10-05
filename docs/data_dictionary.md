# Domain glossary and implemented foundational contracts

## Final local release additions — 2026-10-04

No business table or migration is added. Existing immutable finance/document
records remain authoritative. New private metadata and scoped projections are:

| Object | Meaning and controls |
|---|---|
| `runtime/demo/state.json` | Atomic mode-0600 supervisor/app PID and `/proc` start-tick identity. UID/script/start-tick checks prevent signaling unrelated or reused PIDs. Not a business decision. |
| `runtime/demo/scenarios.json` | Private versioned fictional scope, idempotent checkpoints and retained evaluation/source IDs. Not authoritative for decisions: the API reloads scoped persisted evaluations. |
| `runtime/demo/templates/{vendor,employee}.json` | Private scope envelopes around synthetic form defaults. Returned only for matching authenticated tenant/entity in development. |
| `runtime/demo/reference/` | Ignored remapped fictional references with independent scenario capacity and explicit activation history. Original Git fixtures are unchanged. |
| `development/scenarios` | Development-only permissioned links, retained decision/version and current version. Historical PASS is explicitly superseded when facts change. Other scopes receive no rows. |
| `operations/measurements` | Seven-day projection of up to 500 extraction runs and 2,000 stage audit events: actual count/median/maximum milliseconds, provider header/row/inventory durations, queue state/age and selected incomplete controls. Empty samples are null; stage timings include commit overhead. |
| `audit_write_failed` | Fixed content-free log event when required audit persistence raises. Business effects roll back; retained failure count remains null because a failed event cannot be counted as committed audit. |

The actual partial-delivery source has independent approved PO 100 / accepted
GRN 50 / billed 70; exact Decimal evidence shows a 20-unit shortfall. The visual
case retains raw strings, normalizer-v2 traces, source confirmation, independent
approvals and versions 1 PASS / 2 HOLD / 3 PASS. Historical scores/evaluations bind
to their original versions. Originals, credentials, model shards, reports and
backups remain ignored; no predictive identifiers or hidden reasoning are added.

## Current real-extraction sidecar — 2026-10-04

This integration adds no database table or migration and retains `extraction-v1`.
The existing scoped immutable extraction run, observation, draft, source binding,
correction and evaluation records remain authoritative for their own versions.

| Item | Meaning / invariants |
|---|---|
| ProviderSettings.transport | `SDK` remains default; `TYPELLM_GATEWAY` uses the authenticated configured CPU HTTP endpoint. Token is read from a named environment variable, never persisted in run metadata. |
| ProviderSettings.model_revision | Optional exact 40-character revision pin; gateway responses must agree. |
| Additional visual header observations | `vendor_address`, `customer_bill_to`, `bill_to_address`, `ship_to_address`; raw strings with the same explicit five states and source page. They do not update masters. |
| Visual row amount | Printed `amount` observation supplements existing net/tax/gross fields. No float or inferred zero. |
| document-normalizer-v2 | Adds printed visual row `amount` to the existing Decimal/currency normalization rules. Earlier field semantics and stored v1 traces remain intact; ambiguous currency leaves this candidate unresolved. |
| extraction-routing-v2 | Private run sidecar: actual routing paths, cheap mapping gaps, provider state, prompt hash, call count, measured header/row/inventory seconds and table coverage. Not a finance decision or quality percentage. |
| row_regions / ruled-table-crops-v1 | Measured parent-preview dimensions, derived composite dimensions, header/row extents and offsets, rotation/scale, SHA-256, separate storage key and parent page transform. `field_bbox=null`; a crop extent is not a field box. |
| row_count_disagreement / provider-candidates-v1 | Both source-bound native/OCR and visual extraction outputs, retained privately when row counts differ. The larger candidate set stays visible with every field AMBIGUOUS; no asserted complete table or automatic finance acceptance. |
| Runtime versions | Safe actual TypeLLM, SGLang, torch, tokenizer-library/client Python, CUDA runtime, model source/revision, precision, bridge/cache-isolation and prompt hash. No secret, provider prompt dump or hidden reasoning. |
| Cache isolation | Gateway serializes requests and flushes backend prefix caches per generation; a failed flush makes the dependency unavailable until owned-service restart. |
| Provider uncertainty reconciliation | An empty native MISSING cannot replace source-bound visual AMBIGUOUS/ILLEGIBLE/NOT_APPLICABLE observations. Exact-format money differences may compare only through Decimal with agreed explicit currency; real disagreement remains AMBIGUOUS. |

All page numbers remain one-based. Native/OCR trustworthy coordinates retain
their existing mapping; VLM fields without trustworthy localization use null
boxes. Canonical money remains Decimal encoded as decimal strings. Raw independent
observations remain evidence, not approved canonical facts. See [ADR-0015](adr/0015-current-driver-compatible-real-vlm.md).

Terminology comes from the [specification](AP_Exception_Assistant_Codex_Spec.md). P0-02 implements the foundational value contracts described below; the broader glossary also describes future release concepts. The Phase-1 persisted schema is documented below.

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

Financial screening, processing, and human review states stay separate. Phase 1 implements the bounded transaction/evaluation/rule-result schema and controls below; wider accounting and human workflows remain future work.

## Implemented states

Implementation: [states.py](../apps/api/app/domain/states.py).

| Contract | Exact values |
|---|---|
| ProcessingState | RECEIVED, QUARANTINED, QUEUED, PROCESSING, NEEDS_INPUT, FAILED_RETRYABLE, FAILED_FINAL, COMPLETED |
| ScreeningDecision | PASS, REVIEW, HOLD |
| ReviewApprovalState | NOT_REQUIRED, OPEN, ASSIGNED, AWAITING_INFORMATION, APPROVED, DECLINED, RESOLVED, CANCELLED |
| RuleStatus | PASS, FAIL, UNKNOWN, NOT_APPLICABLE, ERROR |
| DecisionEffect | NONE, REVIEW, HOLD |

These are separate Enum types, not interchangeable string aliases. Use `.value` for their documented wire vocabulary and explicit member comparisons such as `status is RuleStatus.PASS`. Boolean coercion raises TypeError for every state, so `if status` cannot mistake UNKNOWN, FAIL, or NOT_APPLICABLE for success. The value-contract module contains no transitions; Phase-1 services and the pure rules engine implement processing/decision behavior separately.

### UNKNOWN and absent values

`RuleStatus.UNKNOWN != False`, `0`, `None`, FAIL, PASS, NOT_APPLICABLE, and ERROR. None represents an absent optional value; UNKNOWN is an explicit unresolved-check status. Neither defaults to a clean result. Money rejects None and booleans; monetary zero must be supplied explicitly. Evidence observations may be absent (`None`) or explicit text (`"0"`, `"false"`, or a redacted representation); they do not become numeric/boolean facts or replace a rule status. The Phase-1 combiner makes required UNKNOWN/ERROR ineligible.

## Money and currency

Implementation: [money.py](../apps/api/app/domain/money.py).

- `Money(amount, currency)` is frozen. It accepts finite Decimal values, ungrouped plain ASCII decimal strings, and integers; it rejects floats, booleans, None, non-finite decimals, grouped/localized text, and scientific-notation strings. An existing Decimal may have an exponent; no constructor rescales or rounds it.
- An externally constructed Decimal is accepted as an exact value. This type cannot establish how that Decimal was produced; callers must not first create it from a float.
- Currency must be exactly three ASCII letters and is normalized to uppercase. Whitespace/symbols/digits are rejected. This validates structure only, not official registration or policy support.
- Equality compares amount and currency; differing scale with the same exact value compares equal. Addition/subtraction require another Money in the same currency, otherwise fail explicitly. There is no FX, scalar coercion, tax calculation, division, or rounding policy.
- Arithmetic uses a private Decimal context with operand-derived sufficient precision and rounding/inexact/overflow traps. It does not read or mutate the caller's precision, rounding, or flags. Supported operations never silently lose digits; implementation-limit errors remain errors.
- `to_dict()` emits `amount` as plain decimal text and `currency` as normalized text. Fractional zeros are preserved without rounding, including tiny values beyond ordinary currency minor units. Phase-1 API schemas and reports reuse decimal-string serialization.
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
| ImportCellLocator | Frozen batch UUID, nonblank sheet, positive one-based row, and nonblank original column identifier. IMPORT_CELL evidence requires this complete locator; the Phase-1 CSV/XLSX importer supplies actual retained row/cell bindings. |

These references validate structure and keep facts immutable; they do not prove record existence, authorize access, verify tenant relationships against a database, or verify that coordinates map to real content. Phase-1 API lookup resolves scoped records; actual document transform validation remains later work.

### Missing evidence without invented records

A missing-approval finding can carry a TRANSACTION reference to the actual current transaction/version, a POLICY_CLAUSE reference to the actual requirement/version, and the search snapshot on the transaction reference. Its observed text can state that approval was absent. It does not create an APPROVAL reference or guess an approval UUID. The value contract itself implements no approval rule; Phase-1 APR-001/APR-002 persist the missing/insufficient-chain finding and its real context.

## P0-03 fixture terminology

These are implemented JSON fixture conventions described in the [reference README](../data/synthetic/README.md) and [golden README](../data/golden_cases/README.md), not implemented database/API schemas. All records are synthetic and versioned; references use scoped UUIDs. Monetary and quantity fields are decimal strings. Effective intervals are half-open local dates.

| Fixture term | Represented fields and meaning |
|---|---|
| Vendor master | Legal name, aliases, DEMO-NONREG tax identifier, ACTIVE_APPROVED status, approved categories, validity period, DEMO-NONPAYABLE token and account-version tag. No real banking or tax registration. |
| Employee master | Separate employee number/name, employment dates/status, department, cost-center UUID, nullable manager UUID, grade, country and declared demo roles. Manager links are acyclic. |
| Cost center | Scoped UUID, demo code and department, shared consistently by employees, budgets and approval policy. |
| Purchase order | Display number, vendor, INR, APPROVED_OPEN status, gross approved ceiling, category, budget and approval-policy links; contains independently identified PO lines. |
| PO line | Parent PO/vendor/budget, description, ordered quantity, EA unit, unit price, EXCLUSIVE tax basis, synthetic tax rate, explicit zero absolute/relative/quantity tolerances with MAX operator. |
| Goods receipt / GRN line | Parent PO/PO-line and receipt UUIDs, display GRN, local received date/source/version; received/accepted/returned/reversed quantities. Net accepted is accepted minus returned minus reversed. |
| Expense policy | UUID, policy code/version/period, DEMO label, category, grade/country/location dimensions, INR allowance and unit, itemized-receipt requirement, timezone and submission-window days. |
| Approval policy / action | Policy carries scoped INR bands, ordered role chains and separation-of-duties configuration. Case actions carry UUID, actor/role/sequence, state and UTC time bound to transaction/policy/version; these are declared synthetic data, not authorization. |
| Budget / ledger row | Entity/fiscal period/department/cost center/project/category/currency, covered categories and GROSS basis. UUID ledger rows represent ALLOCATION, CONSUMPTION, PO_COMMITMENT or CLAIM_RESERVATION with amount and owner where needed. No mutable balance or reservation service exists. |
| Historical transaction / allocation | Versioned canonical obligation facts, source link, lifecycle and settlement status. Vendor allocation states CONSUMED, RELEASED and REVERSED differ; employee paid consumption and ACTIVE/PENDING reservation differ. Cancelled/reversed rows remain evidence, not active capacity. |
| Synthetic source document | JSON-only invoice/receipt facts labeled SYNTHETIC_JSON_FACTS_ONLY and ADJUDICATED_SYNTHETIC_FACTS. UUIDs resolve within fixtures; no document bytes, actual receipt verification, extraction, page or box coordinates exist. |
| Golden case | UUID plus display case_id, branch, synthetic transaction, pinned reference IDs/versions, expected facts/decision/concepts/evidence, rationale and intended T IDs. Screening labels are future expectations, never executed results. |
| Golden receipt allocation | Authorized demo peer share and separate PROPOSED claimant share; cases are independent alternatives. A proposal exceeding eligible value is exception data, not a committed over-allocation. |
| Fixture snapshot / digest | Case snapshot pins dependency roots and explicit selected children with matching versions; evidence paths resolve. Canonical repeated loads and the 23-file SHA-256 manifest verify deterministic data integrity, not evaluation replay or audit security. |

No FX, contracts/service acceptances, importer, full training/performance dataset, or financial evaluator is represented. Missing hotel nights and per-night amounts stay null; category status expectation UNKNOWN stays distinct from them and from PASS.

## P0-04A extraction terminology

Implementation: [extraction contract](../apps/api/app/domain/extraction.py), [adapter Protocol](../apps/api/app/extraction/base.py), [fixture adapter](../apps/api/app/extraction/fixture.py) and [comparison harness](../apps/api/app/extraction/spike.py). These are in-memory immutable contracts and structured replay, not a document ingestion, OCR, normalization, finance evaluator or persistence service.

| Term | Implemented meaning |
|---|---|
| DocumentBundle / DocumentPage | Scoped UUID document/version, source type, ordered one-based pages, optional available text/future artifact references, declared rotation metadata and named version tags. No PDF/image access or preprocessing. |
| ExtractionAdapter | Replaceable Protocol exposing typed metadata/capabilities and `extract(document_bundle, schema_version) -> ExtractionResult`; no provider/framework dependency. |
| ExtractionResult | Frozen run/document/version/scope/schema identity, AdapterMetadata, ExtractionStatus, header observations, flat repeated rows, optional Decimal adapter elapsed time and raw artifact reference. No private reasoning or finance outcome. |
| ExtractionRun | A result's required run UUID and version metadata identify one extraction observation run. Fixture IDs repeat deterministically. No database/run history, audit service, retry lifecycle or production run-ID generation exists. |
| AdapterMetadata / VersionMetadata | Required adapter ID/version/provider ID plus optional model ID, prompt/template version and unique runtime name/version pairs. Unknown metadata stays absent. |
| AdapterCapabilities | Explicit page-locator, bounding-box, line-item and visual-input support flags. Undeclared result locators/rows are errors; a flag is not independent runtime compatibility evidence. |
| FieldObservation | Named scalar path, raw text, optional unverified candidate text, state, optional document EvidenceReference and uncalibrated diagnostic note. Page/bbox derive from existing evidence; no invented coordinates or required confidence. |
| ExtractionObservationState | PRESENT requires raw text; MISSING requires null raw/candidate; ILLEGIBLE represents unreadable content; AMBIGUOUS preserves uncertain raw text; NOT_APPLICABLE is an extraction-schema annotation. Every non-PRESENT state forbids chosen candidates. None never silently becomes zero or a clean result. Boolean coercion is rejected. |
| ExtractionStatus | COMPLETED, PARTIAL, FAILED, UNSUPPORTED. Execution status stays distinct from RuleStatus, screening and review states; COMPLETED may contain unreadable fields. Boolean coercion is rejected. |
| LineItemObservation | Ordered positive row index, unique named scalar fields; at most 200 rows, 16 fields per row, 64 header fields. No recursive nested tables or general alignment. |
| FixtureExtractionAdapter | Deterministic replay of independent synthetic response files by canonical input SHA-256 and schema; validates binding and does not consult golden finance outcomes. |
| SpikeCase / SpikeDataset | Ten structured-only synthetic inputs, expected field/row facts/states and separate replay paths; version `extraction-spike-v1`, schema `extraction-v1`, canonical manifest digest and separate 11-file byte checksums. |
| Spike report | Per-case statuses/comparisons plus independent critical-field, state/abstention, row count/coverage/value, locator availability, optional latency and version metadata. Empty/unavailable metrics are null. Generated runtime reports are separate from source annotations. |

Parsed candidates remain text, including amount strings; they are neither authoritative Money nor verified normalization. Page references are synthetic declarations in this set and do not prove extraction localization. See the [extraction README](../data/extraction_spike/README.md) for limits and metric denominators. Provider topics are now [source-verified or explicitly unresolved/blocked](extraction_compatibility.md); parent P0-04 is incomplete. P0-04B introduces no new runtime contract.

## P0-04B planned provider boundary

These are documented decisions/proposals, not implemented provider behavior. [ADR-0002](adr/0002-extraction-money-and-provider-boundary.md) fixes printed financial values as strings; later trusted locale/currency normalization may construct Decimal from validated text. TypeLLM number/float output cannot enter authoritative money or be stringified as recovered exact source. Initial provider candidates remain None until trusted normalization is approved; raw/state and combined candidate metrics stay distinct.

Explicit state enums and conditional raw-text questions map to the existing five extraction states; skipped keys are not implicit absence. Per-page requests can bind known source pages, with bbox/coordinate_system None. Flat bounded row assembly avoids unsupported nested provider schemas. Private reasoning and raw exception bodies are excluded. The [plan](typellm_spike_plan.md) specifies mappings, failure states, pins and gates; no real adapter, visual dataset, OCR, normalization or finance routing exists.

## Phase 0 contract version catalog

This is a release/provenance catalog, not a new API version field. The unchanged P0-02 values are Git-versioned at their foundational revision; extraction and synthetic fixtures also carry explicit schema/version identifiers. Later breaking changes require intentional versioning/migrations. Provider pins do not version the finance contracts.

| Contract/data | Version / immutable reference | Scope |
|---|---|---|
| State, Money/currency and evidence foundation | P0-02 Git revision `c7e82a688ee5daccbb354afa03d18f8e4ed5c8af` | [states.py](../apps/api/app/domain/states.py), [money.py](../apps/api/app/domain/money.py), [evidence.py](../apps/api/app/domain/evidence.py); unchanged through Phase-0 closure. No business evaluator/persistence schema. |
| Extraction boundary | `extraction-v1`; P0-04A Git revision `4bf48d764242dd01a7ab5cc59b9ec8682558a8b8` | [extraction.py](../apps/api/app/domain/extraction.py) and [ExtractionAdapter](../apps/api/app/extraction/base.py); frozen scoped inputs, raw/candidate states, bounded rows and explicit result/capabilities metadata. |
| Finance fixture schema | `p0-03-v1` | Golden manifest and 23 finance JSON byte checksums; normalized digest `1fdd167453d530ad286dbb633ed1e0abb5051f61b38b08bfd3b13a6ba52550b6`. Expected outputs are data. |
| Extraction fixture dataset | `extraction-spike-v1` | Ten structured cases, 11 JSON byte checksums; canonical manifest digest `db00315130436eb572065cad35b1b00edcb2c8058dad84ea862de5975387bd0a`. No visual artifacts. |
| Fixture adapter / provider | `fixture-v1` / `synthetic-response-replay` | Explicit synthetic development replay, not runtime fallback for real documents. |
| Spike report | `extraction-spike-report-v1` | Versioned independent comparison results; optional model/runtime/latency/bbox remain unavailable where unobserved. CLI timestamp is generated report data only. |

## Accepted architecture vocabulary — future implementation

The following concepts are design metadata, not new enum values, implemented records or extra extraction-v1 JSON fields. See [inference architecture](inference_architecture.md) and [Phase-0 exit review](phase0_exit_review.md).

| Concept | Responsibility and safety boundary |
|---|---|
| Control plane | CPU-friendly central API/database/rules/approvals/budgets/review/audit/reports and durable jobs/outbox metadata. A laptop runs only the supported client/browser. |
| Inference plane | Separately hosted shared TypeLLM/VLM/SGLang, preprocessing/router, resident model serving/caches and extraction workers. No finance decision authority. |
| FIXTURE | Verified current synthetic development provider mode; no GPU or paid provider. No deployment configuration enum/service yet. |
| ENTERPRISE_VLM | Future shared GPU provider mode behind the same ExtractionAdapter; no production model approved. |
| TEXT_FAST_PATH | Future extraction route for reliable native text and structured extraction, not a finance-risk mode. |
| ExtractionRouter | Chooses text/visual/tier/page/crop paths based on versioned quality/evidence sufficiency, family/layout and resource availability. Cannot decide PASS/REVIEW/HOLD. |
| Model tier | Small visual tier followed by stronger fallback only for supported unresolved facts; disagreement remains explicit. Human review is later workflow. |
| Route/attempt sidecar | Future explicitly versioned run/document/version/scope, original/artifact digest, route/tier, attempts/fallback reason, quality-policy versions and real measurements. Keep strict extraction-v1 unchanged until approved version work. |
| Region/transform sidecar | Future actual crop kind/extent, original page/dimensions, orientation/transform, derived artifact/version/hash and nullable verified field bbox. A selected crop is not a field box; no coordinates invented. |
| Durable extraction job | Future at-least-once leased job/outbox with scoped versioned stage key, timeout/retries/cancellation/failure/provider-unavailable states and guarded idempotent finalization. No persistence/job implementation exists. |
| RULES_ONLY | Initial finance-risk design: no configured ML risk model/score; not a zero-risk result. Independent of extraction VLM. Visibility/reporting and finance rules require Phase-1 implementation. |
| RESEARCH PIN | Source-verified proposed component/checkpoint/container revisions, not a tested production tuple. PRODUCTION APPROVED PIN is NONE until suitable-host quality/safety/operations gates pass. |

Money, uncertainty and evidence semantics above remain stable. Real provider mappings, crop detection, quality thresholds, normalization, router, storage and durable execution remain future work, with real measurements deferred rather than given numeric defaults.

## Implemented Phase-1 persistence

Every business record carries tenant_id/legal_entity_id. UUID keys, scoped foreign keys, forced RLS and transaction-local server identity apply. Monetary columns are Numeric(20,6); quantity columns Numeric(24,8). Financial JSON uses decimal strings. DateTime values are timezone-aware; business dates are ISO dates. The schema has 22 domain tables plus Alembic metadata.

| Tables | Stored behavior and mutability |
|---|---|
| tenants, legal_entities | Trusted scope, names, currency/timezone. Tenant holds an atomic audit sequence/hash projection. |
| reference_records, reference_links | Immutable kind/version/payload catalog; flattened PO/GRN/ledger/allocation children with scoped edges. Indexed exact history attributes. Original synthetic source remains unchanged. |
| reference_snapshots, snapshot_members | Immutable manifest and concrete record/version membership, including relevant selected history at finalization. |
| transactions | Mutable latest version/evaluation, processing state, decision and current eligibility projection; never the historical facts. |
| transaction_versions | Immutable validated canonical payload, amount/date/party search attributes, digest, author/reason and normalizer/schema versions. |
| approval_records | Immutable trusted action bound to transaction/policy version, actor, role, sequence, state and timestamp. No client authority fields. |
| evaluations, evaluation_inputs | Immutable rule/decision-policy versions, reference snapshot, mode/completeness/outcome, input digest/time/supersession and complete canonical rule context. |
| rule_results, evidence_objects | Immutable typed status/effect, operands, expected values/tolerance/reason, and actual scoped source/version references; no synthetic bounding boxes. |
| reports | Immutable deterministic JSON/HTML, digest and report schema version. Snapshot eligibility is distinct from current projection eligibility. |
| review_cases | OPEN REVIEW/HOLD queue with reason-rule IDs. Corrections or a newer evaluation supersede older queue projections. Human resolution is later work. |
| audit_events | Append-only actor/object/version/time/reason/correlation/payload, sequence and hash linkage; atomic with business writes. No external tamper-proof claim. |
| jobs, outbox_events | Durable stage/version/key, current-request generation, QUEUED/RUNNING/RETRYABLE/SUCCEEDED/FAILED/CANCELLED/STALE state, attempts, deadlines and lease owner; local delivery metadata. |
| idempotency_records | Scoped actor/endpoint/key/request hash with stable original response/status. Changed input conflicts. |
| import_batches, import_rows | Private original object key/digest; sheet/row/raw JSON/error/canonical/link metadata. Raw source is immutable; commit links valid rows and retains invalid rows. |
| capacity_reservations | Minimal budget/PO-line/GRN-line admission amounts/quantities. A new version or request releases current effects; guarded finalization creates fresh ones only on eligible PASS. |

Transaction processing uses P0 RECEIVED/QUEUED/PROCESSING/FAILED_RETRYABLE/FAILED_FINAL/COMPLETED. Job execution has its separate vocabulary above. Rule and screening state values remain the unchanged P0 contracts. No rules infer document boxes, FX, zero tax or approval authority. Catalog/input ceilings and version checks are part of the bounded Phase-1 contract; see ADR-0009 and the runbook.

## Phase-2 document records and raw observations

| Record | Meaning |
|---|---|
| documents / upload_sessions | Mutable scoped processing projection and expiring actor-bound upload. Internal keys are server generated. No finance decision on a document. |
| document_versions | Immutable original SHA-256, actual bytes/MIME, upload ID, object key/version, actor/correlation/UTC time. |
| document_pages | Immutable one-based page, PNG preview SHA/key, native text/spans, actual original/display dimensions and transform, explicit quality measurements/routing reason. |
| document_jobs / document_outbox | Additive document-specific durable stage/version/generation/key/attempt/lease/result metadata and delivery marker. Existing finance job schema remains strict. |
| extraction_runs / field_observations | Immutable attempt/provider/schema/template/runtime metadata and explicit PRESENT/MISSING/ILLEGIBLE/AMBIGUOUS/NOT_APPLICABLE raw strings with actual scoped page/box sources. No finance or hidden reasoning fields. |
| document_drafts | Immutable NORMALIZE/VALIDATE candidates, per-field source observation/rule/steps/status trace and unresolved/arithmetic/source findings. Money is decimal string; dates are business dates. |
| transaction_documents | Immutable canonical-version-to-document-version links, INVOICE/RECEIPT/PO/SUPPORT role, actual one-based page range, optional verified-fact/draft pins. Multiple documents can link to one transaction. |
| source_corrections | Immutable actor/reason/current canonical version, old/new raw/canonical values, real observation/correction IDs and page reference. Corrected field boxes remain null; extracted history is unchanged. |
| import_cells | Immutable batch/sheet/row/column/field/raw/parsed/validation evidence, including invalid formula/numeric cells. Rule evidence resolves to the actual originating cell. |

Quality fields name their measurements: Laplacian variance, mean luminance 0–255, dark/light pixel fractions, native character count/density and preview dimensions. Coordinate/quality floats are not financial values. The routing-v1 sidecar is separate from strict extraction-v1. PDF coordinates use actual display rotation; image OCR boxes map through inverse EXIF orientation into normalized original-page coordinates. Unknown boxes are null. Crop/deskew are not fabricated.

### Source and normalization semantics

EXTRACTED observations, NORMALIZED candidates, CANONICAL submitted versions,
HUMAN_CORRECTED traces/actor/reason and MASTER/REFERENCE facts have different
authority. HUMAN_VERIFIED_DOCUMENT records pin actual document/draft/canonical
revisions and pages; factual verification does not create a finance approval.
Source corrections retain real observation IDs and their own immutable correction
record. New evaluations supersede current eligibility while old reports remain.

Number keys retain conservative text and aggressive candidates without I/O
substitution or removing leading zeros. Currency requires a supported explicit
code. Raw money becomes exact Decimal-derived strings; missing tax remains
unknown. Dimensionless quantity/rate/night values reject currency units or guessed
percentage scaling. Ambiguous dates require explicit DMY/MDY or correction; local
business dates remain distinct from UTC events. Normalizer currency support does
not extend the established bounded INR finance policy.

| Version | Responsibility |
|---|---|
| document-pipeline-v1 | Stable scope/document/revision/generation/stage idempotency and lease guards. |
| document-processor-v1 | Bounded parsing, immutable pages/transforms and defined quality measurements. |
| extraction-v1 | Preserved strict provider-independent observation/result contract. |
| extraction-routing-v1 | Separate native/OCR/enterprise paths/status/attempts/segmentation/fallback metadata. |
| typellm-document-v1 + prompt hash | Observable string/state questions, no finance authority/private reasoning. |
| document-normalizer-v1 | Observation-linked normalization/validation and canonical provenance. |
| document-source-v1 | Physical DOC-001 reconciliation; core rules-p1-v7 remains unchanged. |
| report-p2-v1 | Document-derived metadata/links; structured report-p1-v2 remains supported. |

## Phase-3 reference and finance facts

Migration `0005_finance` adds 13 tables to the 34 existing business tables; all 47
enforce forced scoped RLS. Immutable facts reject ORM and direct SQL mutation.
ReferenceBatch is a workflow projection whose source records/system/version/actor
remain protected. Existing reference_records/snapshots/members/links retain exact
versions; contracts, service acceptance, delegation and policy facts reuse them.

| Table | Authority and fields |
|---|---|
| reference_batches | Source system/version, raw records, actor, timestamp, STAGED/VALID/INVALID/ACTIVE/SUPERSEDED projection and exact validation findings. |
| reference_activations | Immutable batch-to-reference UUID/version activation and actor. |
| finance_allocations | Evaluation/transaction/version/resource, BUDGET/PO_LINE/GRN_LINE/CONTRACT/SERVICE/RECEIPT kind, exact amount/quantity/currency and metadata. |
| allocation_events | Append-only RESERVED/CONSUMED/RELEASED/REVERSED lifecycle facts and stable operation key. |
| budget_events | Allocation/adjustment/commitment/reservation/consumption/release/reversal exposure with source/owner/operation binding and decimal amounts. |
| duplicate_comparisons | Both transaction/reference versions, candidate classification, separate signals, normalizer/provider metadata and safe source/candidate facts. |
| duplicate_resolutions | DISTINCT/CONFIRMED_DUPLICATE/SHARED_RECEIPT_ALLOCATION, both version bindings, authenticated actor, reason and real evidence. |
| image_fingerprints | Actual document/page version, algorithm/library/preprocessing, 64-bit hash, dimensions and no invented crop. |
| fingerprint_bands | Indexed seven disjoint bands for bounded <=6-bit candidate retrieval. |
| receipt_shares | Actual receipt UUID, current claim/item/version/employee, authorized exact amount/quantity, actor, reason and evidence. |
| approval_requests | Transaction/policy versions, computed ordered requirements, requirements digest and immutable creation fact. |
| approval_actions | Request/step, APPROVED/DECLINED/REJECTED, actor, master/delegation versions, rejection reason/evidence and UTC time. |
| waivers | Exact rule/version, transaction/version, configured actor/role/policy, reason/evidence, expiry; original result retained. |

All new tables use tenant/entity foreign-key scopes and UUID identities. Receipt
and resource pointers spanning physical and adjudicated synthetic references are
validated through scoped services; they are not represented as a fictitious single
foreign-key target. No raw bank account is imported; equality tokens are redacted
from reports and comparison facts. Page evidence uses the existing physical source
contract; absent boxes remain null.

Activated reference payloads add source_system/source_record_id/source_version,
import_batch_id/imported_at/validation_result and effective half-open dates where
applicable. A nested budget ledger receives its own immutable reference child and
server-owned version equal to the parent import version. Approval policies use
explicit bands, authority matrices, scopes and optional computed exception roles.
Preapprovals require explicit approved_date, period, claimant/approver/category,
scope/currency/ceiling and PREAPPROVER authority. Approved UOM factors and tolerance
MAX/MIN/AND/OR operators are trusted configuration, never extracted assumptions.

Reference selection returns EXACT, CURATED_ALIAS or unresolved FUZZY_CANDIDATES;
multiple exact/alias/policy candidates remain AMBIGUOUS. Similarity is not a
probability. EXACT_BYTES and POSSIBLE_DUPLICATE remain candidates; corroborated
active STRONG_BUSINESS_MATCH or explicit authorized confirmation can HOLD.
Shared receipts still undergo independent cumulative capacity controls.

`rules-p3-v1` / rule version `3.0.0` extends the preserved engine to 28 controls.
Eight additions are REF-001, DUP-001, DUP-003, EXP-002, EXP-004, EXP-005, EXP-006
and PAT-001. Existing control IDs keep their meaning while their configured scope
expands. Reports retain original results plus finance_controls and waiver_dispositions.
Risk remains RULES_ONLY / NOT_CONFIGURED with no score or model probability.

## Phase-4 workflow and operational facts

The additive head is `0006_workflow`: 49 business tables plus Alembic. The original
47 tables and all retained facts remain. New tables have forced scoped RLS and
ORM/direct-SQL immutability. No authoritative money column or numeric precision
changes. See [ADR-0012](adr/0012-versioned-review-and-operational-recovery.md).

| Record/field | Meaning |
|---|---|
| review_cases.owner_id | Trusted reviewer actor, nullable for unassigned. It is not supplied authority. |
| review_cases.row_version / updated_at | Positive optimistic write version and timestamp; accepted ownership/action changes increment the version. |
| review_actions | Immutable case/review-version/transaction-version-bound action, actor, reason code/comment, evidence and redacted old/new facts or requested input. Unique scoped case/version. |
| operation_records | Immutable scoped operation-key digest, kind, object UUID, actor, timestamp and safe details; replay, reconciliation, retry and private report-export snapshots. |
| jobs / document_jobs.failure_retryable | Explicit safe failure classification; permanent failures do not become retryable just because the provider is absent. |
| first_failure_at / last_failure_at | Retained first/last failure timestamps; successful recovery does not erase attempt history. |
| manual_retries | At most two service-authorized extra execution cycles; total attempt counter never resets. |
| current_eligible | Derived eligibility over latest facts/evaluation, state, current references/policy, waiver expiry and required reservations. Separate from immutable evaluation.eligible. |
| evaluation_status | CURRENT, SUPERSEDED or STALE read projection; no mutation of retained screening decision. |
| current_eligibility_as_of | Explicit measurement timestamp for an authorized export snapshot. |
| next_actions | Deterministic control-to-action labels. They do not clear a control or assert approval. |

Stored OPEN means unassigned; ASSIGNED and AWAITING_INFORMATION retain owner.
RESOLVED closes the human exception after fresh eligibility. SUPERSEDED retains a
previous review/evaluation. CANCELLED preserves history and prevents admission.
Operational job display maps RUNNING/RETRYABLE/FAILED/SUCCEEDED to
PROCESSING/FAILED_RETRYABLE/DEAD_LETTER/COMPLETED without rewriting old facts.
CSV escaping changes only exported cells. Original document/field/import evidence
remains unmodified. New export artifact UUIDs resolve only through authorized routes.

## Phase-5 immutable intelligence sidecar

All twelve tables carry tenant/legal-entity scope and forced RLS. Scoped foreign
keys bind existing evaluations, versions, reviews and source evidence; database
triggers and ORM guards reject updates/deletes. Migrations `0007_intelligence` and
`0008_intelligence_audit` are additive. The existing review table accepts explicit
PASS audit cases; this does not permit setting a finance decision.

| Table | Retained fact |
|---|---|
| feature_schemas | Ordered names/types/definitions/null semantics/clips, schema version and digest. |
| risk_history_sources | Activated historical reference/version, sanitized facts, digest and server-observed knowledge time. |
| feature_snapshots | Evaluation/schema, cutoff, transaction/version/reference pin, values/types/missing reasons, lineage/source manifest and code digests. |
| feedback_labels | Evaluation/review/action, actor/time/reason/evidence, taxonomy, label, quality and superseded label. |
| risk_audit_samples | Stable campaign/rate selection of a retained PASS evaluation and existing review case. |
| risk_datasets | Frozen taxonomy/schema/source digest, included IDs/cutoffs, grouped chronological splits, exclusions and supervised-data gate. |
| risk_training_runs | Offline actor/dataset/schema/configuration/seed/code/dependencies; BASELINE_BUILT or SUPERVISED_DEFERRED. |
| risk_models | Statistical artifact version/algorithm/private key/SHA-256, dataset/schema/run and model card. |
| risk_model_events | Append-only CANDIDATE/EVALUATED/APPROVED/SHADOW/ACTIVE/RETIRED/REJECTED governance events. |
| risk_deployments | Scoped configuration version/mode/model/threshold/previous configuration, actor and reason. |
| risk_scores | Evaluation/feature/deployment/model pins; status, score kind/value, factors, separate review reason and digest. |
| risk_monitoring | Bounded actual measurements/baseline/drift diagnostics, actor, digest; no automatic model update. |

`features-p5-v1` contains log_amount, vendor_amount_ratio,
employee_category_ratio, robust_amount_z, po_value_ratio, price_variance_ratio,
receipt_shortfall, policy_limit_ratio, budget_utilization_after,
max_duplicate_similarity, min_phash_distance, same_amount_count_30d,
days_since_previous, vendor_tenure_days, payment_account_changed,
claims_near_limit_7d, submission_delay_days, quality_and_freshness, history_count
and cold_start. The public machine-readable definitions are in
[ml/contracts/features-p5-v1.json](../ml/contracts/features-p5-v1.json).

Feature monetary operands and statistical medians remain decimal strings with
currency; numerical feature outputs are diagnostic, never ledger amounts.
Missing values are null with explicit indicators/reasons, not zero. History excludes
the current transaction and future knowledge. Zero MAD produces no robust z-score;
fewer than five prior observations produces no cohort anomaly score. A backdated
synthetic input created after its cutoff supplies no predictive values.

`max_duplicate_similarity` is bounded printed-number similarity within the completed
prior same-party/currency/branch cohort, not a duplicate disposition. `min_phash_distance`
is actual prior 64-bit Hamming distance, never proof of duplication. Source quality
is the unresolved fraction of known critical observations (vendor/date/currency/total
or merchant/expense date/currency/total), not an invented quality percentage.
Unsupported policy aggregate units and unavailable onboarding/account/source data
remain missing.

`ANOMALY_SCORE` is a defined 0–100 statistical deviation; higher is more unusual.
It is not exception_probability. Explanation status is STATISTICAL or explicitly
unavailable; SHAP is NOT_APPLICABLE. RULES_ONLY retains NOT_CONFIGURED/null score;
SHADOW cannot route; RULES_PLUS_ANOMALY may escalate PASS to REVIEW; a required
RULES_PLUS_MODEL without a compatible model remains MODEL_UNAVAILABLE. An
intelligence configuration change produces STALE current eligibility separately
from immutable historical PASS/REVIEW/HOLD.

`adjudication-p5-v1` labels are CLEAN_CONFIRMED, DUPLICATE_CONFIRMED,
POLICY_EXCEPTION, DOCUMENT_CORRECTION_ONLY, DISTINCT_CONFIRMED and
INSUFFICIENT_INFORMATION. Only final clean/distinct and material duplicate/policy
adjudications form binary targets; correction-only/insufficient labels are excluded.
All current manifests remain SYNTHETIC_DEVELOPMENT and fail the representative
supervised gate. See [model card](../ml/model_card.md) and
[runbook](runbooks/phase5-local.md) for score and governance semantics.

## Phase-6 release boundaries

- **Business configuration draft:** existing ReferenceBatch with source_system BUSINESS_ADMIN, expected current reference version, typed allowlisted changes and actor/reason. Existing validator and activation append a ReferenceRecord version. No new table or executable rule store.
- **Policy administrator:** POLICY_ADMIN may stage/activate expense, approval, delegation and waiver policy kinds only. REFERENCE_ADMIN retains master/reference authority; LEDGER_ADMIN uses existing budget adjustment events. Current permissions are checked before idempotent cached responses.
- **Enterprise membership:** server-owned mapping from verified Entra object identity to application tenant/entity/actor/roles. Token-supplied roles and client scope are not authoritative. Worker scopes are separately server-configured.
- **Private cloud artifact:** existing UUID-scoped storage key and SHA-256, preserved with immutable Blob upload and verified private CPU materialization. Original keys remain distinct from page/report/model keys. Cache availability is not remote availability.
- **Operational health:** minimal public live/ready response versus permissioned dependency state. CONFIGURED_UNVERIFIED is not AVAILABLE; NOT_CONFIGURED malware is not CLEAN.
- **Request telemetry:** route template, method, status, duration_ms, correlation_id. No raw URL/query, token, body, financial/source content or exception text.
- **Release approval:** private operator inputs including subscription/resource group/region/spend/identity/network/residency/GPU disposition and recovery/auth/rollback checks; binds a full release commit and reviewed parameter SHA-256. The dispatcher verifies the active account and target before migrations/deployment. It is not a model, policy or payment approval.

## ClearLedger additive projections — 2026-10-04

No table or migration is added; extraction-v1 and financial record semantics remain.

| Field / sidecar | Meaning and controls |
|---|---|
| printed-layout-v1 | Measured PDF spans/OCR words associate explicit labels/headings; uncertain crossing/wrapped cells abstain. Not confidence or finance sufficiency. |
| OCR layout_bbox | Upright preview coordinate for association only; bbox remains the actual inverse-EXIF original coordinate used by evidence. Word/line kind prevents duplicate association. |
| PRINTED_FACTS_MAPPED_REVIEW_REQUIRED | Routing sufficiency when observed core facts exist but financial mapping gaps remain. It skips unnecessary model guessing, not validation/source confirmation. |
| header_fields_requested | Actual per-page model header field list; empty only when core printed headers are independently covered. Rows/inventory retain real contract calls when needed. |
| UPLOAD_SESSION_CREATED.payload.intake_hint | Immutable original AUTO or explicit user purpose; legacy events fall back to retained source_type. Not authorization. |
| PREPROCESS.classification | document-purpose-v1 SUGGESTED/NEEDS_CONFIRMATION, printed-label method, source_type and evidence_pages; manual source verification always true. |
| DOCUMENT_TYPE_UNCONFIRMED | Processing NEEDS_INPUT after safety preprocessing; no extraction/finance decision until scoped generation-bound purpose confirmation. |
| documents.generation | Existing retry/freshness generation; purpose confirmation increments it and schedules one idempotent EXTRACT stage. Old pages/original audit are retained. |
| documents/intake-capabilities | Authenticated bounded limits, malware_required and explicit scanner configuration/availability. No executable path, credentials or clean-file claim. |
| AP_MALWARE_SCANNER_EXECUTABLE | Operator-supplied absolute local engine; no downloads, shell, file deletion or invoice content logging. Configuration is not successful scanning. |
| NEXT_PUBLIC_PRODUCT_NAME | Public build-time UI name, default ClearLedger; no effect on financial state, roles or tenant scope. |
| Human outcome labels | PASS→Ready for processing, REVIEW→Needs review, HOLD→On hold; processing/stale eligibility/approval remain separate and detailed original states accessible. |
| worker_backoff | Allowlisted FINANCE/DOCUMENT stage and DATABASE_CONTENTION/DATABASE_UNAVAILABLE reason. No SQL, driver exception, document values, credential or success claim; existing durable lease/attempt semantics remain. |

## CL-04/CL-05 extraction continuation

| Field / version | Meaning and controls |
|---|---|
| printed-layout-v2 / labeled-header-table-layout-v4 | Measured stacked labels/values and bounded wrapped descriptions. Competing/crossing/incomplete rows abstain; unread native row fields remain explicit MISSING observations with no raw value/box. No fixture identity exceptions. |
| document_providers.ocr_backend / ocr_python | TESSERACT default or explicit RAPIDOCR_CPU_EXPERIMENTAL with an absolute isolated interpreter. Server settings, not document authority. Finance/inference environments stay intact. |
| routing.ocr_provenance | Actual per-page provider/version, package/model SHA/CPU sessions and measured initialization/RSS. Real fallback retains candidate failure and its actual provider. Configuration alone is not health. |
| routing.enterprise.version | extraction-routing-v3; strict extraction-v1 unchanged. Purpose/independent-heading scope limits questions, never eligibility. |
| question_scope_version / call_metrics | purpose-and-printed-columns-v1; actual fields, question/image counts and seconds. No prompt/source text or confidence. |
| accounting_grounding_version | independent-item-column-v1. Uncorroborated row discount/net/tax/gross keeps raw AMBIGUOUS and no canonical value; totals/arithmetic are not proof. |
| OCR_RUNTIME_PIN_MISMATCH / OCR_CPU_PROVIDER_REQUIRED | Startup attestation failure closes the child. An independently configured actual fallback records failure; no fabricated extraction. |
| Challenge score | Literal observations/core rows on frozen fictional layouts. Distinct from canonical completeness, representative accuracy, source confirmation or PASS. |
| Source-derived form defaults | Missing/ambiguous financial fields and unconfirmed eligible nights stay null/blank, even in development mode. Templates may offer explicit fictional business references; they cannot supply source amounts. |

## CL-06 table correctness

| Field / version | Meaning and controls |
|---|---|
| printed-layout-v3 / labeled-header-table-layout-v5 | Explicit common Seller/Invoice ID/Issue date aliases and independent measured-table association. No source identity exception or financial inference. |
| geometry_retry_version | missing-numeric-cell-v1: one absent numeric cell under unique printed headings with other measured row cells. At most three retries within the original deadline. |
| routing.ocr_provenance.runtime.row_retries | Actual field, integer crop_extents_pixels, scale 2, seconds and MEASURED_CELL_READ/UNRESOLVED/CROP_LIMIT/TIME_BUDGET. Crop extents never serve as evidence boxes. |
| bounded-cpu-row-retry span origin | Newly measured detector region, inverse crop-offset/scale and EXIF mapped to actual original coordinates. Competing/crossing/unrelated reads cannot fill a cell. |
| routing.enterprise.version / reused_tables | extraction-routing-v4; complete independent per-page observations retain source/scope/version and row count during header fallback. Strict extraction-v1 is unchanged. |
| table_coverage UNCERTAIN | An unread/uncertain page stays uncertain even if another page has observed or reused rows; it cannot silently satisfy full coverage. |
| Reserved row literal denominator | Checked fields on seven of eight new variants. r07 intentionally incomplete rows are excluded; its required missing-quantity canonical abstention is scored separately. Not invoice-level accuracy. |

## CL-07 unread cells and row identity

| Field / version | Meaning and controls |
|---|---|
| printed-layout-v4 / labeled-header-table-layout-v6 | Exactly one unread numeric core cell under unique measured headings can retain the row and following items; crossing/competing/multiple missing cells still abstain. |
| TABLE_CELL_UNREAD / SOURCE_CELL_UNREAD | No independently read value. Raw/canonical null, known source-page context, no invented field box. Does not establish absent versus illegible; reviewer confirms source. |
| routing.source_rows | Scoped SHA-256 request identity over document/version/tenant/entity/page/measured row extent, with row/page/unread fields. Row extents are not field boxes, value hashes or duplication proof. |
| extraction-routing-v5 / row_association_checks | Actual source-region identity or PAGE_ORDINAL_UNVERIFIED; strict extraction-v1 unchanged. Equal values in distinct measured regions/pages remain distinct. |
| generation_stops | Actual page/row/remaining/reason for duplicate measured-region requests or REPEATED_UNASSOCIATED_CANDIDATES. No synthetic call timing; unread remaining slots contain null values. |
| ROW_ASSOCIATION_UNCONFIRMED / MODEL_ROW_ASSOCIATION_UNCONFIRMED | Raw candidates retained ambiguous, no canonical quantity/amount. Remaining unassigned slots are unread. Does not declare genuine equal items duplicates. |
| document-normalizer-v3 / observation_diagnostic | New immutable traces preserve extraction diagnostic and source-specific/generic review findings. v2 histories remain retained; money arithmetic/finance decisions unchanged. |
| CL-07 readable row denominator | All 67 printed row literals on six new fictional variants, including q06's unresolved ten. A required null abstention is distinct from successful extraction. |

## CL-08 independent evaluation artifacts

| Field / artifact | Meaning and controls |
|---|---|
| clearledger-public-pixel-truth-v1 | Before-inference manual pixels, exact pinned source/license/README revisions and hashes; no author expected JSON or fixture injection. Public sources are externally authored fictional data. |
| money_tokens / contains_fields / accepted_states | Literal comparison only: printed currency token/whitespace removal for money, punctuation preserved; explicitly limited English substrings and accepted observation states. No locale normalization, Arabic fidelity or finance clearance. |
| row_matches / row_checked | Correct literal, accepted state and correct source page for all selected fields on all 19 source rows. Wrong/missing/ambiguous rows stay in the 86-field denominator. |
| absent / required_abstentions | Explicit MISSING/raw null is separate from canonical null. Safe null cannot inflate literal extraction success; invented zero does not satisfy missing tax. |
| clearledger-public-results-v1 | Limited attributed source facts/observed failures plus timing/call/provenance metadata. Full outputs/source pixels stay ignored; no confidential invoice/export is tracked. |
| source_classification_erratum | p01 frozen description says native but original PDF has zero native characters. Correction is explicit; frozen truth, originals and scores remain untouched. |
| end_to_end_seconds / upload_seconds | Actual loopback proxy/durable final-state observations at 0.5 s polling with resident CPU/model; excludes human/browser/approval time. Not a cold-load, paired improvement or VRAM measurement. |

## CL-09 source context and header repair

| Field / version | Meaning and controls |
|---|---|
| document-normalizer-v4 | New immutable traces recognize unique euro/rupee or supported explicit ISO codes; dollar/yen/pound alone stay unresolved. Existing v2/v3 traces/reports retain their versions. |
| number_format / number_format_source_observation_ids | Source-bound monetary separator convention and contributing PRESENT measured observations; never currency/country/FX or quantity/rate arithmetic. Strong mixed conventions and isolated three-digit separators without evidence are unresolved. |
| DERIVED_SOURCE_CURRENCY | Printed monetary tokens agree on a supported unique currency. Actual monetary locator retained; derivation step explains that it is not a separately printed Currency field. Conflicting/nonunique tokens stay ambiguous. |
| printed-layout-v5 / labeled-header-table-layout-v7 | Qualified stacked headers with measured alignment, bounded native font overlap and independently separated left text; inline values retain their own row. Metadata table cells require measured nonoverlap and all financial/unit anchors. |
| PROVIDER_VALUE_UNREAD | Actual null model text becomes ILLEGIBLE/raw null. No fabricated literal null and no contradiction of an independently measured PRESENT source. Real non-null conflict/illegibility remains unresolved. |
| extraction-routing-v6 / independent-header-coverage-v1 | Reuse independent headers across pages and previous actual reads; request unresolved core and first-page supplementary addresses when measured coverage exists. Human conflicts are not model votes. Strict extraction-v1 and finance authorization unchanged. |
| reused_header_fields / header_fields_requested / call_metrics | Actual per-page known/requested field lists and executed model times/calls. No synthetic latency/confidence or extraction PASS. |
| independent-document-summary-v1 / SOURCE_HEADER_AMOUNT_UNCONFIRMED | Model-only document tax/discount/shipping/other charges without an independently read summary label retain raw AMBIGUOUS and canonical null. Item tax/amount and guessed zero do not establish summary scope. |
| CL-09 development/reserved probes | Four inspected development sources plus two additional source-fact probes frozen before tuning, sharing author/template families. All selected row fields remain counted; reserved null checks are distinct from literal success. No real-company or genuinely new-layout-family accuracy. |

## CL-10 measured geometry and partial source rows

| Field / version | Meaning and controls |
|---|---|
| measured-ocr-layout-alignment-v1 / native 8 / printed-layout-v6 | Four rigid measured layout candidates; unique printed ownership/physical axes select, weak/tied cases abstain. Small consistent global baselines ≤8° only. Not confidence or a finance decision. |
| polygon_layout_pixels / layout_axis_pixels / layout_bbox | Actual detector quadrilateral in preview pixels; transformed physical dimensions/layout envelope used for association. Original normalized source `bbox` stays independently measured and unchanged. |
| layout_alignment / transform | Status, actual cardinal/residual measured angle/support and rigid matrix/source/layout dimensions; source fixture angle never enters inference. `image_bytes_transformed:false` describes coordinate alignment only. |
| aligned_pixel_read | Optional ONE actual private in-memory aligned CPU read: actual PNG hash/dimensions/source transform/Pillow version, `image_bytes_transformed:true`; no original/preview mutation. Layout refinement uses its measured polygons without another pixel read. |
| excluded_source_regions | Actual aligned detector regions inverse-projecting outside original canvas, retained privately with raw text/extents/reason. Excluded from source facts; no clipped or invented source box. |
| alignment_read_disagreements / OCR_ALIGNMENT_READ_DISAGREEMENT | Actual corresponding source-region conflicting read literals and original locator; AMBIGUOUS/canonical null/source confirmation, no model vote. Separate segmentation is not automatically disagreement. |
| missing-numeric-cell-v2 / layout_to_preview_transform | Existing ≤3 numeric-cell retries share page/document deadlines; layout context inverse-projects to unchanged source preview, then measured new detector fields project through independent EXIF. Crop extents are not field boxes. |
| Two unread quantity/price slots | Measured description+amount under unique independent columns can retain partial/following distinct rows. Both missing raw/canonical null, precise SOURCE_CELL_UNREAD questions, no arithmetic/value/UOM/tax guess. Crossing/unanchored/competing rows remain uncertain. |
| clearledger-rotation-truth/measurement-v1 | Three frozen original-fictional families/ten correlated variants; two initially reserved families/seven variants now spent. All wrong/missing/ambiguous literals stay in denominator; safe null is scored separately. Baselines, first reserved, spent replay, failed/final live results remain distinct. |

## UI-01 presentation and probe sidecars

`NEXT_PUBLIC_PRODUCT_NAME` remains build-time public presentation only (trimmed, maximum48 characters); fallback is now Kivo. It changes the displayed name/monogram, never tenant/company identity, policy, source provider or authority. `Prepare review` labels existing FINALIZE job success and makes no human-confirmation assertion. Ready for processing remains existing PASS with current eligibility; stale PASS displays Needs review. PAID duplicate prose is derived only from resolved pinned historical evidence. No backend contract, database field, currency/Decimal representation or financial state was changed.

The separately frozen `data/kivo_fresh/manifest.json` is benchmark truth, not extraction-v1/API/defaults. `family`, `scanned`, original source SHA256, literal header/row expectations, absent fields and canonical abstentions are used by the existing harness after extraction. Two families/four variants are correlated, now-spent fictional sources; expected values/instructions are never provider input other than untrusted original document pixels/text. Private timing/provenance/output, screenshots and PDF stay ignored. Native/OCR results and UNKNOWN/missing/ambiguous tax/date/currency/row behavior do not change canonical finance schemas or rules.


## REL presentation replay and extraction sidecars

| Name | Meaning and authority |
|---|---|
| `kivo:mutation:v1:<SHA256>` tab key | Hash of actual server `/me` tenant/entity/actor, endpoint and ordered input; value is random idempotency UUID. No plaintext document/policy/body/credentials stored. Transport replay only; never authorization/business identity. |
| New source draft line `id` | Omitted when constructing a new source case; the existing backend assigns distinct UUIDs after canonical validation. Existing case-revision line IDs remain. No canonical schema change. |
| `maximum_bytes`, `maximum_pages` | Existing intake-capabilities values displayed in upload UI; whole oversize selection rejected before upload sessions. Backend enforcement remains authoritative. |
| Repeated `pages[].page_sha256` | Existing rendered-page digest identifies exact copies for a visible source correction notice. Original pages/rows retained; no automatic financial duplicate finding or deduplication. |
| `printed-layout-v7`, native adapter `9` | Generic measured complete-heading association shared by table parsing/printed-column detection/bounded cell routing; original source boxes, generic row grouping and extraction-v1 unchanged. Unsafe/competing geometry abstains. |
| `CONFIGURED_NOT_NEEDED`, `SOURCE_CELL_CONFIRMATION_REQUIRED` | Existing routing states observed after repaired h02 OCR captures readable cells; missing cells still require human/source information. Zero VLM calls is not model accuracy or a finance approval. |
| `kivo-reliability-truth-v1` | Frozen original-fictional source hashes/literal scorer truth, split/family/correlation/required nulls. Reserved naming is historical; split is spent. Never production defaults/provider input. |
| `kivo-reliability-sanitized-evidence-v1` | Recorded run labels, source/truth/code/measurement hashes, scores, actual paths/calls, elapsed seconds, abstentions and limitations. Private document IDs/full source outputs omitted. |
| Bounded snapshot members | Same scoped immutable manifest/digest/UUID/member relation and database constraints, inserted in 500-row batches. No database schema or evaluation-selection change. |

Financial strings/Decimal, UNKNOWN versus missing/ambiguous/zero, source confirmation and historical version/audit meanings are preserved. Actual displayed fictional hotel version 52/INR 9,000 does not overwrite version 48. [Verification](kivo_reliability_verification.md) records current and historical context separately.


## REL-04 test-only concurrency measurements

No production/financial schema changed. `kivo-concurrency-evidence-v1` is a sanitized test evidence sidecar, never a policy, API authority, source correction, score or model input. `advisory_wait_ms` measures the actual PostgreSQL lock-query round trip; `transaction_ms` spans the complete sampled database-session operation and commit/rollback. `COMMITTED` means database effects committed, not finance PASS. `round` distinguishes initial receipt admission and admission after explicit duplicate disposition. All authoritative finance amounts/quantities remain Decimal.

Actual existing `lock_timeout_ms=5000`, per-statement `statement_timeout_ms=10000`, `lease_seconds=60` and maximum attempts 3 are documented boundaries, not throughput promises. SQLSTATE55P03 denotes lock-not-available/timeout; current public API safely maps it to retryable DATABASE_UNAVAILABLE/503, and worker classification schedules bounded recovery. Test-only timings contain no SQL, parameters, credentials, private source/actor IDs or business values. Full private measurements stay ignored. [Evidence/conditions](kivo_concurrency_verification.md).
