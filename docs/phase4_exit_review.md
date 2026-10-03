# Phase-4 exit review — Human workflow and operational reliability

Disposition: **COMPLETE LOCALLY — EXIT GATE PASSED**. Direct approval authorizes
P4-01–P4-04 continuously. Phases 0–3 and the separate enterprise-runtime deferral
remain preserved. Phase 5 has not begun.

## Task and exit criteria

| Task | Implemented behavior and evidence |
|---|---|
| P4-01 | Reuses review_cases with owner/version; claim, release, authorized reassignment, internal information request, source/canonical correction and typed resolution/waiver/cancel actions. Actual synchronized competing claims admit one owner. A resolves review v4 to v5; stale B receives 409 and A's resolution remains. Claimed legacy mutations obey the review guard. Evidence remains server-authorized and source-linked. |
| P4-02 | Derived current eligibility and CURRENT/SUPERSEDED/STALE reports preserve immutable historical outcomes. Material revision invalidates approvals and compensates reserved resources. Cancellation preserves facts/evidence/audit, cancels work and cannot revive eligibility. Nonzero 100 reservation releases once; PO/GRN/receipt/budget history is append-only. New company-payment evidence invalidates current PASS and blocks consumption. 50,000→150,000 requires Manager/Director instead of stale Manager/Head authority. |
| P4-03 | Classified bounded retries, safe terminal/dead-letter metadata, scoped operations permission, bounded audited manual recovery, minimal public health, honest dependency configuration, stale worker rejection, guarded reconciliation and deterministic pinned digest replay. Repeated recovery does not duplicate evaluation, release or repair audit. Real absent required enterprise assets preserve preprocessing and failed extraction; no empty success or transaction/PASS. |
| P4-04 | Actual measured workload/activity, server filters/pagination for queue/transactions/jobs, deterministic next actions, typed field and receipt-share inputs, audit timeline and private permissioned JSON/HTML/CSV exports. Actual backend browser flows cover evidence, stale forms, correction, authority/resolution, retained reports, auditor download, permanent failures and filter/error/empty/focus/laptop/mobile behavior. |

The specification exit is demonstrated by the full exception resolution: retain
original HOLD, claim/request information, correct an actual source-linked PDF fact,
append canonical versions, obtain fresh version-bound authority, compute PASS,
resolve the human case and retain the original decision/report. A second reviewer
cannot overwrite that accepted case version. Failure/lease/retry/cancellation and
reconciliation tests retain a single logical financial effect.

There is no unrestricted decision override, payment execution, replacement reviewer
system, outbound messaging, GPU work, inference deployment or Phase-5 ML.

## Retained history and authorization

Original canonical versions, observations, source verifications, evaluations,
contexts, rules, evidence, reports, allocation/budget events and audit remain.
The original 20-control evaluator and Phase-3 28-control evaluator are unchanged.
New immutable workflow/operation facts have forced tenant/entity RLS and scoped
keys; ORM/direct-SQL mutation fails. Replayed PASS, duplicate HOLD and allowance
REVIEW use stored facts, exact evaluator/time and result digests, without OCR/VLM.
Existing policy-change replay retains original T42 coverage.

Reviewer, approver, duplicate/share/waiver, ledger, export, audit and operational
permissions remain distinct. New development identities are separate fictional
operations administrator, auditor and review manager; existing roles stay unchanged.
The public dependency response is minimal. Evidence/export UUID knowledge grants
no access. Export creation/access is audited, private/no-store and digest checked;
formula-prefix cells are escaped only in CSV output. Historical JSON view remains
the original immutable contract; live status is a separate labeled projection.

## Database and operational limits

Head `0006_workflow` adds two fact tables and review/job projection fields: 49
business tables plus Alembic. Prior migrations are unchanged. Actual development
upgrade preserves data. Fresh isolated upgrade/base downgrade/re-upgrade, constraints,
numeric precision, forced RLS and cross-scope tests remain part of the suite.
Alembic check reports no new upgrade operations.

The conservative scope lock and existing lease/generation guards remain. Retry
classification does not save exception text or provider payloads. Three automatic
attempts plus at most two authorized three-attempt recovery cycles are bounded.
Permanent invalid input, missing mandatory input/configuration and superseded work
cannot be arbitrarily re-executed. Required audit failure rolls back business effects.

Reconciliation repairs expired leases, cancelled active reservations and delayed
consumed outbox notification. Missing completed projection queues fresh admission.
It inspects at most 100 metadata objects per category and 1,000 scoped directory
entries; it is explicitly bounded. Missing retained reports/originals/pages stay
unresolved pending exact artifact recovery; unfinalized upload intent is not inferred.
Orphan objects are retained and surfaced. No organization retention, backup restore,
destructive cleanup, full sweep or executor heartbeat is claimed.

