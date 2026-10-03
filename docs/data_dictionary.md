# Domain glossary and implemented foundational contracts

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
