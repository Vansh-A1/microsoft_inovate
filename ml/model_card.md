# Transparent statistical anomaly policy

- Algorithm: `ROBUST_STATISTICAL`; version `anomaly-p5-v1`.
- Use: request finance review of unusual submitted canonical amounts, separate
  from mandatory finance controls. Synthetic local development only.
- Target: statistical deviation, **not** fraud or exception probability.
- Training: no fitted classifier. A registered JSON artifact pins the algorithm,
  feature schema/code, service/scoring code, dataset and offline run metadata.
- Supervised gate: `SUPERVISED_TRAINING_NOT_JUSTIFIED`; representative adjudicated
  labels are absent. Synthetic metrics cannot authorize production promotion.
- SHAP/calibration: not applicable; no classifier/margin/probability is delivered.

For at least five prior submitted same-currency vendor observations, or prior
employee/category observations, compute median and MAD using Decimal. The amount
ratio is current amount / prior cohort median. Robust deviation is absolute amount
minus median, divided by 1.4826 × MAD. Zero MAD leaves that feature null; the ratio
can still be usable. Empty/incomplete/too-small history has no anomaly score.

The available score is the maximum of:

1. `min(100, 20 × abs(log2(amount ratio)))`;
2. `min(100, 15 × robust absolute deviation)` when MAD is positive.

This is an intentionally defined **ANOMALY_SCORE**, 0–100, higher means more
statistically unusual. It is not a calibrated probability or learned importance.
Factors display actual measured ratios/deviations and lineage, with no causal claim.
The score is reproducible from retained feature values. A verified unavailable
artifact/schema/code records null score and an explicit diagnostic; no risk-zero
fallback or invented explanation exists.

Default development review threshold is 60, corresponding to an eightfold ratio
deviation or four robust scales. It is a versioned heuristic, not a threshold
tuned against test outcomes, a company policy or a calibrated review-capacity claim.
Governance records every deployment threshold/reason. Representative validation
is required to establish useful review capacity/precision/recall.

`RULES_ONLY` produces `NOT_CONFIGURED` and null score. `SHADOW` stores actual
statistical scores without changing decisions. `RULES_PLUS_ANOMALY` may escalate
otherwise deterministic PASS to REVIEW. Required unavailable/inapplicable scoring
also requests REVIEW under this recorded fail-closed development policy. Existing
REVIEW/HOLD remains unchanged, regardless of score. ML alone never creates HOLD.
`RULES_PLUS_MODEL` without a compatible classifier records MODEL_UNAVAILABLE;
unsupported supervised artifacts cannot be promoted through the data gate.

Limitations include synthetic coverage, small/cohort selection, unverified
representativeness, submitted facts rather than inferred clean outcomes, no FX,
no production generalization evidence and missing features where cutoff-safe
reference/ledger/source evidence is unavailable. Current scoring uses amount
statistics only. Other versioned features support transparent inspection and
future governed evaluation; availability does not imply trained predictive value.

Candidate registration never activates. Independent ML governance approval,
explicit shadow deployment and actual available shadow output precede active
anomaly review. Rollback appends another configuration; historical scores and
decisions retain their original versions. Deployment changes make current
eligibility stale until reevaluation. A retired/rejected/incompatible artifact
requires resolution before reuse; it is never silently substituted.
