# Failure and operational response

Use the authorized Operations view and persisted state; public `/health/live` and `/health/ready` expose only alive/ready or a safe failure. Ordinary finance reviewers receive 403 for dependency internals. Logs record route templates/status/duration/correlation, never document text, tokens, raw queries or stack traces.

| Situation | Integrity-preserving response |
|---|---|
| Database unavailable | Stop writes/current eligibility, verify readiness/connectivity/TLS and non-bypass role; retry with the original operation key after recovery. Do not reset schema/data. |
| Local/cloud storage unavailable | Preserve document metadata and hashes, restore private access/object versions, verify bytes and reconcile. A warm local cache never declares the remote object healthy or present. |
| Worker backlog or abandoned lease | Inspect queued age/stage/attempts; restore dependency, let bounded lease recovery run, inspect safe terminal errors. Manual retry needs operational authority, reason and current generation. |
| Corrupt/unsupported/ambiguous document | Quarantine permanent malformed input or request critical corrections. No fabricated zero values or PASS; originals/history remain. |
| Required VLM unavailable | Report dependency/incomplete extraction, preserve completed native/OCR stages. Safe complete native paths may proceed; unresolved visual critical facts require review/input. Do not substitute fixture answers. |
| Required anomaly artifact unavailable | MODEL_UNAVAILABLE/null score and visible configured policy; deterministic HOLD stays HOLD. Restore a compatible approved artifact or explicitly governed mode/rollback. Never silent zero-risk fallback. |
| Reference import invalid/conflicting | Keep draft/errors; correct a new authorized batch/version. Do not overwrite masters/policies or prior snapshot. Wrong policy/master permission remains denied on retry. |
| Stale reviewer/approval write | 409, refresh owner/review/transaction version and inspect the newer work. Do not last-write-wins. Material revisions require new approvals/evaluation and compensation of prior reservations. |
| Failed migration or bad release | Stop deployment, preserve prior state, inspect private logs; deploy a compatible previous image after review. No destructive schema rollback or financial-history deletion. |
| Audit persistence failure | Atomic rollback of required business actions, investigate private persistence using correlation; no audit bypass. Replay uses pinned inputs/rules/time/stored extraction. |
| Missing report/projection/orphan metadata | Run scoped reconciler, inspect classifications, repeat to prove idempotency. Safe repairs append audited operation keys; unresolved findings remain visible. Cloud-wide orphan inventory is not implemented by the local cache inventory. |

The existing `/operations` dashboard exposes actual backlog/failure/workload counts, deterministic next actions and dead-letter inspection. Configured services report CONFIGURED_UNVERIFIED until verified; OCR configuration is not a throughput/quality claim. `risk_model=AVAILABLE` requires integrity-compatible artifact loading. No automated retraining/provisioning/remediation is triggered.

For a pilot, collect CPU Container Apps console telemetry in Log Analytics. Alert on HTTP 5xx, minimal readiness failure, sustained queue age/retry/dead-letter backlog, audit failure, reference freshness and required provider/score unavailability. Thresholds, notification recipients and incident routing require approved operational policy; this delivery invents none. Inspect persisted document/job/extraction/evaluation/review/ledger/monitoring records for quarantine, routing/abstention, PASS/REVIEW/HOLD, stale writes, capacity conflicts and approval invalidations. These are queryable records; not every counter has a dedicated live time-series/alert. Cloud collection and alert delivery are unverified until the pilot smoke exercise.
