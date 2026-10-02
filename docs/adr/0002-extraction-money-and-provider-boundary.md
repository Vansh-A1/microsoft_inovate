# ADR-0002 — Exact money text at the provider boundary

- Date: 2026-10-03 (research began 2026-10-02).
- Status: Accepted boundary decision; real provider implementation deferred to approved P0-04C.
- Scope: P0-04B research; no domain/application/dependency changes.

## Context

The existing [Money contract](../../apps/api/app/domain/money.py) rejects floats and requires exact monetary representation. The existing [extraction contract](../../apps/api/app/domain/extraction.py) preserves raw observed text and optional unverified candidate text separately. TypeLLM 0.5.1's numeric decoder calls `float(text)` for `number`; it does not establish an exact Decimal output boundary. This was verified by reading the [pinned runtime source](https://github.com/TypeLLM/TypeLLM/blob/0c34f00251f850b4cd1b8060f24dd7066522fb5d/typellm/runtime.py), accessed 2026-10-02. No provider code was executed.

## Decision

Ask for printed amounts, prices, taxes, discounts, rates and financial quantities as strings. Preserve observed separators, signs, currency symbols, scale and uncertainty. The proposed adapter will validate strings and explicit observation states before constructing the existing immutable result. It will not calculate finance outcomes or turn extracted numbers into Money.

Only a later approved trusted normalizer may resolve an evidenced locale/currency convention and construct Decimal from validated decimal text, followed by Money. Ambiguous conventions stay ambiguous. Prohibit authoritative `number`/float fields, `Decimal(float_value)`, and converting a float to text while claiming exact source recovery. Diagnostic numeric outputs must remain outside financial facts and cannot be used to choose a monetary candidate. No domain float validation is weakened.

Retain the provider-independent Protocol and flat rows. Null/skipped outputs must not erase explicit MISSING/ILLEGIBLE/AMBIGUOUS/NOT_APPLICABLE states. Return no private reasoning, invented confidence or coordinates; unavailable boxes stay None. Runtime completion remains separate from finance decisions.

## Consequences and verification gate

Existing contracts, 488 tests and fixture data remain unchanged. The future adapter must prove string-only money, exact scale/sign preservation, abstention, rejection of float responses and no hidden normalization. Existing harness raw/state results remain reportable; combined candidate agreement may fail until a separately approved trusted normalizer exists. Do not copy benchmark candidates into provider responses to improve results. See the [runtime plan](../typellm_spike_plan.md) for the conditional environment, mappings and failure gates. This decision selects a boundary, not a verified runtime or production provider.
