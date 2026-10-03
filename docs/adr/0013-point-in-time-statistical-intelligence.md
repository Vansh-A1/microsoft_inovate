# ADR-0013 — Point-in-time statistical intelligence and supervised-data gate

Accepted under the continuous P5-01–P5-05 approval, 2026-10-03.

The inspected 200 structured scale inputs are synthetic vendor invoices without
adjudicated labels. The 10k generated history is a disposable performance corpus.
The retained review actions are corrections/requests/resolutions, not independently
adjudicated taxonomy labels. Representative training permission/data are absent.
Supervised training is NOT JUSTIFIED; no classifier, probability, calibration,
held-out generalization or SHAP will be fabricated. Isolation Forest also requires
representative history, so use an explicit robust statistical anomaly baseline.

Reuse canonical versions, evaluations, jobs, scope locks, private storage and audit.
Append feature, score, feedback, dataset, training and registry facts with forced
RLS. Feature code/schema and source manifests bind each cutoff. Histories are prior
submitted canonical facts, not inferred clean/paid cases. Select the latest version
known before cutoff, exclude the current UUID/all its revisions, and compare only
same-currency cohorts. Imported references lack a universal ingestion timestamp;
record conservative server-observed availability rather than backdating knowledge.
Missing/zero-MAD/incomplete history stays explicit. IDs are lineage/join/group keys,
not predictive features; personal attributes, approval/label/settlement outcomes
and future correction/disposition information are excluded.

RULES_ONLY remains the default compatibility path with NOT_CONFIGURED/null score.
Explicit governed SHADOW scores without changing routing. RULES_PLUS_ANOMALY may
escalate deterministic PASS to REVIEW; required unavailable scoring cannot become
zero risk. No model alone creates HOLD or clears deterministic HOLD/REVIEW.
Thresholds are versioned development policies, not validated probability cutoffs.
Retained scores and reports bind original artifacts/configuration and never change
on promotion/rollback. A changed deployment invalidates current eligibility until
reevaluation, without mutating historical decisions.

Feedback is a separate evidenced adjudication, versioned by supersession, not an
automatic correction label or online learning update. PASS sampling uses a stable
hash/seed and retains selection evidence. Dataset manifests use frozen chronological
periods and connected document/transaction/duplicate groups; groups spanning split
boundaries are excluded. Synthetic-only datasets fail the supervised-data gate
regardless of row count. Offline training proposals remain governed and deferred.
Dataset/registry permissions are separate from finance actions. Explicit approval,
shadow evidence, activation and rollback are audited; training cannot activate.
Monitoring records missingness/distributions/cold starts/delayed feedback and raises
evaluation requests, without automatic retraining. No Phase-6 infrastructure work.