PDF export remains deferred; JSON/HTML/CSV are implemented. Production SSO, real
data/policies, external VLM, scanner, operational availability/backup guarantees and
Azure deployment remain outside this gate. T29/T39 now have supported application
tests; T30/T33 remain partial for missing finance ML interactions. T31/T34 are
NOT IMPLEMENTED — PHASE 5. No 42/42 or production-readiness claim.

## Verification

| Command/check | Actual result |
|---|---|
| `.venv/bin/pytest -q` final code | Exit 0, 720 passed, 1452.86s; zero failures/skips, one upstream Starlette/httpx deprecation warning. |
| `.venv/bin/pytest -q apps/api/tests/integration/test_workflow_phase4.py apps/api/tests/integration/test_finance_phase3.py::test_budget_ledger_consumption_reversal_and_immutability` | Exit 0, 16 passed, 397.78s at the checkpoint before adding the final transient recovery test. |
| Final authorization and amount-filter check | Exit 0, 1 passed, 22.22s. |
| `.venv/bin/pytest -q apps/api/tests/integration/test_workflow_phase4.py::test_transient_document_storage_failure_exhaustion_allows_bounded_recovery` | Exit 0, 1 passed, 24.31s; one READY document and one page artifact. |
| Transaction batching/filter/pagination checks | Exit 0, 2 passed, 48.43s. |
| `npm --prefix apps/web run test:e2e` on final API/web/worker | Exit 0, 27 passed, 1.6m; zero retries. |
| `npm --prefix apps/web run typecheck` / `run build` | Exit 0 / exit 0, final production build. |
| `npm --prefix apps/web run generate:api` | Exit 0, current OpenAPI/types. |
| `.venv/bin/alembic -c apps/api/alembic.ini check` / `current` | Exit 0, no drift / 0006_workflow head. |
| `.venv/bin/python -m pip check` | Exit 0, no broken requirements. |
| `node --test apps/web/checks/development-identity.mjs` | Exit 0, 1 passed. |
| Source pack / finance fixtures / extraction fixtures SHA-256 | Exit 0; original inputs preserved. |
| Restarted final owned API/worker/web; `/api/v1/health/live`, `/api/v1/health/ready`, `/operations` | Exit 0; 200 / 200 / 200. Public health exposes only alive/ready. |
| `git diff --check`, original evaluators/migrations and publication exclusions | Exit 0; original evaluators and five prior migrations unchanged. 43 intended changed files; no private runtime paths or detected credential signatures. |
| Local documentation link check | Exit 0, 124 local targets resolve. |

Intermediate failures were repaired and recorded in progress. Earlier full runs
were interrupted to run final code after the last batch; interrupted pytest
teardown does not count as a passing regression. Final aggregate results alone
close this gate. Logs/screenshots/runtime exports remain ignored/private.

## Local performance

`scripts/benchmark/workflow_phase4.py` executed in an isolated migrated test schema
with 100 computed synthetic cases, then removed only that owned schema.

| Operation | Samples | Median ms | p95 ms |
|---|---|---|---|
| Review queue, 25 rows | 10 | 18.470 | 25.302 |
| Case detail | 10 | 3.095 | 4.348 |
| Audit timeline, 50 rows | 10 | 3.439 | 4.791 |
| Dashboard | 10 | 6.762 | 9.431 |
| Assignment | 10 | 46.968 | 74.095 |
| CSV report generation | 10 | 72.753 | 97.391 |
| Reconciliation | 3 | 690.823 | 690.823 |
| Correction + reevaluation | 1 | 631.204 | Single sample |
| Cancellation | 1 | 49.628 | Single sample |

Warm local single-process measurements, not an SLA/load/inference benchmark.
EXPLAIN ANALYZE chose sequential review scans at this small scale and existing
audit/job indexes. The one new scope/owner/state/order index matches the actual
ownership query; no further indexes were justified by these measurements.

## Publication and next boundary

Phase-4 publication has not yet been attempted. Prior consolidated pushes are
authentication-blocked; credentials will not be repaired or retried. Verified local
commits and exact publication outcome will be recorded before the final report.
Local implementation batches: `c07e6ad` (backend/schema/recovery) and `81b7c96`
(operational UI/browser contract). The final gate/documentation commit records the
passed aggregate and preserved boundaries before publication.
The next phase is Phase 5 and requires separate user approval; no ML work begins.
