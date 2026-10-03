# Backup and recovery

## Local executed drill

`.venv/bin/python scripts/release/restore_drill.py` exports a repeatable-read snapshot of the owned loopback PostgreSQL application, writes a private custom-format backup and restores it into a newly created disposable database. It never resets the source. It compares all retained table counts, the report manifest and audit tip; verifies the complete hash-linked audit chain, 61 forced-RLS business tables and non-bypass/unscoped isolation; copies private artifacts and checks original/restored SHA-256. Source symlinks are rejected. Only the drill's generated database is dropped afterward. The private backup/object/result directory remains under ignored `runtime/release` for evidence.

This validates logical local restoration, not machine-loss RTO/RPO or Azure PITR. Source data is synthetic. Restrict backup permissions, encrypt institutional backups through approved infrastructure and never commit/export confidential snapshots. An unscoped application-role query must return no business rows after restoration; table ownership must remain with the non-bypass application role before normal business access. Preserve schema versions and migration history.

## Cloud plan and required exercise

Bicep requires explicit PostgreSQL backup retention/HA and Blob soft-delete/version/container recovery settings. No organization-specific retention period is invented. These protections do not replace a tested recovery procedure or archive policy. Do not configure lifecycle deletion of historical originals/reports/audit without an approved retention policy.

An authorized pilot operator must restore PostgreSQL to a separate private server at a selected recoverable time, restore corresponding Blob versions into an isolated container, reinstall compatible release/configuration, then verify migration head, retained transactions/versions/evaluations/reference pins/reports/ledger, the audit chain, object hashes, RLS/roles and tenant/entity evidence denial. Reconcile missing artifacts/projections without duplicating financial effects. Confirm compatible model/artifact digests. Do not replay changing VLM extraction to reproduce a retained deterministic decision.

Measure actual restore duration and recoverable cutoff on that provisioned configuration. Obtain explicit cutover authority and keep the original system preserved during validation. Test private DNS/TLS/managed identity and application-image rollback in the recovered environment. Cloud restore remains **DEFERRED_EXTERNAL** and blocks AC20.

## Incident boundaries

Database outage: pause eligibility-changing work, inspect minimal readiness/authorized health, restore connectivity or a verified backup; retain idempotency keys and retry after recovery. Storage outage: preserve metadata/original keys, do not mark missing evidence clean, verify remote objects/hash before resuming. Audit failure: required actions roll back atomically; do not bypass audit to approve/cancel.

Worker backlog/stale lease: inspect authorized job state/age/error, correct the dependency, allow bounded lease recovery or permissioned safe retry. Permanent corrupt/unsupported inputs stay terminal/quarantined; request corrected input. Reconcile twice and verify no duplicate evaluations/reservations/releases/reports/audit. See [failure operations](failure-operations.md).
