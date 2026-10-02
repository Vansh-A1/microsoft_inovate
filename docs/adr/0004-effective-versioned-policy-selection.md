# ADR-0004 — Effective, versioned policy selection

- Date: 2026-10-03.
- Status: Accepted Phase-0 design; resolver/rules remain unimplemented.
- Basis: specification sections 5, 7, 9, 12 and P0-06.

## Decision

Resolve exactly one authorized, versioned policy using tenant/entity, relevant transaction/expense date, category, currency and applicable grade/location/trip dimensions. Development fixtures use half-open effective intervals. Explicit, versioned precedence may resolve an overlap only when approved; never choose the newest, cheapest or most permissive policy by convenience. Missing, stale, unsupported or multiple applicable policies stay explicit UNKNOWN/ambiguity/error, with candidate IDs, matched dimensions and source versions.

An evaluation pins the policy/reference snapshot, normalization/rule versions and evaluation time. Current mandatory restrictions checked at release/finalization may differ from transaction-date policy; record both rather than rewriting history. Changed policies or facts create a new evaluation and invalidate affected eligibility/approvals through future version checks. Do not read changing live references halfway through a pinned evaluation.

Required controls cannot PASS because no policy matched. NOT_APPLICABLE requires cited applicability, and waivers require separate authorized scoped evidence. Finance routing follows the deterministic decision policy later; extraction uncertainty and policy ambiguity are not the same state.

## Consequences and alternatives

Reject permissive fallback and implicit overlapping-policy priority. Existing P0-03 references and malformed-overlap tests validate fixture structure/expectations only; no production policy resolver or decision combiner exists. Phase 1 and later matching work must test absent/overlapping/stale policies, effective boundaries, explicit precedence and reproducible snapshots. [Coverage](../test_coverage.md) remains business behavior NOT IMPLEMENTED.
