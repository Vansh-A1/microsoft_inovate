# Phase-1 exit review — Rules-first vertical slice for both branches

**Disposition: COMPLETE LOCALLY.** P1-01–P1-06 and all mandatory local Phase-1 criteria are satisfied under the 2026-10-03 continuous approval. This is a synthetic local development product, not a production pilot. Phase 2 has not begun. Git publication is a separately reported external gate; the user explicitly permits local completion when authentication is unavailable.

## Working end-to-end behavior

The browser loads original fixture-derived canonical examples from the API. Users create a vendor invoice or employee expense, or preview/commit a CSV/XLSX import. PostgreSQL retains canonical facts, revisions, raw import cells and validation errors. Evaluation requests create durable jobs and outbox records. The worker pins a reference/context snapshot, computes the rules, checks fresh capacity and current intent, and atomically persists the evaluation, all 20 checks, evidence, JSON/HTML report, audit and any eligibility reservations. Cases display actual processing state and decision; REVIEW/HOLD appear in the filtered exception queue. Evidence resolves through scoped API lookup. Corrections append versions and invalidate current eligibility without overwriting history.

New submissions cannot assert approvals. Trusted synthetic approvals are installed only by the development seed. Newly submitted otherwise clean examples therefore commonly HOLD; the authorized seeded clean cases genuinely PASS.

| Task | Result |
|---|---|
| P1-01 | COMPLETE: pinned isolated backend/frontend stack, three PostgreSQL migrations, private filesystem objects, durable jobs/outbox. |
| P1-02 | COMPLETE: server-derived tenant/entity identity, strict canonical creation/revisions, CSV and XLSX preview/commit with retained invalid rows. |
| P1-03 | COMPLETE: executable required-field/arithmetic/date/currency, party, exact duplicate, basic PO/GRN, expense, budget and approval controls. |
| P1-04 | COMPLETE: HOLD-first precedence, immutable facts/evaluations/context/evidence/reports, atomic audit, deterministic JSON/HTML. |
| P1-05 | COMPLETE: real API overview, create/import, list, case, evidence/rules, exception queue and reports; production build and browser inspection. |
| P1-06 | COMPLETE: five computed combined demos and eight separately tested supported golden alternatives. |

## Implemented architecture

- Backend: FastAPI 0.142.2 / Pydantic 2.13.5, SQLAlchemy 2.1.2, Alembic 1.20.0, psycopg 3.3.6, uvicorn 0.54.0; Python 3.13.11. Pure rule execution is independent of routes, DB, clock, extraction and models. Full transitive dependencies are locked in `apps/api/requirements.lock`.
- Database: PostgreSQL 16.15, 22 business tables plus Alembic metadata. Bounded immutable reference catalog/linkage represents existing vendor/employee/PO/GRN/policy/budget/history fixtures. UUIDs, scope-qualified FKs, Numeric money/quantity, forced RLS and SQL immutability triggers. Application role is NOSUPERUSER/NOBYPASSRLS.
- Jobs/outbox: at-least-once polling, `SKIP LOCKED`, 60-second lease, three attempts, bounded backoff, compatible stage/ruleset gating and latest request generation. Finalization checks owner/deadline/version/generation before atomically committing effects. Local outbox consumption is implemented; no external broker exists.
- Frontend: Next 16.3.8 / React 19.3.0 / TypeScript 5.9.3, Node 24.21.0 LTS, generated OpenAPI intake types and private loopback API proxy. Package lock committed; no public/browser bearer token or body-supplied role/scope. Batched transaction list reads avoid per-case queries and fetch only current canonical facts; full history remains on detail.
- Extraction: **STRUCTURED_SYNTHETIC** for this app; existing **FIXTURE** adapter and ten-case extraction harness remain intact separately. No source image/bounding box claim.
- Finance risk: **RULES_ONLY / NOT_CONFIGURED**, no score, ML or live VLM dependency. No payment execution.

## Actual rule catalog

