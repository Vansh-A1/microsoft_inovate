# ADR-0009 — Bounded Phase-1 persistence and local runtime

Status: accepted under the user's continuous P1-01–P1-06 approval, 2026-10-03.

The executable slice uses FastAPI/Pydantic, SQLAlchemy/Alembic and real PostgreSQL. Python dependencies live in `.venv`; official Node LTS and signed Ubuntu PostgreSQL packages are extracted into ignored project directories. No sudo, Docker access, system installation or GPU setup is required. SQLite is explicitly rejected for the application; an opt-in test fallback exists but the integration suite runs PostgreSQL.

The schema separates immutable canonical versions, snapshots, evaluations, rule results, evidence, reports and audit records from mutable case/job/import projections. A bounded reference catalog retains original synthetic records and flattened PO lines, GRN lines, ledger entries and allocations, with scoped relational links and snapshot membership. This is a Phase-1 catalog, not an external master-import platform. Its source is the original P0 fixture corpus. No new public reference-write or approval-write surface is exposed.

All business tables use tenant/entity keys, scope-qualified foreign keys and forced PostgreSQL row-level policies. A non-superuser, non-BYPASSRLS application role binds transaction-local server identity. PostgreSQL triggers protect immutable facts even from bulk SQL. This does not defend against a database administrator.

A private, randomly generated development bearer token maps to server-owned scope and roles. The loopback Next server injects it into API requests; it is not a browser token or production SSO. Request schemas reject scope, approvals and decision authority. The trusted seed command imports genuine synthetic approval actions bound to the canonical version. New ordinary submissions cannot self-approve.

Scope advisory locks guard duplicate admission, evaluation finalization and minimal budget/PO/GRN reservations. Existing PO commitment coverage is counted once. Historical searches use scoped indexed exact predicates and explicit result limits. A separate immutable evaluation-input record retains the complete deterministic context, including current reservations and relevant historical versions. These basic guards do not implement the full Phase-3 accounting/allocation lifecycle.

The worker polls durable jobs, consumes the corresponding outbox notification, acquires an expiring lease, retries with bounded backoff and commits effects and audit atomically. Outbox delivery here means local database-worker consumption; no external broker is claimed. Lease ownership and current canonical version are checked before publishing. Rule and policy versions are explicit. Prototype evaluations produced during development are retained and superseded, never patched into successful outcomes.

Deterministic reports escape every value and include every required control. Synthetic source JSON has no images, pages or boxes. CSV/XLSX intake has one text `transaction_json` column, bounded rows/bytes/expansion, formula rejection, private server-generated object keys and retained invalid rows. Files may remain as private orphan objects after a database rollback; automatic storage reconciliation is deferred. There are no external URLs or client-chosen paths.

Reference snapshots are bounded master catalogs; finalization extends the snapshot with the relevant immutable history/allocation records. Exhausted limits are explicit failures, never an empty history or unlimited budget. Rule arithmetic uses the P0 Decimal/Money and evidence contracts with a private precision context, explicit INR rounding and tolerances. Credit/refund, foreign-currency and unsupported contexts abstain; mandatory failures retain HOLD precedence.

Sources for the runtime choices: [Node releases](https://nodejs.org/en/download), [Next installation](https://nextjs.org/docs/app/getting-started/installation), [SQLAlchemy](https://docs.sqlalchemy.org/en/20/intro.html), [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html), [PostgreSQL initdb](https://www.postgresql.org/docs/16/app-initdb.html). Exact installed pins and commands are recorded in the runbook and lockfiles.
