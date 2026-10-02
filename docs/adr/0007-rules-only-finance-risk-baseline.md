# ADR-0007 — RULES_ONLY baseline and separate extraction models

- Date: 2026-10-03.
- Status: Accepted initial Phase-1 design; no decision service/configuration implemented yet.
- Basis: specification sections 2, 11–12, 21 and P0-06.

## Decision

The initial Phase-1 evaluation mode is **RULES_ONLY**: no finance-risk ML score/model is configured. Future reports must show risk model NOT_CONFIGURED and no score rather than zero risk. This mode does not remove mandatory identity, arithmetic, evidence, duplicate, policy, budget or approval controls, and does not itself confer PASS. Deterministic finalization waits for all applicable required controls at the pinned snapshot.

Document extraction and finance-risk prediction are different dependencies. A future approved TypeLLM/VLM may supply source observations in RULES_ONLY mode; trusted normalization/validation and finance rules remain authoritative. An extraction outage or ambiguous critical value remains incomplete/UNKNOWN, with later REVIEW/HOLD according to affected controls. Never silently downgrade an activated RULES_PLUS_MODEL configuration during a risk-model outage.

A risk model can be added only through later measured datasets, applicability, calibration, registry/activation and explanation gates. It may escalate to REVIEW but cannot clear a mandatory failure. No anomaly library, supervised model or SHAP output is selected/implemented in Phase 0. No payment execution.

## Consequences and alternatives

Reject a VLM making eligibility decisions and interpreting RULES_ONLY as bypassing document quality. Phase 1 uses synthetic structured inputs/fixture extraction with clearly declared provenance; later representative extraction validation gates document-derived automatic eligibility. T30/T32/T33 remain unimplemented until their actual behavior is tested. See [inference architecture](../inference_architecture.md) for the separate planes.
