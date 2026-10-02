# ADR-0005 — Durable jobs and independent inference workers

- Date: 2026-10-03.
- Status: Accepted Phase-0 design; no queue/database/worker created.
- Basis: specification sections 3.3, 15, 17, 19 and P0-06.

## Decision

Start with PostgreSQL durable jobs plus a transactional outbox. Commit accepted metadata, scoped idempotency record and work intent in one database transaction. External object writes require staged/finalized storage and reconciliation; they cannot share that transaction. A later Azure Service Bus transport remains behind an adapter and does not replace business idempotency.

Jobs use tenant/entity, document or transaction revision, stage name and stage implementation version as an idempotency boundary. At-least-once delivery is expected. Workers claim/renew expiring leases, use bounded retry/backoff/jitter and explicit dead-letter/permanent-failure states. Retries converge on one logical committed effect; no claim of exactly-once message delivery. Audit commitment and eligibility-changing business effects must be atomic as required by the specification.

Upload acceptance returns a job/resource status promptly. UI polls or subscribes to authorized progress; it does not wait on a browser-held model request. CPU finance workers share the domain implementation with API services. Inference workers and resident GPU servers scale independently of API/frontend/rules/PostgreSQL. Queue events carry minimal identifiers/versions/correlation, not raw documents or bank details; workers fetch private artifacts under scoped access.

Before publishing an attempt result, recheck cancellation, document/version freshness, job ownership/lease and scope. Preserve attempt history; a late or superseded result cannot overwrite a newer correction/review. Provider-unavailable/timeout/malformed/OOM states remain incomplete; no empty successful extraction, zero risk, implicit fixture substitution or finance PASS. Circuit breakers and per-tenant quotas prevent an inference outage from exhausting the control plane.

## Consequences and alternatives

Reject in-memory browser jobs and a model load per invoice. No PostgreSQL schema, lease algorithm, retry scheduler, outbox or worker is implemented here. Phase 1 must verify transactionality, repeated keys, crash/retry, stale/cancelled results and authorized status reads; financial reservation/finalization concurrency remains later required work. See [inference architecture](../inference_architecture.md).