Final ruleset **rules-p1-v7**, each rule **1.0.6**, decision policy **hold-first-p1-v1**, report schema **report-p1-v2**. Every evaluation persists every rule exactly once, including explicit branch-only NOT_APPLICABLE results. Required UNKNOWN/ERROR prevents eligibility. Any HOLD effect dominates all other results; REVIEW follows; complete applicable controls alone permit PASS.

| Rule ID | Implemented behavior in the supported synthetic slice |
|---|---|
| VAL-001 | Required header fields and nonblank values; absent critical facts are explicit UNKNOWN. |
| VAL-002 | ISO dates, date ordering/not future at supplied evaluation time, supported INR currency. |
| VAL-003 | Decimal/Money exclusive-tax line and document arithmetic; explicit discount/shipping/other/tax and employee company-paid/advance operands. Missing operands are UNKNOWN. |
| VEN-001 | Vendor resolves to the pinned scoped master. |
| VEN-002 | Vendor is approved and active. |
| VEN-003 | Submitted synthetic account token equals approved master/source; mismatch HOLD, master unchanged. |
| DUP-002 | Confirmed same-vendor normalized number/date/amount/currency against scoped indexed history/current eligible cases; excludes cancelled/reversed and current identity. Missing lookup inputs are UNKNOWN. |
| PO-001 | Required approved, effective, open purchase order exists. |
| PO-002 | PO vendor/entity/currency/category/budget associations match. |
| PO-003 | Line UOM, unit price, tax and configured MAX tolerance; unapproved extra charges. Unresolved terms remain UNKNOWN. |
| PO-004 | Cumulative quantities/gross value fit approved PO capacity. |
| GRN-001 | Net accepted quantity after returns, historical and active consumption covers the invoice; exact shortfall and allocation sources. |
| EMP-001 | Employee active and effective; branch dimensions match. |
| DOC-001 | Canonical values reconcile with pinned verified synthetic JSON source facts. No real document verification is implied. |
| EXP-001 | Required readable adequate receipt facts under the selected synthetic expense policy. |
| EXP-003 | Verified hotel nights or local-day allowance aggregate, including paid/reserved/current claims and their IDs. |
| BUD-001 | Fresh matching budget dimensions/gross basis/currency; incremental exposure against available capacity with PO commitment coverage counted once. |
| APR-001 | Amount-band mandatory approval sequence, completeness, policy/version/time/order and canonical-version binding. |
| APR-002 | Effective actor authority, role/cost-center/department/manager and basic separation of duties. |
| SYS-001 | Complete supported rules-only context; unsupported currency/type/partial receipt allocations cannot PASS. |

INR uses a private precision-60 Decimal context, HALF_EVEN rounding and explicit 0.01 reconciliation tolerance. The configured fixture approval bands are <10,000 Manager; 10,000–<100,000 Manager + Department Head; 100,000–<500,000 Manager + Director; >=500,000 Manager + CFO. These are synthetic demo policies, not a real company's authority matrix.

## Computed demos

| Scenario | Transaction UUID suffix | Computed result | Main evidence/control |
|---|---|---|---|
| Clean vendor invoice | 001 | PASS, eligible | 20 units; INR 23,600; approved PO/GRN, existing commitment coverage and completed approval chain. |
| Paid duplicate vendor | 002 | HOLD, ineligible | DUP-002 cites same vendor/number/date/amount/currency in paid historical transaction. |
| Clean employee taxi | 005 | PASS, eligible | INR 2,400 versus 3,000/day, authorized employee, full receipt, budget and Manager approval. |
| Daily meal exception | 008 | REVIEW, ineligible | EXP-003: 600 paid + 600 reserved + 600 current = 1,800 versus 1,500/day, linked claim evidence. |
| Missing mandatory approval | 004 | HOLD, ineligible | APR-001 identifies absent Department Head step. |

All five IDs begin `30000000-0000-4000-8000-000000000`. Seed reruns preserve history and do not duplicate logical effects. Expected decision labels are used only as independent test assertions, never as evaluator input/results.

## T01–T42 disposition

