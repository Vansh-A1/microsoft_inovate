# Phase-4 local review and recovery runbook

Extends [Phase-3 finance setup](phase3-local.md). Use the existing owned CPU stack
and synthetic sources. Do not repair GPU/Docker prerequisites or configure a risk
model for this phase.

```bash
.venv/bin/alembic -c apps/api/alembic.ini upgrade head
.venv/bin/python scripts/dev/setup_workflow_identities.py
export PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH"
npm --prefix apps/web run generate:api
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
.venv/bin/python scripts/dev/run.py
```

The setup creates three separate, scope-bound fictional identities. It preserves
all existing roles, stores tokens in ignored private configuration, and prints
labels only. The loopback supervisor enables the existing development picker.
This is not production authentication or SSO.

| Permission | Authorized work |
|---|---|
| FINANCE_REVIEWER | Claim/release owned cases, request information, evidenced correction, cancel unconsumed obligations, resolve after fresh eligibility. |
| REVIEW_MANAGER + FINANCE_REVIEWER | Reassign to another trusted configured reviewer in the same entity. |
| MANAGER / DEPARTMENT_HEAD / DIRECTOR / CFO | Act only within effective master/delegation authority, sequence, scope and ceiling; separation of duties still applies. |
| DUPLICATE_REVIEWER / RECEIPT_ALLOCATOR / FINANCE_CONTROLLER | Respective evidenced duplicate/share/waiver actions; claimed ownership and policy restrictions remain enforced. |
| LEDGER_ADMIN | Explicit resource lifecycle transitions; consumption requires fresh current eligibility. |
| OPERATIONS_READER | Read scoped operational status and failures. |
| OPERATIONS_ADMIN | Bounded retry and reconciliation; no finance decision, approval or export authority follows from this role. |
| AUDITOR | Scoped read, deterministic replay verification and report export; no ownership, correction, cancellation or financial mutation. |
| REPORT_EXPORTER | Generate/access authorized scoped report exports. |

## Review an exception

Open [Exception queue](http://127.0.0.1:3000/queue). Filter decision, branch,
reason/control, owner, age, review/processing state and decimal amount range.
Pagination is server-side, 25 cases per UI page. Open a case, inspect facts,
controls and source evidence, then claim it. The server supplies current ownership
and permitted actions. A stale review or transaction write receives 409; the UI
keeps the form and offers an explicit refresh. A second reviewer cannot overwrite
the accepted action.

Request information records an internal reason and required input. It sends no
email or other message. Field correction uses typed inputs and measured page
evidence where available. Physical correction re-normalizes the source value and
requires verification; structured correction appends a canonical revision. Old
observations, facts and evaluations remain available. Material changes invalidate
old approvals/eligibility and compensate active reservations before fresh screening.

Use the existing authority, duplicate, receipt share and waiver controls. Receipt
share inputs select the actual linked expense item and exact amount/quantity;
technical JSON is optional. A waiver retains the original failed finding, explicit
authority, evidence and expiry in a later evaluation. There is no SET_DECISION
endpoint. After a fresh eligible evaluation, the owner can resolve the superseded
exception. Reports show historical decision plus CURRENT / SUPERSEDED / STALE
current status. Cancellation preserves history and prevents current eligibility.

## Recover a failure

Open [Operations](http://127.0.0.1:3000/operations). Counts, queue ages, ownership,
reason distribution and activity come from persisted data. Failure details show
stage, attempts, safe error code, timestamps and correlation ID. Internal durable
states map as follows:

| Stored state | Operational display |
|---|---|
| QUEUED | QUEUED |
| RUNNING | PROCESSING |
| RETRYABLE | FAILED_RETRYABLE |
| FAILED | DEAD_LETTER |
| SUCCEEDED | COMPLETED |
| CANCELLED | CANCELLED |

Timeout/temporary database or storage failures can retry. Corrupt documents,
unsupported input, authorization failure, missing user input and unconfigured
required assets stay terminal or require input/configuration. Resolve the cause
before manual recovery. An operations administrator supplies a reason and expected
attempt count; at most two extra cycles are allowed. Stale worker leases/generations
cannot publish. Retry never resets counters or duplicates financial admission.

Reconciliation inspects at most 100 metadata objects per category and 1,000 scoped
directory entries. It repairs expired leases, cancelled active reservations and
delayed consumed outbox notifications. Missing completed projections queue a fresh
evaluation with current admission checks. It classifies missing reports, originals,
previews, unfinalized uploads and orphan objects; it preserves them and records
unresolved findings. This bounded local inspector is not a full repository sweep
or backup restore tool. For missing retained artifacts, restore the exact original
from an authorized verified backup; do not fabricate replacement evidence or delete
historical decisions. No cleanup/retention period has been selected.

Operational dependencies distinguish configuration from verified availability.
DATABASE_LEASED_POLLING describes executor design, not a heartbeat. CONFIGURED OCR
or CONFIGURED_UNVERIFIED VLM is not an inference success. Public health contains
only alive/ready or a minimal unavailable response. Required VLM failures preserve
successful preprocessing and cannot produce empty successful extraction or PASS.

## Audit, replay and exports

Case timeline lists retained actions in audit sequence with actor, reason, time,
version and authorized evidence/report links. It paginates independently. POST
`/api/v1/evaluations/{id}/replay` compares retained input/result digests using the
original evaluator/time; it never calls OCR/VLM or changes the original evaluation.

An auditor/exporter can generate JSON, HTML or CSV from the report screen. Download
routes require current authorization, check snapshot integrity, audit access and
send private/no-store responses. CSV prepends an apostrophe to executable-prefix
cells; stored values stay unchanged. The original JSON report view remains the
immutable historical contract; inline HTML additionally labels current status.
PDF export is deferred: Phase 4 adds no separately verified PDF renderer. Browser
printing of HTML is not claimed as generated server-side PDF export.

## Verification

```bash
.venv/bin/pytest -q
.venv/bin/python -m pip check
.venv/bin/alembic -c apps/api/alembic.ini current
.venv/bin/alembic -c apps/api/alembic.ini check
node --test apps/web/checks/development-identity.mjs
npm --prefix apps/web run test:e2e
.venv/bin/python scripts/benchmark/workflow_phase4.py
sha256sum -c docs/source_inputs.sha256
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
```

The benchmark creates and drops only its own disposable test schema. Measurements
are warm local development samples, not SLAs. Test schemas never reset the existing
development database. Keep private artifacts, source uploads and credentials out
of Git. See [Phase-4 exit review](../phase4_exit_review.md) for executed results.
