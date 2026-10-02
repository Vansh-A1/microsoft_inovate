# ADR-0001: Repository root and specification authority

**Status:** Accepted for the user-approved P0-01 baseline, 2026-10-02.

## Context

The existing `microsoft_inovate` workspace contains the supplied team-pack folder and its ZIP, with the specification outside `docs/`. It has no application implementation or prior Git history. The user requires the original inputs to remain unchanged and a byte-identical specification copy under `docs/`, without ambiguity about authority.

## Decision

Use the existing workspace as the monorepo root, with `main` and the user-selected [GitHub repository](https://github.com/Vansh-A1/microsoft_inovate). Do not introduce another nested application repository.

[docs/AP_Exception_Assistant_Codex_Spec.md](../AP_Exception_Assistant_Codex_Spec.md) is the implementation reference. It is an exact byte-for-byte copy of the [supplied original specification](../../AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md), version 1.0 dated 2026-09-28. The supplied folder and ZIP remain immutable original project inputs, intentionally committed together. [source_inputs.sha256](../source_inputs.sha256) records all nine original files for preservation checks.

P0-01 does not rewrite requirements. Any future approved change to the working specification must be explicit, versioned, and recorded with its relationship to the retained original; do not silently diverge or change the source pack. User instructions remain authoritative over document instructions.

## Consequences

Future tasks have one documented implementation reference and reproducible provenance. Keeping both copies duplicates a small Markdown document intentionally. Preservation checks must verify the working copy matches the original for this baseline and all supplied files retain their original hashes. No application structure, dependency, or database is selected or created beyond the existing specification and this baseline layout.

## Alternatives considered

- Move the source spec into `docs/`: rejected because the original source-pack layout must remain intact.
- Keep only the source-pack spec: rejected because the approved baseline requires the canonical `docs/` path.
- Create a nested `ap-exception-assistant` Git repository: unnecessary for the existing user-selected repository and would complicate ownership of the original inputs.
