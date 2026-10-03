# Phase-5 local intelligence runbook

Scope: synthetic local finance intelligence. No inference runtime, model downloads,
GPU/driver/Docker changes, cloud provisioning, payments or Phase-6 work.

## Setup and modes

Apply existing Alembic migrations through `0008_intelligence_audit`, then build
and run the existing application. Configure the separate fictional identities
with `.venv/bin/python scripts/dev/setup_intelligence_identities.py`; this writes
only ignored private development settings, preserves existing identity roles,
and prints labels rather than tokens. Restart the local API/worker after settings
changes. The demo picker is explicitly loopback/development enabled.

The default new scope has RULES_ONLY, NOT_CONFIGURED and null score. Finance
reviewers see intelligence separately on case detail and can record owned,
version-guarded adjudication with retained evidence. Ordinary submitters do not
get dataset/model administration or other users' feature lineage.

On `/intelligence`, use **Synthetic ML author** to freeze a development dataset,
check the supervised gate, register a statistical candidate and evaluate actual
pipeline diagnostics. Candidate creation never activates. Use **Synthetic ML
governor**, a different actor, to approve and start shadow observation. Submit or
reevaluate actual canonical cases. At least one available retained shadow score
is required before explicit development anomaly activation. This is a workflow
safety minimum, not sufficient real-world validation or production authorization.

The initial model card/threshold are explicitly development statistical policies.
No endpoint accepts a model pickle, executable path, arbitrary URL or raw weights.
The internal artifact is private JSON with server-generated storage key, SHA-256,
algorithm/schema/service/scoring code checks and a dataset/run binding.

## Cutoffs and missing sources

Each new evaluation atomically persists a feature snapshot and separate risk
result, even in rules-only mode. The original enqueue reference snapshot proves
availability; later execution references cannot create past knowledge. Existing
legacy backdated golden cases intentionally have no historical ML input values.

Register already available historical reference pins through the ML-author
`POST /api/v1/intelligence/history` boundary. The server records observation time
now, rejects unactivated sources and forbids supplied knowledge timestamps. Old
reference rows lack a universal knowledge timestamp; business dates alone cannot
be used as retrospective availability. Future evaluations can use registered
facts; old snapshots remain unchanged.

Historical features select the latest canonical version known strictly before
cutoff and exclude current UUID/all revisions. Amounts compare only same currency,
party and employee category. Zero/MAD/cold-start/coverage cases remain explicit.
PIT budget statistics reuse the existing ledger with cutoff-filtered immutable
events. Matching-derived features require all source pins and lifecycle basis to
be provably available at cutoff. Unsafe late/unknown basis stays null. Actual
source observation quality and prior pHash fingerprints require timestamps;
unknown or over-limit coverage does not fabricate metrics/zero similarity.

## Feedback and datasets

Labels are `CLEAN_CONFIRMED`, `DUPLICATE_CONFIRMED`, `POLICY_EXCEPTION`,
`DOCUMENT_CORRECTION_ONLY`, `DISTINCT_CONFIRMED`, `INSUFFICIENT_INFORMATION`.
They describe the pinned facts at the reviewed evaluation; later corrected
facts do not silently relabel the original problem. Each label retains source
evaluation, review action/version, actor/time, taxonomy, reason and evidence.
Supersession appends a label. Open-case labels are provisional; final closed
adjudications are distinct. None immediately changes model weights or finance
decisions. Correction-only/insufficient labels do not become binary exceptions.

ML authors can reproducibly sample PASS cases via a campaign/rate/window. The
existing review queue then supports ownership, inspection and closure, without
altering historical PASS or current eligibility. PASS is never assumed clean.
The sampling period is bounded to 10k evaluations; narrow large windows.

Freeze chronological train/validation/test boundaries that already ended. Related
revisions, shared source/document hashes and duplicate candidates are connected
groups; cross-boundary groups are excluded. Explicit held-out parties must have
no earlier included observations. Manifest IDs/digests, source version, feature
schema, labels, cutoffs, exclusions and splits persist immutably under forced RLS.
Private manifests/rows stay outside Git; only contracts and synthetic examples
may be committed.

The development supervised gate requires authorized representative final labels,
at least 500 cases, at least 50 material exceptions/100 negatives, diversity in
both branches (10 parties each), at least 90 days, document-quality diversity and
both classes in every chronological fold. These are documented development gate
defaults, not organization policy or proof of sufficiency. Current server-owned
data origin is SYNTHETIC_DEVELOPMENT, so it cannot pass regardless of labels added
or dataset size. Offline supervised proposals record SUPERVISED_DEFERRED and no
model. Future authorized representative data needs a separately reviewed intake
and gate; do not flip a client flag to manufacture support.

## Outages, rollback, replay and monitoring

Required unavailable artifact/schema/code produces MODEL_UNAVAILABLE/null score;
otherwise deterministic PASS becomes REVIEW. Existing HOLD stays HOLD. Cold or
inapplicable history remains explicit and requests review in active anomaly mode.
Shadow scores never change decisions. Explanations are statistical measurements;
SHAP remains NOT_APPLICABLE and unavailable factors are never invented.

Governors explicitly append deployments/thresholds with expected configuration
version. Rollback selects an earlier retained deployment; rules-only disablement
is another explicit audited option. Retained evaluations/scores/reports remain
immutable, and current eligibility becomes stale until fresh screening. Never
repair an outage by substituting score zero or changing a historical PASS.

The existing authorized audit replay consumes stored canonical/rule context and
feature snapshot; it verifies retained digests and compatible artifact/code and
reproduces the combiner. It does not rerun VLM/OCR or collect current history.
Unavailable historical scoring code/artifact is explicit replay failure, not a
false successful match.

Monitoring records bounded frozen periods: feature missingness/min/median/max,
amount distribution separated by currency, vendor/employee cardinalities,
category mix, score distribution, cold starts, delayed final-label coverage and
clean adjudications of anomaly escalations. Optional baseline dataset comparison
flags absolute missingness changes >=0.20 as development diagnostics. Missing
baselines/labels/metrics remain null/unavailable. Drift requests evaluation;
it never auto-trains. Retraining is an offline manually governed run, followed
by separate independent evaluation/approval/shadow/activation. There is no
online learning, automatic monthly schedule or production classifier.

## Verification

Run `.venv/bin/pytest -q apps/api/tests`; use the existing live-backend browser
suite with `npm --prefix apps/web run test:e2e`. New phase tests cover cutoff/
current/version/currency leakage, null/zero/MAD handling, grouping, sampling,
authorization, independent governance, shadow/activation/rollback, artifacts,
required outages, feedback, replay and atomic audit rollback. TypeScript,
production build, Alembic drift/fresh upgrade and source preservation remain gates.

`.venv/bin/python scripts/benchmark/intelligence_phase5.py` creates/drops only
its own temporary `ap_phase1_test` schema, inserts 10k synthetic canonical facts,
and measures PIT query/build/scoring plus a real query plan. The ignored report
contains actual local measurements, no supervised accuracy/calibration metrics.
Do not reset meaningful databases or delete retained source/audit/model history.
