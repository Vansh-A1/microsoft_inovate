# ADR-0012 — Review ownership and retained operational recovery

Status: accepted under direct P4-01–P4-04 approval, 2026-10-03.

Extend the existing review_cases projection with scoped owner, row version and
update time. OPEN means unassigned; ASSIGNED and AWAITING_INFORMATION retain
ownership. Reassessment supersedes the old case, preserves its owner in a new
exception case, and leaves the previous case available to close after current
controls become eligible. Immutable review_actions preserve who changed what,
why, evidence and the accepted versions. A write requires both expected review
and transaction versions under the existing scope lock. Legacy correction,
resolution, attachment, waiver and user reevaluation routes obey claimed ownership.
Approval actors retain their independent authority workflow.

Historical Evaluation, EvaluationInput, RuleResultRow and Report remain immutable.
Current eligibility is a separate read projection over latest facts/evaluation,
processing/cancellation, reference and policy freshness, waiver expiry and active
allocation lifecycle. A historical PASS does not authorize consumption after its
eligibility becomes stale. Cancellation retains all facts, releases only RESERVED
capacity with compensating events, and rejects consumed capacity until an explicit
authorized reversal. Repeated transitions do not append a second effect.

Reuse durable jobs and lease/generation guards. Keep existing internal states for
compatibility; map them into clear operational lifecycle labels. Record safe error
codes, retry classification, first/last failure and bounded manual recovery count.
Transient failures use at most three attempts per execution cycle, with bounded
exponential delay and stable jitter. An OPERATIONS_ADMIN may grant at most two
additional three-attempt cycles; attempts never reset. Permanent inputs and
superseded jobs cannot be manually retried.

Immutable operation_records hold replay verification, safe reconciliation and
authorized export snapshots. Their scoped operation keys prevent duplicate repair
records. Reconciliation queues fresh admission for a missing completed projection;
it cannot resurrect an old PASS. Missing originals/reports/pages and unfinalized
uploads remain visible, unresolved and retained. The local directory scan and
metadata inspection are bounded. No organization retention policy is invented.

Replay uses the retained encoded context, exact original evaluator, original fixed
time and stored extraction facts. Compare result digests, including all rule
results, completeness, decision and eligibility. Replay does not rerun extraction.
Finance/auditor readers may inspect; finance writes, approval authority, ledger,
review reassignment, operations recovery and report export use distinct permissions.
Exports are private authorized snapshots, with access audit and CSV escaping.

The public liveness/readiness responses remain minimal. Operational configuration
details require scoped authorization. Development uses separately configured
synthetic operations, auditor and review-manager identities; existing identities
are not widened. Real enterprise authentication, VLM execution, malware scanning,
production monitoring/retention and backup restoration remain separate inputs.