The [scenario matrix](test_coverage.md) retains the original scenario/expectation text and names actual executed tests.

- **IMPLEMENTED + PASSING (21):** T01, T02, T03, T06, T08, T11, T12, T13, T14, T15, T16, T23, T24, T25, T26, T28, T32, T35, T36, T37, T38.
- **PARTIALLY IMPLEMENTED (11):** T04, T07, T10, T21, T27, T29, T30, T33, T39, T40, T42.
- **NOT IMPLEMENTED (10):** T05, T09, T17, T18, T19, T20, T22, T31, T34, T41.

Partial rows retain their missing behavior explicitly; shared receipt/image/fuzzy/provider/ML and full-policy workflows are not reported as complete. Full T01–T42 production release coverage is not claimed.

## Working API inventory

All business endpoints require trusted scope; mutations require FINANCE_REVIEWER and Idempotency-Key. Cross-scope resources return 404, read-only writes 403, stale/conflicting retries 409, schema failures 422, unavailable dependencies 503. Decisions HOLD/REVIEW are business results, not 500 errors.

| Method | `/api/v1` path | Behavior |
|---|---|---|
| GET | `/health/live`, `/health/ready` | Process/mode and migrated PostgreSQL readiness. |
| GET | `/me`, `/references` | Trusted development identity and scoped fixture reference view. |
| GET | `/development/templates/{vendor\|employee}` | Canonical fixture-derived input without authority. |
| POST / GET | `/transactions` | Persistent canonical creation / filtered batched list. |
| GET | `/transactions/{id}` | Current facts, immutable revision history and latest job. |
| POST | `/transactions/{id}/revisions` | Expected-version correction; append history/invalidate eligibility. |
| POST | `/transactions/{id}/evaluate` | Expected-version async durable evaluation, 202/job ID. |
| GET | `/jobs/{id}` | Persisted stage/state/attempts/result and safe error. |
| GET | `/evaluations/{id}` | Immutable report projection plus current eligibility. |
| GET | `/evaluations/{id}/report?format=json\|html` | Authoritative deterministic export with all passed/failed required checks. |
| GET | `/evidence/{id}` | Authorized pinned source/reference/import cell/approval lookup. |
| GET | `/reviews` | Open REVIEW/HOLD; decision/branch/reason/minimum_age_days filters. |
| GET | `/overview`, `/audit?object_id={id}` | Actual persisted counts and scoped audit events. |
| POST | `/imports/preview`, `/imports/{id}/commit` | CSV/XLSX row validation, retained errors, valid transaction/job linkage. |
| GET | `/imports/{id}` | Retained raw/error/link/status projection. |

OpenAPI is saved at `packages/api-client/openapi.json`; backend serves `/docs`. The frontend proxies this bounded API subset with its private trusted context.

## UI verification

All screens were production-built, run and inspected through real browser flows: overview, create/import, transactions, case detail, rule/evidence inspector, exception queue and JSON/HTML report view. Browser checks cover actual API data, both branch submissions and retained reloads, seeded decisions, resolved evidence, report iframe, import status/errors, queue filters, empty results, delayed loading, simulated API error, cross-origin rejection and 390-pixel mobile layout. The error test intercepts only the selected error response; ordinary decision flows use the actual backend/worker.

Desktop overview, vendor case/evidence and employee HTML report screenshots plus the mobile create screen were visually inspected. Generated screenshots/results are ignored at `output/playwright/`. The running local product is [AP Review Desk](http://127.0.0.1:3000).

## Database and exact verification

Migrations `0001_phase1`, `0002_inputs`, `0003_generation` are versioned source; the application is at head `0003_generation`. Every integration case starts a fresh migrated UUID-named schema in a separate test database. Upgrade/downgrade/upgrade, seeding, constraints/FKs, Numeric scale, bulk-update immutability, all 22 forced RLS policies, non-superuser/no-BYPASS role and scoped application operations passed. `alembic check` reports no new upgrade operations. No application SQLite fallback was used.

The [local runbook](runbooks/phase1-local.md) records tested bootstrap/migration/seed/run/build/test commands. Dependencies install in project scope; user-space PostgreSQL/Node are SHA-verified. No sudo, system package installation, Docker permission changes or cloud provisioning.

Final gate: **569 passed, 0 failed, 0 skipped** in 197.53 seconds (488 preserved Phase-0 + 44 pure rules + 37 PostgreSQL integration); browser **11 passed, 0 failed, 0 skipped** in 9.4 seconds. Strict TypeScript and the production Next build passed. Exact commands are recorded in [progress](progress.md). The original 488 tests remain unchanged. New tests exercise pure rules, persisted both-branch golden decisions, authorization, revisions/stale requests, immutable facts, resolved evidence, imports, atomic audit failure, leases/retries/current intents and concurrent budget/GRN admission. The last list-query refinement has a dedicated bounded-query/current-version/latest-job integration test and a complete regression rerun. One upstream Starlette/httpx TestClient deprecation warning is non-fatal.

## Financial invariants actually verified

| Invariant | Evidence |
|---|---|
| Decimal-safe money | Unsafe float/bool/scientific/grouped input rejected; exact original Money regression, private precision and Numeric columns tested. |
| UNKNOWN distinct | Missing headers/line operands/denominators/source context yield explicit UNKNOWN, never zero or PASS. |
| Mandatory HOLD dominates | Pure combiner tests and duplicate/approval/GRN persisted cases; no aggregate confidence/model score. |
| Immutable evaluation | Database triggers protect versions/context/evaluations/rules/evidence/report/audit; reevaluation supersedes without changing old report. |
| Tenant/entity isolation | Non-superuser forced RLS and server-derived identity; cross-tenant source/report/evaluation 404 and foreign-entity raw query empty. |
| Idempotent effects | Stable same-key responses, changed-body 409; lease recovery/retry has one logical evaluation/report and capacity effect. |
| Fresh eligible capacity | Concurrent budget and GRN competing cases cannot both over-admit; old version/intent/stage cannot publish; revision releases old screening reservations. |
| Atomic audit | Simulated audit failure rolls back creation or PASS/evaluation/report/reservations; no uncoupled eligibility. |

Audit has a tenant-sequenced hash chain but no external tamper-proof anchor. Minimal reservations protect screening; no payment/settlement ledger is claimed.

## Source preservation

All **nine original inputs**, **23 finance JSON files**, and **11 extraction JSON files** pass their unchanged checksum manifests. `docs/AP_Exception_Assistant_Codex_Spec.md` remains byte-identical to the 123,229-byte source specification. Domain/extraction modules, original 488 tests, fixtures and Phase-0 history are preserved; no original labels/data were rewritten to fit the engine. Runtime/private credentials/cluster/storage/browser artifacts remain ignored.

## Mandatory Phase-1 exit criteria

| Criterion from the user approval | Disposition |
|---|---|
| User can submit structured synthetic data for both branches | SATISFIED — API and browser create flows, CSV/XLSX intake. |
| Records persist | SATISFIED — actual PostgreSQL and browser reload. |
| Real deterministic rules execute | SATISFIED — pure engine reused by durable worker. |
| PASS / REVIEW / HOLD computed, not hard-coded | SATISFIED — independent golden expectations and demo engine outputs. |
| Rule results persist | SATISFIED — all 20 controls per evaluation. |
| Evidence persists and resolves | SATISFIED — every golden rule's evidence fetched with scope enforcement. |
| Evaluations immutable | SATISFIED — trigger/bulk update and supersession tests. |
| Audit events exist | SATISFIED — creation/revision/job/evaluation/review/report/import plus rollback tests. |
| JSON/HTML report works | SATISFIED — persisted API exports and browser report. |
| Exception queue works | SATISFIED — REVIEW/HOLD persisted, filters/empty state tested. |
| Case detail works | SATISFIED — canonical versions/job/rules/evidence/report shown. |
| Frontend uses actual API data | SATISFIED — real production browser suite. |
| Clean vendor PASS exists | SATISFIED — computed seeded/golden vendor. |
| Clean employee PASS exists | SATISFIED — computed seeded/golden taxi. |
| Duplicate exception exists | SATISFIED — exact paid historical match HOLD. |
| Allowance exception exists | SATISFIED — daily meals aggregate REVIEW. |
| Missing approval HOLD exists | SATISFIED — absent Department Head and unauthorized approver tests. |
| No ML dependency | SATISFIED — RULES_ONLY / NOT_CONFIGURED; no risk score. |
| No live VLM dependency | SATISFIED — structured synthetic input and preserved separate fixture adapter. |
| Tests pass | SATISFIED — complete Python regression, production typecheck/build and live browser suite. |

## Full-product acceptance review and limits

| Specification gate | Current supported evidence / remaining release work |
|---|---|
| AC01 | Supported both-branch persisted slice verified. |
| AC02 | Basic required controls implemented; full contract/service, shared receipt, advanced policy matching deferred. |
| AC03 | Supported findings resolve pinned records or show missing evidence. |
| AC04 | Complete fresh supported controls/approvals/capacity guard PASS; no payment. |
| AC05 | Queue/next action/canonical correction works; full human resolution/approval workflow deferred. |
| AC06 | Exact duplicate/retry behavior works; fuzzy/image/shared allocation deferred. |
| AC07 | Canonical versions, imports and superseded decisions traceable; real raw-document/extraction chain deferred. |
| AC08 | PASS/REVIEW/HOLD throughout; processing remains separate. |
| AC09 | Honest T01–T42 matrix; full production deterministic/concurrency/security release gate incomplete. |
| AC10 | Trusted scope/roles/stale writes/basic authority tested; production OIDC/complete authority workflow deferred. |
| AC11 | Minimal budget/GRN/retry admission tested; receipt/settlement/cancellation lifecycle deferred. |
| AC12 | Audit atomicity and current pinned-input replay tested; changed-policy/legacy replay and external anchoring deferred. |
| AC13 | Missing facts/context/unsupported modes cannot PASS; real provider outages deferred. |
| AC14 | Private local storage, ignored generated credentials and authorized evidence tested; production storage/retention deferred. |
| AC15 | Prior compatibility research/blockers preserved; live image compatibility/quality still deferred. |
| AC16 | Visible RULES_ONLY / NOT_CONFIGURED satisfies this phase's authorized no-model mode; no ML metrics claimed. |
| AC17 | No SHAP delivered; later model-specific gate. |
| AC18 | Local setup/migrations/seed/process and clean backup boundary documented; production restore exercise deferred. |
| AC19 | No performance/SLA claim; explicit query bounds and tested batched reads only. |
| AC20 | Local synthetic demo labeled honestly; no deployed pilot/restore/monitoring/rollback claim. |

Other limits: INR ordinary exclusive-tax invoices, goods PO/GRN and fully attributed ordinary receipts only. CSV/XLSX uses a single `transaction_json` text column, not arbitrary workbook mapping. Partial receipts abstain. No fuzzy/pHash, advanced allocation/waivers/delegation, real master import activation, PDF/OCR/preprocessing, live TypeLLM/SGLang/VLM, ML, cloud deployment or production SSO. No live company policy/data supplied. Private orphan import objects may remain after rollback; reconciliation is deferred. The owned local cluster and services remain running for review.

## Git publication

Coherent Phase-1 commits preserve all Phase-0 history. The final verified commit/tree and the one authorized normal `main` push outcome are recorded in progress and the completion report. No force push, credential repair or repeat publication attempt is authorized. Local completion remains independent of an authentication blocker.

## Next major batch only

After explicit approval, start Phase 2 with secure original upload/finalization, quarantine/limits, private source storage and preprocessing/source mappings behind the existing provider contract. Live GPU inference continues to require separately suitable approved infrastructure. Do not implement Phase 2 under this closure.

Waiting for approval to begin Phase 2.
