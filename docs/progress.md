# Implementation progress

## Current priority override — real local document inference

The 2026-10-04 direct request authorizes an isolated current-driver VLM experiment
and actual application integration, superseding earlier inference deferrals for
this task. Phases 0–6 were already delivered locally; this checkpoint changes the
extraction front half and preserves their finance architecture. No new phase,
host change, cloud provisioning or Git publication/authentication task is started.

Actual Qwen2.5-VL-3B BF16, pinned revision
`66285546d2b821cf421d4f5eb2576359d3770cd3`, now runs with SGLang 0.4.6.post5 /
PyTorch 2.6.0+cu124 on the unchanged 550.120 driver. Actual TypeLLM 0.5.1 lives
in a separate CPU client environment. Real pixels reach the existing adapter,
persisted extraction pipeline, Decimal normalizer, source corrections and finance
engine. Final full backend: **803 passed / 6 opt-in skipped**, 2375.28 s, exit 0.
The final affected CPU batch passes **200**, 2.30 s, covering five cases added
after full-run collection; all **808 current ordinary cases** are covered by
these overlapping runs. The separate actual GPU suite passes **6**, 241.19 s.
Final browser suite passes **37**, 2.8 minutes; TypeScript/build/drift/contracts,
dependency integrity, source manifests and secret scanning pass. Counts are
separate executed runs, not an invented 814-case ordinary full-suite result.

Changes include an authenticated CPU gateway, legacy transport compatibility,
measured source-mapped row crops, mapping-coverage escalation, visual row inventory
independent of partial OCR, retained provider conflicts and actual admin health.
`document-normalizer-v2` routes printed visual row amounts through the existing
Decimal/currency validator while retaining earlier trace versions.
The scan-to-finance test preserves raw observations and explicitly corrects a
compact-table error; finance returns HOLD for missing approvals. The supplied
table invoice maps its eight checked header literals and 12 core row values, but
currency/date/fee uncertainty still requires input. Northstar's exact source was
not found. Five source variants and crop measurements are a smoke, not universal
accuracy. The model's Qwen research license is a production-use gate.

A browser regression exposed a delayed reference-list response overwriting newer
staged work. A small generation guard and a real delayed-response regression test
repair it. Identity test navigation and provider-status assertions were corrected;
no finance authorization or decision behavior was weakened.

The [acceptance record](real_vlm_acceptance.md), [ADR-0015](adr/0015-current-driver-compatible-real-vlm.md),
[runbook](runbooks/local-inference.md), compatibility/architecture/assumptions,
dictionary, coverage and release matrix describe actual behavior and limits.
Source originals, hashes, private outputs, keys, caches and model artifacts remain
preserved/ignored. No GPU driver, host CUDA, system Python, GPU/Docker configuration
or administrator package was changed, and no sudo was used. Earlier sections below
are retained historical checkpoints, superseded by later approved phase/override work.

### Local delivery checkpoint

Implementation commit `4d69cf0` contains the real runtime/gateway, provider boundary,
coverage routing, uncertainty/normalization guards, benchmark and opt-in tests.
A separate reviewed UI/documentation commit records actual provider health, the
browser response-race repair, acceptance evidence and reproducible run commands.
Original source-pack/fixture manifests remain verified and unchanged. Source scan
reports 310 text files with no configured credential patterns/private paths;
Gitleaks 8.30.1 finds zero source secrets and passes its redacted positive probe.
Staged whitespace checks pass. No new migrations or finance-rule changes occurred.

Actual stop/start/health and post-restart image inference were exercised. Final
provider health is AVAILABLE, application readiness is HTTP 200, and Finance
Workspace responds HTTP 200. Working inference and app artifacts are retained.
No push or authentication repair is attempted. Next task: **none; STOP after
delivering the verified local extraction checkpoint.** Production hosting/license,
representative quality, supervised labels and cloud inputs remain separate gates.

## Phase 5 complete locally — rules plus anomaly; stop before Phase 6

Direct approval authorized P5-01–P5-05 continuously and the specification's honest
rules/anomaly-only exit when representative supervised data is absent. The full
Python suite passed **753 tests** (exit 0); after the final five cases were added,
the stable 38-test intelligence batch and two actual-source cases passed (exit 0).
All **758 currently collected backend cases** are covered by those executed runs;
758 is not claimed as the count of one full-suite invocation. The full real-backend
browser suite passed **31 tests**, and the final four changed intelligence flows
passed again. TypeScript/build/drift/contracts/source preservation also passed.

Twenty point-in-time features, transparent statistical factors, evidenced feedback,
PASS audit sampling, grouped chronological manifests, offline runs/data gate,
private registry/shadow/activation/rollback, monitoring and separate reports/UI are
implemented. Entry inventory returned exit 0: 200 synthetic vendor inputs, no
adjudicated training labels, 129 transactions/142 versions, 218 evaluations,
174 reviews and 24 actions. Five history references and the generated 10k corpus
are synthetic. No authorized representative labels exist:
**SUPERVISED_TRAINING_NOT_JUSTIFIED**. No classifier, probability, calibration or
SHAP was fabricated. P5-03/P5-04's supervised behavior is explicitly deferred.

The local synthetic scope is explicitly **RULES_PLUS_ANOMALY / AVAILABLE**,
configuration 39, after independent approval and actual shadow scores. An actual
fresh evaluation produced score 91.214299 / ANOMALY_ESCALATION / REVIEW with no
mandatory rule escalation. Default new scopes retain RULES_ONLY/null score;
mandatory HOLD remains authoritative. See [exit review](phase5_exit_review.md),
[runbook](runbooks/phase5-local.md) and [model card](../ml/model_card.md).
Publication is authentication-blocked after the single ordinary main push; all verified work is retained in clean local commits. No Phase-6 work began.

## Phase 4 complete locally — stop before Phase 5

Direct approval authorized P4-01–P4-04 continuously. All four tasks and the local exit gate are complete: existing review ownership/optimistic conflicts, retained correction/resolution and eligibility lifecycle, safe recovery/reconciliation/replay, accessible operations/timeline/private exports. The final full gate passed 720 Python tests and 27 actual-backend browser tests, with TypeScript/build/migration/integrity checks passing. Publication is recorded separately below. No Phase-5 ML or inference infrastructure work began.

## Project status

- Session date: 2026-10-02–04 (Asia/Kolkata).
- Current phase: **PHASES 0–6 COMPLETE LOCALLY** with their recorded external cloud/data gates.
- Current task: **PRIORITY OVERRIDE COMPLETE — real current-machine VLM extraction, application integration and final regression verified; stop after local commits.**
- P0-01: **COMPLETE LOCALLY**; the single consolidated phase push failed authentication; remote publication remains blocked.
- P0-02: **COMPLETE**; tested Money/currency, states and evidence foundation.
- P0-03: **COMPLETE**; reproducible synthetic references and independent golden expectations.
- P0-04: **CLOSED WITH EXTERNAL RUNTIME DEFERRAL**; fixture/contracts/research verified, real inference not executed.
- P0-05: **COMPLETE FEASIBILITY CONSOLIDATION**; final compatibility matrix, research pins and honest unverified/blocked/deferred limitations.
- P0-06: **COMPLETE DESIGN DECISIONS**; identity, effective policy, durable jobs, private storage, RULES_ONLY risk and optimized shared inference.
- Real inference runtime: **OPERATIONAL FOR TESTED LOCAL CASES** under ADR-0015; the earlier CUDA-13 and Docker observations remain historical blockers for those paths.
- Development extraction: **ACTUAL NATIVE_TEXT / LOCAL_OCR / ENTERPRISE_VLM** plus preserved FIXTURE replay; production shared serving/license/representative quality remain separate gates.
- Phase 1: **COMPLETE LOCALLY**; preserved as the Phase-2 finance baseline.

The [Phase-0 exit review](phase0_exit_review.md) preserves the explicit runtime qualification. The [Phase-1 exit review](phase1_exit_review.md) records the working product and full-release limits. [T01–T42 coverage](test_coverage.md) is 39 implemented/passing, 1 partial and 2 deferred by the supervised-data gate. Historical work records below describe the approval/status at each checkpoint; this current disposition supersedes their prior stop/parent-incomplete statements. No original record or specification is rewritten to suggest a passed real spike.

## Phase checklist

- [x] Phase 0 — Contracts and feasibility (local exit criteria satisfied; real runtime explicitly deferred, publication separately reported).
- [x] Phase 1 — Rules-first vertical slice for both branches (local exit passed; Git publication separately recorded).
- [x] Phase 2 — Real document ingestion and extraction (local exit passed; shared enterprise VLM execution explicitly deferred).
- [x] Phase 3 — Complete finance matching and controls (local exit verified; authentication-blocked publication).
- [x] Phase 4 — Human workflow and operational reliability (local exit passed; publication separately recorded).
- [x] Phase 5 — Measured intelligence/explanations: explicit rules/anomaly-only exit; supervised model and SHAP deferred for representative-data gate.
- [x] Phase 6 — Local deployment/pilot handoff complete; cloud provisioning deferred for external inputs, as recorded in the Phase-6 exit review.

### Phase 0 tasks

- [x] P0-01 — Repository/documentation baseline complete locally; publication separate external gate.
- [x] P0-02 — Domain glossary, explicit states, exact Money/currency and evidence contracts.
- [x] P0-03 — Reproducible synthetic references and independent golden expectations.
- [x] P0-04 — Replaceable extraction contract, fixture adapter/harness, research and observed prerequisite gate; real image execution deferred by explicit approval.
- [x] P0-05 — Compatibility/null/row/evidence/latency/license/hardware findings and research pins, with working fixture fallback and external prerequisites recorded.
- [x] P0-06 — Accepted identity, policy, durable-job/private-storage, RULES_ONLY and optimized enterprise architecture decisions.

### P0-04 execution detail and explicit deferrals

- P0-04A: COMPLETE, locally tested extraction contract/fixture/harness; no visual artifacts.
- P0-04B: COMPLETE research; upstream evidence is not local provider execution.
- P0-04C1: prerequisite gate COMPLETE; runtime smoke NOT RUN due to observed blockers.
- P0-04C / P0-04C2: real image smoke and full ten-case real-provider benchmark **DEFERRED — REQUIRES SUITABLE INFERENCE HOST**. Real image quality, latency and VRAM unavailable.
- Quantization, text/visual/model-cascade and actual crop benchmarks: later suitable-host work, not completed measurements or remaining required Phase-0 local tasks.

## P0-01 work record

### Scope

Establish this existing workspace as the repository root; create only the documentation foundation, exact specification copy, ignore rules, and provenance records. Preserve the supplied folder and ZIP. Initialize `main`, configure the requested GitHub remote, verify locally, commit, publish the authorized initial baseline, and verify its remote contents.

### Files

- Root: `README.md`, `AGENTS.md`, `.gitignore`.
- Documentation: exact spec copy, this progress tracker, assumptions, baseline glossary, T01–T42 coverage, original-input checksum manifest.
- Decision record: [ADR-0001](adr/0001-repository-and-specification-authority.md) records repository root and specification authority.
- All nine supplied source files are intentionally retained for version control without changes.

### Reconnaissance already executed

| Command/check | Exit/result |
|---|---|
| `rg --files --hidden` with generated-directory exclusions | Exit 0; eight Markdown source documents and one ZIP; no code or project manifests. |
| `git status --short --branch` before initialization | Exit 128; workspace was not a Git repository. |
| `python3 --version` | Exit 0; Python 3.13.11. |
| `git --version` | Exit 0; Git 2.43.0. |
| Python runtime/package inventory | Exit 0; available Python tools and absent prerequisites recorded in assumptions. |
| `docker --version` | Exit 0; Docker 29.1.3. |
| `docker compose version` | Exit 1; `docker: unknown command: docker compose`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --collect-only -q -p no:cacheprovider` | Exit 5; no tests collected. This is not a passing application test suite. |
| `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT` | Exit 0; existing identity available; no identity/credentials changed. |
| `GIT_TERMINAL_PROMPT=0 git ls-remote https://github.com/Vansh-A1/microsoft_inovate.git` | Exit 0; no published refs before initialization. Push permission not established by this read. |
| `sha256sum` over supplied folder files and ZIP | Exit 0; nine pre-change hashes captured. |

### Baseline verification

| Command/check | Exit/result |
|---|---|
| `git init --initial-branch=main` | Exit 0; repository initialized on `main`. |
| `git remote add origin https://github.com/Vansh-A1/microsoft_inovate.git` | Exit 0; requested remote configured. |
| `python3` inline standard-library documentation audit (`python3 <<'PY'`) | Exit 0; all 10 new baseline files and ADR directory present; 25 local links across 16 Markdown files resolve, including one heading anchor. |
| Same audit: coverage comparison against spec section 22.2 | Exit 0; all 42 scenarios/expectations match exactly; 42 NOT IMPLEMENTED, no automated test paths. |
| Same audit: `git check-ignore --no-index --stdin` | Exit 0; 44 generated/sensitive example paths ignored and 28 source/template/example paths trackable, including `.env.example` and synthetic PDF/image/JSON/CSV fixtures. No example files were created. |
| Same audit: file-set and credential-signature inspection | Exit 0; exactly 19 intended files (10 baseline files plus nine original inputs), no application or dependency files, and no common private-key/AWS/GitHub token signatures in Markdown. This limited scan is not a security certification. |
| `sha256sum -c docs/source_inputs.sha256` | Exit 0; all nine original files, including ZIP, report OK. |
| `cmp AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md docs/AP_Exception_Assistant_Codex_Spec.md` | Exit 0; specification copy byte-identical (123,229 bytes). |
| `git branch --show-current` and `git remote -v` | Exit 0; `main`, with the requested HTTPS origin for fetch/push. |
| `git diff --check` and `git diff --cached --check` | Exit 0; no working-tree or staged whitespace errors. |
| `git diff --cached --stat` and `git status --short --branch` | Exit 0; only the 19 intended baseline/source files staged. |
| `git diff --cached --` over authored docs/configuration | Exit 0; diff inspected; exact-copy/original source additions separately checked against pre-change hashes. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --collect-only -q -p no:cacheprovider` after baseline creation | Exit 5; no tests collected in 0.00s. Expected for documentation-only P0-01; no application tests passed. |

### Self-review

Reviewed authored documentation, staged scope, and preserved source additions. README describes planned capabilities and actual setup; no working startup commands or production claims are invented. AGENTS preserves the approved stack, finance invariants, one-task approval gates, and updated publication policy. Coverage remains entirely unimplemented. Assumptions distinguish defaults, missing external inputs, and observed tools. No application work, dependency installation, credentials, or real finance documents were added. The original ZIP is intentionally included as provenance, not generated runtime data.

### Publication

Local verification is complete. The clean initial baseline commit is `0e55422f596f470b5ea39ba491ef90532f59fc68`, message `chore: establish project documentation baseline` (`git commit` and `git rev-parse HEAD`: exit 0). It contains exactly the 19 intended baseline/source files.

`GIT_TERMINAL_PROMPT=0 git push -u origin main` returned **exit 128**:

```text
fatal: could not read Username for 'https://github.com': terminal prompts disabled
```

Git HTTPS authentication is unavailable to the checked noninteractive environment. No credentials, identity, or authentication configuration were changed; no workaround or force-push was attempted. The verified local baseline commit remains intact.

After the failed push, `GIT_TERMINAL_PROMPT=0 git ls-remote origin` returned **exit 0 with no refs**. Remote `main` does not exist; no baseline files were published, so remote SHA/file verification cannot succeed yet. `git status --short --branch` returned exit 0 with a clean local `main` before recording this blocker.

An additive documentation-only follow-up records this actual publication result and environment limitation locally, as required by the P0-01 approval. The working tree and committed progress must remain consistent. P0-01 remains unchecked because its remote publication acceptance condition is not satisfied. Once the user configures GitHub authentication, retry the existing commits with a normal push and verify the remote SHA and exact file set before completing P0-01. Do not begin P0-02 without separate approval.

### Limitations and next task

No application code, project dependencies, runtime setup, database, migrations, APIs, finance rules, extraction, fixtures, ML, or Azure resources were created. Application tests do not exist. Phase 0 exit criteria remain unmet. Environment prerequisites are recorded, not installed. **Active P0-01 blocker: GitHub HTTPS authentication is required to publish and verify the baseline.**

Next recommended task: **P0-02 — Domain contracts, state enums, Decimal/currency conventions, evidence schema, and unknown-data semantics**, only after user approval. This task stops after P0-01.

## Publication policy

The user explicitly authorized the initial verified P0-01 baseline on `main`. From P0-02 onward, keep approved task work and commits local, and publish consolidated phase work only after the entire phase is completed, verified, and approved, unless explicitly directed otherwise. No force-push is authorized.

## P0-02 work record

### Approved scope and recorded implementation plan

Implement only reusable standard-library domain values under `apps/api/app/domain/`: the five specified state enums, immutable exact-decimal Money with structurally normalized currency, and scoped immutable evidence references with normalized bounding boxes and import-cell provenance locators. Missing evidence must cite real current transaction/policy/snapshot references rather than an invented matched record. Enums require explicit comparisons; no unknown value becomes zero, false, NOT_APPLICABLE, or PASS.

Expected files: minimal `app`/`domain` package initializers; `states.py`, `money.py`, `evidence.py`; three domain unit-test files; a minimal root `pytest.ini` for reproducible imports/discovery. Update current README/instructions, glossary, assumptions, and coverage notices to reflect actual scope. No package/dependency installation, API, persistence, business rule, decision combiner, datasets, extraction, ML, infrastructure, or P0-03 work is authorized.

Requirements: specification sections 2.1–2.2, 13.1, 14.1, 20, P0-02 in section 21, and unit/invariant testing in section 22.1. This is supporting groundwork for AC03/AC07/AC08/AC13; no end-to-end acceptance case is completed by foundation types.

Verification plan: `python3 -m pytest apps/api/tests/unit/domain -q`, then `python3 -m pytest -q`; test exact enums/explicit unknown semantics, immutable values, exact amount inputs/arithmetic under changed Decimal contexts, currency mismatches, UUID/version/page/bounds validation, import locators, and honest missing-evidence references. Run source checksums, byte-copy comparison, documentation link checks, architecture/scope inspection, and working/staged whitespace checks. Commit locally with `feat: establish core finance domain contracts`; do not push or attempt authentication workarounds. Stop for approval before P0-03.

### What was implemented

- `states.py`: ProcessingState, ScreeningDecision, ReviewApprovalState, RuleStatus, and DecisionEffect with exact specification values. Different lifecycle enum types remain distinct; boolean coercion raises TypeError and callers must compare explicit members.
- `money.py`: frozen Decimal/currency values; finite Decimal/plain-decimal-string/integer construction; no floats, bools, or absent amounts; structural three-ASCII-letter uppercase currency; exact same-currency addition/subtraction with sufficient operand-derived private context and rounding traps; mismatch error; exact decimal-string serialization.
- `evidence.py`: all 11 evidence kinds; frozen, scoped non-nil UUID/version references; optional field/document/page/snapshot/observation metadata; normalized original-page BoundingBox and complete ImportCellLocator. Missing approval evidence cites the actual current transaction, policy, and search snapshot, without a fictitious approval ID.
- `pytest.ini`: repository-root test discovery/import configuration; no environment-variable path hacks, project dependencies, or packaging scaffold.
- Domain tests prove input boundaries, missing/unknown distinctions, immutability, decimal arithmetic/context independence, currency integrity, source-locator integrity, and missing-data representation.

### Files created and updated

Created `apps/api/app/__init__.py`, `apps/api/app/domain/__init__.py`, `states.py`, `money.py`, `evidence.py`, the three files under `apps/api/tests/unit/domain/`, and root `pytest.ini`.

Updated this tracker, `docs/data_dictionary.md`, `docs/assumptions.md`, `docs/test_coverage.md`, root README, and the stale bounded-task approval notice in AGENTS. No source pack/specification/ZIP or ADR was changed. No new ADR is needed: Decimal, explicit states, provenance, and these pure value contracts follow the already approved specification; there is no new service/persistence architecture.

### Exact verification results

| Command/check | Exit/result |
|---|---|
| `python3 -m pytest apps/api/tests/unit/domain -q` | Exit 0; final run: 241 passed in 0.08s, 0 failed, 0 skipped. |
| `python3 -m pytest -q` | Exit 0; complete current suite: 241 passed in 0.08s, 0 failed, 0 skipped. These are the same 241 distinct tests, not 482 tests. |
| `sha256sum -c docs/source_inputs.sha256` | Exit 0 before and after implementation; all nine originals, including ZIP, unchanged. |
| `cmp AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md docs/AP_Exception_Assistant_Codex_Spec.md` | Exit 0; byte-identical specification copy. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `python3` inline AST architecture/scope audit (`python3 <<'PY'`) | Exit 0; five production Python files parse using Python 3.10 grammar and import only the standard library; execution verified only on Python 3.13.11. |
| Same audit: Markdown links and coverage | Exit 0; 32 local references resolve before final progress expansion; all 42 T01–T42 rows remain NOT IMPLEMENTED. |
| Same audit: later-phase scope | Exit 0; no datasets, API server, database/migrations, frontend, workers, extraction, ML, or infrastructure. |

### Self-review and limits

Checked exact Decimal preservation and addition/subtraction under deliberately restrictive caller precision, exponent range, rounding, and traps. Same-currency `(a + b) - b == a` holds for representative values well beyond default precision. Constructors and operations reject float/boolean/missing inputs and implicit currency conversion; no monetary rounding, tax, FX, or minor-unit policy exists.

Reviewed UNKNOWN/FAIL/PASS/NOT_APPLICABLE distinctions and explicit enum comparisons; no rule engine or decision combiner exists. Evidence uses typed, scoped UUIDs and preserved versions; None coordinates stay absent, one-based pages and ordered finite normalized bounds are enforced, and import source coordinates stay intact. These contracts validate structure, not authorization, record existence, actual document transforms, or freshness.

The pytest setup is configuration only. No dependency was installed, package version was pinned, or FastAPI/Pydantic behavior was introduced. Runtime execution was on Python 3.13.11; older-interpreter syntax inspection is not a runtime compatibility test. Decimal provenance before construction, input resource bounds, actual currency support, complete transaction schemas, and real evidence resolution remain later work. No T01–T42 business scenario or Phase 0 exit gate is completed by these foundation tests.

### Commit/publication and next task

The verified task is committed locally with `feat: establish core finance domain contracts`. No push or authentication attempt is part of P0-02; the P0-01 publication blocker remains recorded. Verify the local working tree is clean after the commit. Phase 0 remains incomplete.

Next recommended task: **P0-03 — Create reproducible synthetic reference fixtures and golden finance cases**, only after explicit user approval. P0-03 has not started.

## P0-03 work record

### Approved scope and plan

Phase 0, P0-03 creates a small, hand-auditable INR-only synthetic reference set and ten independent golden scenarios. Expected files: `data/synthetic/reference/*.json`, synthetic/golden READMEs, `data/golden_cases/{vendor,employee}/*.json`, a case manifest, a fixture checksum manifest, test-only standard-library validation support and pytest integrity tests under `apps/api/tests/fixtures/`, plus existing documentation updates. No domain contract changes, dependencies, finance evaluators, extraction, application scaffolding, authentication workarounds, or push are authorized.

Relevant requirements: specification sections 2, 5–10, 14, 16, 21–23; exact decimal strings, scoped UUID identities, versioned temporal references, explicit missing facts, reproducible arithmetic, and truthful evidence expectations. Proposed fixture support: T01, T03, T08, T13–T16, T19–T20, T24, T26. All 42 business scenarios remain NOT IMPLEMENTED.

Verification plan: validate required fields, UUID uniqueness, references, tenant/entity/manager/cost-center relationships, currencies, decimal strings, temporal/policy consistency, pinned evidence and manifest mappings. Test malformed mutations as well as actual relationships and expected operands; compare repeated normalized loads/digests. Run existing domain tests, new fixture tests, the full suite, original-input SHA-256 and byte-copy checks, fixture checksums, documentation/scope audit, and working/staged whitespace checks. Self-review and update exact results before one local commit; stop before P0-04.

### What was built

Twelve JSON reference envelopes contain 38 root records: two tenants, three entities, one cost center, one vendor, four employees, one PO with one line, one GRN with one line, three expense policies, one approval policy, two budgets, five historical transactions and fourteen JSON-only source documents. Embedded lines, three prior matching allocations and six ledger rows bring reference UUID records to 49. All finance activity is in one entity; other scopes are isolation-test sentinels.

Ten independently adjudicated golden cases: vendor clean/paid duplicate/partial GRN/missing approval; employee taxi/two-night hotel/unknown-night hotel/daily meals/shared within/shared exceeded. Their transactions, source/reference links, version pins, expected facts, future decisions, concepts, rationale and evidence relationships are data only. The total dataset has 108 distinct UUID records. The 23 JSON files are covered by `data/synthetic/fixtures.sha256`; fixture/golden READMEs explain intentional updates and limits.

Test-only `apps/api/tests/fixtures/fixture_support.py` loads deterministic JSON, reuses Money/state/evidence contracts, and validates required fields, UUID identity/uniqueness, typed and scoped links, manager/cost-center consistency, currencies and decimal strings, nested float/constants/duplicate-key rejection, effective dates, applicable policy overlaps, demo bands, declared policy bindings, allocation lifecycle/ledger-owner consistency, human approval vocabulary, snapshot dependency closure and evidence kind/version/field paths. Tests corrupt independent copies and derive exact operands from the baseline records. No validator returns a screening decision.

Fixture support is exactly T01, T03, T08, T13, T14, T15, T16, T19, T20, T24 and T26. All 42 coverage rows remain NOT IMPLEMENTED. The remaining 31 IDs have no dedicated golden preparation. No claim of behavior PASS or end-to-end coverage is made.

### Exact verification results

| Command/check | Exit/result |
|---|---|
| `python3 -m pytest apps/api/tests/unit/domain -q` | Exit 0; 241 passed in 0.08s, 0 failed, 0 skipped. |
| `python3 -m pytest apps/api/tests/fixtures -q` | Exit 0; final fixture run: 123 passed in 0.28s, 0 failed, 0 skipped. |
| `python3 -m pytest -q` | Exit 0; 364 passed in 0.34s, 0 failed, 0 skipped. This is 241 existing + 123 new distinct tests, not a sum of repeated runs. |
| `sha256sum -c docs/source_inputs.sha256` | Exit 0; all nine original project files, including ZIP, unchanged. |
| `cmp AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md docs/AP_Exception_Assistant_Codex_Spec.md` | Exit 0; specification copy byte-identical. |
| `sha256sum -c data/synthetic/fixtures.sha256` | Exit 0; all 23 JSON files report OK. |
| `git diff --check` | Exit 0; no working-tree whitespace errors. |
| `python3 /tmp/audit_p003.py` (ad hoc standard-library documentation/scope audit) | Exit 0; 79 local Markdown references including heading anchors resolve; all 42 scenario/expectation rows match the specification and remain NOT IMPLEMENTED; 13 Python files parse with Python 3.10 grammar and import only stdlib/existing domain/pytest support. Runtime tested only on Python 3.13.11. |
| Same audit: scope and limited credential patterns | Exit 0; exactly 37 authorized files, no domain/source changes, no application/extraction/rules/dependency files and no common private-key/AWS/GitHub signatures in changed text. This is not a security certification. |
| Same audit and repeat-load fixture tests | Exit 0; 108 unique scoped UUID records, ten independent cases. Repeated canonical content/digest agree: `1fdd167453d530ad286dbb633ed1e0abb5051f61b38b08bfd3b13a6ba52550b6`. |
| `git diff --cached --check` | Exit 0; no staged whitespace errors. |
| `python3 /tmp/audit_p003.py --staged` | Exit 0; all documentation/scope/fixture checks above plus exactly 37 intended files staged, no unstaged tracked changes. |

### Self-review and limitations

Reviewed scoped references and parent versions, effective periods and policy dimensions, exact decimal fields, pinned dependency closure and evidence paths. PO/GRN operands give 100 ordered, 85 accepted minus 5 returns = 80, prior consumed 30, available 50, new 70 and shortfall 20; cancelled/reversed allocations remain distinct. Supplies budget is 200,000 − 35,400 − 82,600 = 82,000; covered invoice incremental need is zero. Travel budget is 50,000 − 600 − 600 = 48,800. Hotel 15,000 / 2 = 7,500 versus 8,000; missing nights stay null. Meals total 1,800 versus 1,500. Shared receipt alternatives total 1,200 or 1,400 against 1,200, with proposed shares explicitly uncommitted. Missing approval does not invent an action UUID.

All people, organizations, tax identifiers and account tokens are visibly fictional. JSON source facts do not include document bytes or real bank/payment instructions. Demo approval roles and source verification tags are declarations, not authentication, actual receipt validation, or policy authority. The first two INR approval bands have actors/actions; higher bands are configuration only. One currency/cost center and three expense categories are represented. No FX, contract/service acceptance, UOM conversion, image transformation, import freshness, concurrency, training/performance dataset or full 200/10k construction is delivered.

No production domain code was changed and no dependency installed. No database/API schema, finance rule, evaluator, application scaffold, extraction adapter, TypeLLM, ML or cloud component was introduced. The validator is test support for this data shape. Python 3.10 grammar inspection is not runtime compatibility verification. No new ADR is needed because fixture conventions follow the approved specification without a new production architecture decision. Phase 0 remains incomplete and P0-04 has not started.

### Documentation and local commit

Updated root README and the bounded-task notice in AGENTS, this progress tracker, assumptions, fixture dictionary and fixture support coverage. Added synthetic and golden READMEs. Original documents/specification/ZIP and prior domain contracts are unchanged.

One verified local commit uses `test: add synthetic finance fixtures and golden cases`. No push or authentication workaround is attempted; P0-01 publication remains separately blocked. Staged scope/whitespace and post-commit cleanliness are checked locally.

Next recommended task: **P0-04 — Define the ExtractionAdapter contract and run a TypeLLM/VLM compatibility spike on varied synthetic documents**, only after explicit user approval. Stop here.

## P0-04A work record

### Approved design and verification plan

Phase 0, bounded P0-04A establishes an immutable, provider-independent DocumentBundle/FieldObservation/ExtractionResult boundary, a small ExtractionAdapter Protocol, deterministic fixture responses and a reusable comparison harness. Expected files: `apps/api/app/domain/extraction.py`, `apps/api/app/extraction/{base,fixture,spike}.py` and package marker, `apps/api/tests/unit/extraction/`, `data/extraction_spike/` manifest/response JSON/README/checksums, a document-only compatibility checklist, and existing tracking documentation. Specification basis: sections 3.3, 4.1, 4.3–4.6, 13.1, 20–22. No finance decisions, real TypeLLM/SGLang/VLM/OCR/preprocessing, dependency installation, model downloads, credentials or push are authorized.

Design: raw text and optional unverified candidate text stay distinct; PRESENT/MISSING/ILLEGIBLE/AMBIGUOUS/NOT_APPLICABLE are separate extraction states. A bounded header plus flat indexed rows supports line items. Source references reuse P0-02 EvidenceReference/BoundingBox, with optional page-only provenance and no invented boxes. Result metadata identifies adapter/provider/schema/document/version and optional model/runtime/template/timing/artifact data. Ten structured synthetic cases have future visual artifact slots; fixture responses are separate from benchmark ground truth. Critical-field, state/abstention, line coverage/value, locator availability and optional latency metrics are reported independently; unavailable/empty metrics remain null.

Validation plan: contract type/immutability/uncertainty/evidence and financial-status separation tests; deterministic fixture behavior, scope/version/input-digest binding and no golden finance dependency; harness wrong-value, guessed-abstention, missing-row, unsupported-locator and unavailable-metric tests. Run existing domain and P0-03 fixture tests, new extraction tests, full suite, source/spec-copy checks, unchanged P0-03 checksums, new spike checksums, documentation/import/scope audits and working/staged whitespace checks. Keep the original 23-file finance checksum set unchanged; narrowly scope its test inventory to its documented directories so the new extraction dataset has its own manifest. One local commit, then stop before P0-04B; parent P0-04 remains incomplete.

### What was built

The standard-library extraction contract defines frozen DocumentBundle/DocumentPage, FieldObservation, LineItemObservation, AdapterMetadata/VersionMetadata/AdapterCapabilities and ExtractionResult. Header/row/page resource limits are explicit. Raw observed text and unverified candidate strings are separate. Non-PRESENT states reject chosen candidates; MISSING rejects invented raw text. No confidence number is required or supplied. Optional diagnostic notes are uncalibrated. ExtractionStatus is separate from screening/rule status; COMPLETED can still contain illegible fields. Evidence reuses P0-02 normalized optional BoundingBox/one-based page semantics and validates result/input document/version/scope/page binding. No source box is fabricated.

ExtractionAdapter is a small runtime-checkable Protocol. FixtureExtractionAdapter replays immutable separate responses by full canonical input SHA-256 and schema, requires synthetic inputs, and verifies binding. It reads no files during extract, consults no golden finance outcomes, parses no text and executes no rules. Fixed synthetic run IDs repeat deterministically; production run history/identity generation is not implemented.

Ten future spike cases are prepared in `data/extraction_spike/`: clean vendor, multi-page/multiple rows, clean receipt, small/poor text, declared rotation, ambiguous numeric date, inclusive-tax variation, missing PO, obscured total and repeated header/footer. These contain structured text/metadata and explicit raw/candidate/state/row ground truth, separate from response JSON. Available text and page evidence are authored synthetic declarations; artifact slots and all boxes are null. There are no actual image/PDF/OCR/VLM artifacts or visual tests. The repeated footer's policy-override instruction remains observed text. Receipt NOT_APPLICABLE PO is a schema annotation, not a policy waiver.

The provider-independent harness records each status/run/failure, version metadata, independent total/currency/document-number/date/party metrics, exact state/abstention comparisons, indexed row count/coverage/value agreement, missing/extra rows, locator availability and optional adapter timing. Missing results count as disagreements; empty denominators and unsupported locators are null, never perfect. Exception messages are excluded; exception class is recorded. Runtime reports are separate, ignored output, with a CLI-only current execution timestamp. Comparison without a timestamp is deterministic. The separate checksum manifest pins exactly 11 new JSON files; the prior 23-file manifest and all old JSON are unchanged.

The generated fixture report attempts/completes all ten cases: each critical observation agrees 10/10, states 130/130, explicit abstentions 7/7, rows 12/12 and row values 48/48. Page availability is 130/130; boxes are unsupported/null and adapter latency is absent/null. These are expected replay/annotation agreements by construction, not independent extraction-quality, visual, real-world or production-accuracy results.

### Exact verification results

| Command/check | Exit/result |
|---|---|
| `python3 -m pytest apps/api/tests/unit/domain -q` | Exit 0; 241 passed in 0.08s, 0 failed, 0 skipped. |
| `python3 -m pytest apps/api/tests/fixtures -q` | Exit 0; 123 passed in 0.27s, 0 failed, 0 skipped. |
| `python3 -m pytest apps/api/tests/unit/extraction -q` | Exit 0; final required run: 124 passed in 0.09s, 0 failed, 0 skipped. |
| `python3 -m pytest -q` | Exit 0; 488 passed in 0.43s, 0 failed, 0 skipped. These are 364 existing + 124 new distinct tests, not repeated-run totals. |
| `sha256sum -c docs/source_inputs.sha256` | Exit 0; all nine original files including ZIP report OK. |
| `sha256sum -c data/synthetic/fixtures.sha256` | Exit 0; all 23 prior finance JSON files report OK; manifest unchanged. |
| `sha256sum -c data/extraction_spike/fixtures.sha256` | Exit 0; all 11 separately pinned extraction JSON files report OK. |
| `cmp AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md docs/AP_Exception_Assistant_Codex_Spec.md` | Exit 0; byte-identical specification. |
| `python3 scripts/benchmark/extraction_spike.py --dataset data/extraction_spike --output generated/reports/extraction-fixture.json` | Exit 0; generated ten-case structured replay/comparison report with truthful unsupported/absent metrics. |
| `git check-ignore generated/reports/extraction-fixture.json` | Exit 0; runtime report ignored by existing rules and excluded from commit. |
| `git diff --check` | Exit 0; no working-tree whitespace errors. |
| `python3 /tmp/audit_p004a.py` (adapted ad hoc documentation/scope audit) | Exit 0; 102 local Markdown references including heading anchors resolve; all 42 scenario/expectation rows match the specification and remain NOT IMPLEMENTED; 23 Python files parse using Python 3.10 grammar, stdlib/existing contracts/pytest only. Execution verified only on Python 3.13.11. |
| Same audit: scope, boundaries and limited credential patterns | Exit 0; exactly 31 approved files; prior domain/source/finance JSON/checksums unchanged; no provider/OCR/API/database dependency or later-phase files; no common private-key/AWS/GitHub signatures. This is not a security certification. |
| Same audit: repeat loads/status | Exit 0; old finance normalized SHA-256 unchanged (`1fdd167453d530ad286dbb633ed1e0abb5051f61b38b08bfd3b13a6ba52550b6`); ten deterministic extraction comparisons; manifest digest `db00315130436eb572065cad35b1b00edcb2c8058dad84ea862de5975387bd0a`; all 20 future compatibility topics NOT CHECKED; parent P0-04 incomplete. |
| `git diff --cached --check` | Exit 0; no staged whitespace errors. |
| `python3 /tmp/audit_p004a.py --staged` | Exit 0; all preceding documentation/scope/boundary checks plus exactly 31 intended files staged and no unstaged tracked changes. |

The first extraction-only run had 122 passing tests and two failing test assertions: the item mutation targeted the wrong field name, and a capability declaration applied to all cases rather than one. Corrected the test setups; no failure was suppressed. Final specific and full suites pass as recorded above.

### Self-review, documentation and limits

Reviewed type/immutability, raw/candidate separation, all five observation states, financial-status isolation, document/source scope/version/page consistency, bounded rows, deterministic input binding and comparisons, missing/extra rows, optional locators/timing and error privacy. Negative tests demonstrate that guessed illegible/ambiguous/missing fields, wrong critical/item values, omitted observations and incomplete row sets cannot score as correct. Other adapter implementations and real runtimes remain unverified. There is no general table alignment, normalization, localization-correctness metric, authoritative Money conversion, real document ingestion, authorization or audit/persistence service.

No TypeLLM or SGLang was installed, no model downloaded or VLM executed, no OCR integrated, no preprocessing or finance rule implemented, and no dependency/environment/credentials changed. The document-only compatibility checklist records 20 NOT CHECKED topics for later official-source/runtime verification; it makes no current provider capability claims. P0-04B/P0-04C have not started, parent P0-04 is not complete, and Phase 0 exit gates remain unmet.

Updated root README, bounded approval notice in AGENTS, this tracker, assumptions, dictionary and test coverage. Added extraction dataset README and compatibility checklist. The existing P0-03 integrity test's inventory is narrowly limited to its original documented directories; it still verifies all 23 prior files, independently of the new checksum set. No original fixture/source/specification or earlier production domain contract changed. No ADR is added because the provider-independent boundary, uncertainty and source semantics are already mandated by the approved specification; no consequential new service/dependency/persistence architecture was selected.

### Local commit and next task

Commit checkpoint: one local commit, `feat: define extraction contract and spike harness`, after staged scope/whitespace review. No push or authentication attempt is authorized or attempted; the prior P0-01 publication blocker remains recorded separately. Post-commit SHA and clean working-tree verification are reported in the completion response.

Next recommended task: **P0-04B — Verify current TypeLLM/SGLang/model compatibility and produce an exact dependency/runtime plan before installation**, only after explicit user approval. Stop here.

## P0-04B work record

### Approved research and verification plan

Phase 0, bounded P0-04B verifies official TypeLLM/SGLang/model metadata and documented interfaces, inspects this machine without changing its environment, compares the existing extraction boundary, and produces a gated exact P0-04C runtime/install/spike/rollback plan. Expected changes are documentation only: compatibility checklist, new spike plan, progress, assumptions, dictionary/coverage context and README/AGENTS scope notice as needed; an ADR only if a consequential decision is supported. Sources must have URLs/access dates and immutable revisions where practical. Distinguish upstream documentation from actual local execution; proposed pins are not compatibility-tested pins.

Investigate the string-only authoritative money boundary, explicit uncertainty/dependency/conditional mapping, bounded header/row extraction and page-only evidence, safe reasoning/error/privacy handling, exact package/model revisions, Python/CUDA/GPU requirements, native/container isolation, download/cache/storage budgets and cleanup. Local inspection is read-only: OS/CPU/RAM/disk, GPU/driver/toolkit and safe Docker/tool/package metadata. No packages, model weights, images, accounts, keys, drivers, CUDA or system settings may be installed/changed; no real adapter or P0-04C implementation, no push. Preserve the 488-test project environment and all prior source/fixture files.

Verification plan: official-source provenance/consistency review, non-mutating Python/package/hardware checks, existing full pytest suite, nine original and both fixture checksum sets, byte-identical spec comparison, documentation/link/scope audits and working/staged whitespace checks. Record unverified dependencies/hardware blockers explicitly, keep parent P0-04 incomplete, make one local documentation commit and stop for user approval.

### Findings and documented decisions

Official sources and immutable release/model/image identities are recorded in [typellm_spike_plan.md](typellm_spike_plan.md), accessed 2026-10-02–03. TypeLLM 0.5.1 declares Python>=3.10/Apache-2.0 and supports client-encoded images, scalar/null/enum/DAG/conditional questions; nested property objects/arrays are rejected. Its number decoder returns float. [ADR-0002](adr/0002-extraction-money-and-provider-boundary.md) therefore records string-only printed financial values, with later trusted Decimal normalization and no float recovery. Existing domain contracts are unchanged. Explicit states/conditional omissions, serialized field/row calls, page-only provenance with bbox None, reasoning suppression and sanitized failures are proposed mappings, not an implemented adapter.

TypeLLM README names Qwen3.8-27B for images, but its recorded image smoke actually uses RadixArk/Qwen3.8-27B-NVFP4-BF16-LMHead on Blackwell; exact engine version/model revision are absent. Stock BF16 weighs 55,563,006,776 bytes (~51.75 GiB), recorded derivative 23,749,332,688 (~22.12 GiB), both beyond local 16,380 MiB before runtime overhead. Official Qwen FP8 and NVIDIA NVFP4 variants also exceed capacity. Qwen3.5-4B revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a weighs 9,319,828,096 bytes (~8.68 GiB); TypeLLM evidence is text-only, its proposed image tuple explicitly experimental.

VERIFIED LOCALLY: Ubuntu 24.04.2/x86_64/glibc 2.39, Intel Ultra 7 265/20 cores, 62 GiB RAM (43 available), single RTX 2000 Ada/SM8.9, driver 550.120/nvidia-smi CUDA driver capability 12.4, nvcc NOT AVAILABLE on PATH; /data ~790 GiB free and root/home/tmp ~238 GiB. Docker CLI 29.1.3 exists but daemon/image queries exit 1 with permission denial. NVIDIA container tools 1.20.0 exist; GPU passthrough NOT YET VERIFIED. Python 3.12.3 lacks ensurepip/pip. Existing Python 3.13.11/Torch 2.10.0+cu128 CUDA enumeration works; not evidence of selected inference compatibility.

Verdict **NOT FEASIBLE ON THIS MACHINE** in its current state. Proposed SGLang 0.5.21 pinned amd64 container uses CUDA 13.0.3/Ubuntu 24.04/Python 3.12 and requires a supported >=580 host driver. Image metadata source SHA matches the release; runtime package imports/resolution remain unverified. Recommend a gated small 4B BF16 experiment only after supported runtime and owner-approved Docker GPU access are supplied. The older official cu129 image is a separate unverified alternative, not an automatic workaround. Neither system changes nor remote/paid compute are authorized. Storage reservations are 65 GiB /data and 120 GiB at actual DockerRootDir; VRAM fit remains an estimate with OOM risk.

Nine documentation files changed: AGENTS, README, progress, assumptions, dictionary, coverage context, [20-row checklist](extraction_compatibility.md), new exact plan, and ADR-0002. The plan includes provenance, version matrix, native/container comparison, conditional install/check/download/launch/text-image smoke/future ten-case entrypoint commands, network/privacy, bounded failure mapping and scoped rollback. Commands were syntax/signature checked only, NOT executed. The future benchmark entrypoint/visual manifest is explicitly not available yet. Parent P0-04 remains incomplete; P0-04C has not started; all T01–T42 remain NOT IMPLEMENTED.

### Executed verification

| Exact command/check | Exit/result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | Exit 0; **488 passed, 0 failed, 0 skipped**, 0.43s. Existing test files unchanged. |
| `sha256sum -c docs/source_inputs.sha256` | Exit 0; all nine preserved original inputs OK. |
| `sha256sum -c data/synthetic/fixtures.sha256` | Exit 0; all 23 prior finance fixture JSON files OK. |
| `sha256sum -c data/extraction_spike/fixtures.sha256` | Exit 0; all 11 structured extraction JSON files OK. |
| `cmp docs/AP_Exception_Assistant_Codex_Spec.md AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md` | Exit 0; specification copy remains byte-identical. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_p004b.py` | Exit 0; exactly nine documentation files, 122 local links/anchors resolve, all 42 scenarios unchanged, no provider/runtime/test/data changes. Temporary audit script is not part of the repository. |
| Same audit: source/pin/command consistency | Exit 0; five model revisions/blob byte inventories and selected image source/CUDA/digest agree with retrieved official metadata. Ten shell blocks pass bash -n; seven Python examples parse and client/generate keyword signatures match 0.5.1 source. No proposed code executed. |
| Same audit: runtime/fixture preservation | Exit 0; 16 recorded package states unchanged, selected kernel still absent, no experiment directory created. Finance normalized digest remains 1fdd167453d530ad286dbb633ed1e0abb5051f61b38b08bfd3b13a6ba52550b6; extraction manifest remains db00315130436eb572065cad35b1b00edcb2c8058dad84ea862de5975387bd0a. Ten deterministic fixture comparisons; latency remains null. |
| Same audit: status/security checks | Exit 0; 20 topics: 11 VERIFIED FROM OFFICIAL SOURCE, 0 VERIFIED LOCALLY provider rows, 5 NOT VERIFIED, 3 BLOCKED, 1 UNSUPPORTED. No NOT CHECKED rows. Limited credential-pattern scan clean; not a security certification. |
| `git diff --check` | Exit 0; no whitespace errors. |

Runtime mutation: TypeLLM installed NO; SGLang installed NO; model weights downloaded NO; Docker inference image pulled NO; CUDA/driver modified NO; project runtime modified NO. Only official source/metadata text and temporary audit data fetched; no real documents, keys or private reasoning sent/stored. Existing fixture operation preserved. Complete transitive licensing, actual model/kernel/CUDA/image compatibility, measured latency/quality and visual artifacts remain outstanding.

Publication policy: one local documentation commit `docs: verify TypeLLM spike compatibility plan`; no push attempted. `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_p004b.py --staged` and `git diff --cached --check` both returned exit 0: exactly nine authorized documentation files staged, no unstaged tracked changes, no whitespace errors. Final commit SHA and post-commit clean-tree state are reported in the checkpoint completion message. No Git authentication/configuration was changed. Stop before P0-04C.

Next recommended step: supply supported CUDA 13 runtime and owner-approved GPU Docker access, then explicitly approve the pinned Qwen3.5-4B experimental image smoke and gated ten-case P0-04C spike. Keep the fixture adapter operational; no automatic dependency/model/hardware/hosted-provider substitution. Await approval.

## P0-04C1 work record — blocked prerequisite gate

### Approved scope and stop decision

Phase 0 / parent P0-04 / P0-04C1 authorizes a fresh prerequisite gate, then only the approved pinned runtime and one text/one synthetic image smoke if every mandatory prerequisite passes. The latest approval explicitly forbids driver/system/Docker configuration changes, workarounds, the full ten-case benchmark and P0-04C2. The gate was checked before any download/install. It failed; runtime work stopped immediately. Necessary support is documentation only in AGENTS, README, this record, extraction_compatibility and an appended observed-results section in typellm_spike_plan. No application, adapter, dataset, dependency or ADR change is needed. Verification: existing regression suite, three checksum sets, byte-identical spec, documentation/scope and staged whitespace checks; one local documentation commit, no push, stop.

### Observed gate, 2026-10-03 01:11:59 IST

Primary classification **BLOCKED_DRIVER**; additional independent failure **BLOCKED_DOCKER_ACCESS**. Failure stage **ENVIRONMENT_FAILURE**, before image pull or model/client setup. The approved SGLang 0.5.21 digest remains unchanged and uses CUDA 13.0.3 with a supported >=580 driver requirement from the P0-04B plan. No alternate stack was selected.

| Exact command/check | Exit / actual result |
|---|---|
| `nvidia-smi` | Exit 0; driver 550.120, advertised CUDA driver capability 12.4; 1,417 MiB / 16,380 MiB used before any experiment. No model load or inference occurred. |
| `nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv` | Exit 0; one RTX 2000 Ada Generation, 550.120, 16,380 MiB, capability 8.9. Driver gate fails. |
| `docker --version` | Exit 0; CLI 29.1.3. |
| `docker info` | Exit 1; permission denied while connecting to Docker API at unix:///var/run/docker.sock. Daemon/GPU/container state not verified. |
| `docker info --format '{{json .Runtimes}} {{json .DockerRootDir}}'` | Exit 1; same permission denial. Empty/null formatted values are not evidence that no runtime/storage exists. |
| Python command discovery for `nvidia-container-cli` | /usr/bin/nvidia-container-cli found; no tool installed. |
| `nvidia-container-cli --version` | Exit 0; CLI/library 1.20.0. This does not establish GPU passthrough. |
| `python3 --version` | Exit 0; existing project Python 3.13.11. No inference environment created. |
| `free -h` | Exit 0; 62 GiB total, 42 GiB available, 8 GiB swap. |
| `df -h /data` and `df -h` | Both exit 0; ~790 GiB /data, ~238 GiB root/home/tmp free. Byte-level disk inspection: /data 848,253,620,224 bytes; root/home/tmp 255,498,735,616 bytes. |

GPU passthrough **NOT VERIFIED** because Docker access failed; no container was pulled/run to test it. Storage capacity on the observed filesystems is sufficient for the planned reservation, but actual DockerRootDir remains **NOT VERIFIED**, so the complete storage prerequisite cannot pass. Required budget unchanged: model weights 9,319,828,096 bytes/full listed repo 9,342,907,469 bytes, container compressed 15,164,770,325 bytes; /data temporary downloads 10 GiB, cache/possible copy 9 GiB, overlay/artifacts/reports/kernel cache 4 GiB, plus safety reserve. Reserve 65 GiB /data and 120 GiB at actual DockerRootDir, including extraction temporary space and 30 GiB safety per location. Conditional remaining free space would be ~725 GiB /data and ~118 GiB root if Docker storage is on root. No storage was allocated for inference.

### Smoke, runtime, privacy and cleanup

Text smoke **NOT RUN**; image smoke classification **IMAGE_PATH_NOT_RUN**. Actual container/dependency matrix, model load, schema/null/enum/money-string behavior, thinking suppression, health, OOM, image stability and latency remain **NOT VERIFIED**. Model-loaded/text/image peak VRAM and latency are unavailable, not zero. No extraction result or finance decision was fabricated. Existing string-only money/Decimal boundary is unchanged.

No container/image/model/client package downloaded or installed; no runtime/p004c directory, synthetic image, adapter, model server, named container or network created. No host driver/CUDA/OS package/group/socket/service/Docker configuration changed; no sudo used. No real finance documents, credentials or reasoning processed. Nothing required container/network cleanup; shared resources/caches were not queried destructively or removed. Only gate documentation and a temporary local read-only inventory record exist from this step; no inference artifacts occupy disk. Full ten-case provider benchmark and P0-04C2 **NOT RUN / NOT STARTED**.

### Regression and preservation

| Exact command | Exit/result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | Exit 0; **488 passed, 0 failed, 0 skipped**, 0.43s. Existing test/environment baseline preserved. |
| `sha256sum -c docs/source_inputs.sha256` | Exit 0; nine original inputs OK. |
| `sha256sum -c data/synthetic/fixtures.sha256` | Exit 0; 23 prior finance fixtures OK. |
| `sha256sum -c data/extraction_spike/fixtures.sha256` | Exit 0; 11 prior structured extraction JSON files OK. |
| `cmp docs/AP_Exception_Assistant_Codex_Spec.md AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md` | Exit 0; 123,229-byte specification copy unchanged. |

Next external action: machine owner/administrator supplies a host driver supported by the approved CUDA 13 runtime (>=580 baseline) and authorized Docker daemon access with NVIDIA GPU passthrough. These system changes are outside this task and were not attempted. Then reapprove/recheck P0-04C1 using the same pins; do not jump to P0-04C2. Parent P0-04 remains incomplete. A documentation-only local commit records the fresh failed gate; no push authorized.

Documentation self-review: `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_p004c1.py` returned exit 0: exactly five documentation files, 125 local links/anchors resolve, original P0-04B plan/pins preserved byte-for-byte as a prefix, all 20 provider statuses unchanged, all 42 business scenarios unimplemented, no experiment directory, and all 16 recorded host package states unchanged. Limited credential-pattern scan found no common key/token signatures; this is not a security certification. `git diff --check` returned exit 0. The temporary audit/inventory files are outside Git. Final local commit SHA, staged-check result and clean-tree status are reported in the checkpoint completion message; push not attempted.

## Phase 0 consolidated closure — approved implementation plan

The 2026-10-03 user approval supersedes the prior per-task stop gates for the remainder of Phase 0 only. Close P0-04 with its verified fixture/contracts/research and externally blocked real-runtime outcome; consolidate P0-05; complete P0-06 architecture decisions; review all Phase-0 exit criteria; commit and attempt the Phase-0 main push once. Do not rerun the host gate, install/download inference, provision cloud resources, or begin Phase 1.

Expected changes are documentation only: README, AGENTS, progress, assumptions, data dictionary, compatibility checklist, appended runtime-plan closure, coverage clarification, new inference architecture and Phase-0 exit review, plus ADR-0003–0008 covering identity, effective policy selection, durable jobs, private storage, RULES_ONLY risk mode and optimized enterprise inference. Existing provider-independent contracts already accommodate replaceable extraction and version metadata; routing/crop/attempt metadata will be documented as future sidecar contracts rather than adding speculative runtime fields. Money/uncertainty/evidence code and all 488 tests remain unchanged.

Specification basis: sections 2–4, 5, 12–14, 17–19, Phase-0 tasks/exit in section 21, acceptance gates in section 23 and external-prerequisite handling in section 24. The original spec is preserved; the latest human authorization explicitly accepts deferral of the real image spike. Upstream source verification and research pins remain distinct from locally validated provider/production pins.

Verification plan: run the complete existing pytest suite, all 9/23/11 checksum sets, byte-identical spec comparison, runnable ten-case fixture CLI and report integrity, repeated normalized fixture digests, documentation/link/scope/import audit, acceptance coverage review, working/staged whitespace checks and phase-exit evidence matrix. No test deletion or invented quality/latency/VRAM metrics. Review/commit the completed phase, push main once to the authorized remote without repairing credentials, verify published SHA/file set only if the push succeeds, record the actual outcome and preserve clean local commits. Stop before Phase 1.

## Phase 0 consolidated completion — executed review

### Completed behavior and design

P0-04 closes with verified provider-independent extraction, deterministic fixture replay, ten structured extraction cases, comparison metrics, official TypeLLM/SGLang/model research and the previously observed external prerequisite failure. The fixture adapter remains the only development provider implementation. P0-05 consolidates 26 final requirements and distinguishes RESEARCH PIN from PRODUCTION APPROVED PIN: NONE. The original 20 provider-source statuses remain unchanged; real image smoke/full benchmark and quality/latency/VRAM are deferred rather than passed.

P0-06 adds six accepted ADRs: trusted server identity/UUID keys, effective versioned policy selection without permissive fallback, PostgreSQL durable jobs/outbox and independent inference workers, private original/derived storage, initial RULES_ONLY finance-risk configuration and optimized shared enterprise inference. Architecture describes native-text-first selective routing, bounded actual pages/crops, small then stronger tiers, measured quantization selection, persistent serving, supported batching, safe scoped caches, async jobs, independent scaling and future warm-capacity autoscaling. Finance laptops need no GPU/VLM runtime. No service, router, crop detector, model or Phase-1 code is implemented by these decisions.

Changed file set: README.md, AGENTS.md; docs/progress.md, assumptions.md, data_dictionary.md, test_coverage.md, extraction_compatibility.md, typellm_spike_plan.md, inference_architecture.md, phase0_exit_review.md; and docs/adr/0003–0008. Exactly **16 documentation files**. Existing application code, all 488 tests, fixtures, specification/originals, prior ADRs, checksums and configuration are unchanged.

### Exact local validation

| Command/check | Exit / result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | Exit 0; **488 passed, 0 failed, 0 skipped**, 0.43s (241 domain, 123 finance-fixture, 124 extraction). |
| `sha256sum -c docs/source_inputs.sha256` | Exit 0; all 9 preserved original inputs OK. |
| `sha256sum -c data/synthetic/fixtures.sha256` | Exit 0; all 23 finance fixture JSON files OK. |
| `sha256sum -c data/extraction_spike/fixtures.sha256` | Exit 0; all 11 extraction JSON files OK. |
| `cmp docs/AP_Exception_Assistant_Codex_Spec.md AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md` | Exit 0; copied specification byte-identical, 123,229 bytes. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/benchmark/extraction_spike.py --dataset data/extraction_spike --output generated/reports/phase0-fixture.json` | Exit 0; generated ten-case structured fixture comparison, ignored by Git. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_phase0.py` | Exit 0; exactly 16 authorized documentation files; 187 local links/anchors resolve; T01–T42 unchanged and NOT IMPLEMENTED; all AC01–AC20 mapped to foundations and pending release work. Temporary audit is outside Git. |
| Same audit: preservation/runtime/development boundary | Original runtime-plan text preserved as exact prefix; original 20 provider statuses unchanged; final matrix 26 requirements; all 16 recorded package states unchanged, no experiment directory; 10 application modules parse as Python 3.10 and import only stdlib/project code. Execution remains verified on Python 3.13.11. No GPU gate rerun. |
| Same audit: version/digest/replay checks | Actual contract/data/report/adapter versions match catalog and unchanged historical Git code. Finance digest 1fdd167453d530ad286dbb633ed1e0abb5051f61b38b08bfd3b13a6ba52550b6 and extraction digest db00315130436eb572065cad35b1b00edcb2c8058dad84ea862de5975387bd0a unchanged. Deterministic library replay matches CLI report except generated UTC timestamp. |
| Same audit: ignored artifacts / limited credential patterns | Report and model paths ignored. No common private-key/AWS/GitHub token signatures in changed docs; limited scan is not security certification. |
| `git diff --check` | Exit 0; no working-tree whitespace errors. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_phase0.py --final` | Exit 0; qualified Phase-0 completion, four exit criteria and Phase-1 boundary verified. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_phase0.py --staged` | Exit 0; exactly 16 intended documentation files staged; no unstaged tracked changes; all link/scope/version/preservation checks pass. |
| `git diff --cached --check` | Exit 0; no staged whitespace errors. |

Fixture observations: 10/10 COMPLETED replay cases; 130/130 state agreement; 7/7 expected abstentions; 12/12 row coverage; 48/48 important row-value agreement; 130 declared page locators available; zero boxes with unsupported ratio null; adapter latency count 0 and min/max/mean null. These are authored response/annotation comparison results, not measured image accuracy, evidence correctness, VLM latency/VRAM or business screening.

### Exit review and limitations

All four Phase-0 exit criteria are **SATISFIED** under the latest approved external-runtime qualification: versioned contracts; compatibility notes; reproducible fixtures; no unsupported provider assumptions. Money/currency, uncertainty, evidence and replaceable extraction remain stable. Normal fixture development needs no cloud/model dependency. None of AC01–AC20 is claimed as a full-product release pass; all 42 mandatory business cases remain NOT IMPLEMENTED. TEST FIXTURE READY is distinct from BUSINESS BEHAVIOR IMPLEMENTED.

Real runtime execution remains BLOCKED_EXTERNAL_PREREQUISITE: recorded driver 550.120 / CUDA 13.0.3 supported >=580 requirement, Docker daemon permission denial and unverified GPU passthrough. Adequate observed filesystem capacity does not verify DockerRootDir. No models/runtime downloaded/installed, no host configuration changed, no cloud provisioned, no real documents/secrets/reasoning processed. Real image benchmark, latency, VRAM, quantized accuracy and text/visual/model cascade are **DEFERRED — REQUIRES SUITABLE INFERENCE HOST** plus later provider/preprocessing implementation. Production model/tier/format approval is NONE.

### Commit and publication boundary

After the final/staged audit and whitespace review, commit the consolidated verified Phase 0 with `docs: close Phase 0 with optimized enterprise inference`. Exactly one normal main push to the authorized repository follows; actual SHA/publication outcome will be in the completion report and any necessary local blocker record. Do not repair credentials, retry or force-push. Preserve clean local commits if publication fails.

Recommended first major next batch only: **P1-01 — API/frontend scaffold, PostgreSQL migrations, local storage adapter and durable jobs/outbox**, explicit fixture development mode and RULES_ONLY risk design. No Phase-1 implementation has started. Phase 0 is complete locally; waiting for approval to begin Phase 1.

## Phase 0 publication outcome — single authorized attempt

The verified completion commit is **a5d09b7b7192e8829f4e4ac0adf28affd2bdf3e1**, `docs: close Phase 0 with optimized enterprise inference`. It contains exactly the reviewed 16 documentation files, with 598 insertions / 43 deletions. `git commit`, `git rev-parse HEAD` and `git status --short --branch` returned exit 0; the working tree was clean on main before publication.

A Python standard-library guard confirmed that origin is exactly https://github.com/Vansh-A1/microsoft_inovate.git, branch is main and the tree is clean, then executed **exactly one** push using `GIT_TERMINAL_PROMPT=0 git -c core.askPass= push -u origin main`. Result: **exit 128**.

```text
fatal: could not read Username for 'https://github.com': terminal prompts disabled
```

**Phase 0 complete locally. Push blocked by local Git authentication.** No retry, credential/configuration repair, token exposure, force-push or alternate publication path was attempted. This command did not publish the Phase-0 commits; remote SHA/file-set verification is unavailable after the failed push and is not claimed. The previous local task history and completion commit are preserved.

A documentation-only follow-up records this actual outcome in progress, assumptions and the exit review. `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_phase0.py --final --publication-staged`, `git diff --check` and `git diff --cached --check` returned exit 0: all 187 links/anchors resolve, preserved code/fixtures/versions and Phase-0 qualifications pass, exactly three outcome documents staged with no unstaged tracked changes. Its final SHA and clean-tree verification are in the completion report. The external publication gate is distinct from the deferred GPU experiment and does not reopen the approved local Phase-0 exit.

No Phase-1 implementation has begun. Stop here; recommend only P1-01 scaffolding after new approval.

## Phase 1 approved continuous implementation plan — 2026-10-03

The latest user approval authorizes **P1-01 through P1-06 continuously**, dependency setup in isolated project/user scope, coherent internal commits, full exit review and exactly one final main push. No approval stops between batches. Continue independent work if an external component is blocked. No sudo/system changes, GPU/live VLM/ML, cloud provisioning or Phase-2 implementation.

### Intended behavior and bounded architecture

A user creates or previews/commits synthetic structured vendor/employee records; immutable canonical revisions persist; durable jobs run deterministic rules; immutable evaluations, every rule/evidence, audit and JSON/HTML reports persist; UI lists actual cases/counts and REVIEW/HOLD queue. Development identity comes from server-configured credentials/context, never request-body tenant/role/approval assertions. Explicit RULES_ONLY reports model NOT_CONFIGURED with no score. Phase-0 domain/extraction modules, original sources and 488 tests remain intact.

Use FastAPI/Pydantic, SQLAlchemy/Alembic and PostgreSQL; attempt safe user-space PostgreSQL binaries and Node LTS before declaring an environment blocker. SQLAlchemy SQLite is permitted only as test fallback, never the application target. Persist a bounded relational subset: tenant/entities, scoped immutable reference records/links/snapshot membership representing the verified masters/PO/GRN/policies/budgets/history, transactions/versions, trusted approval records, evaluations/rules/evidence, review projections, reports/audit, import batches/rows, durable jobs/outbox/idempotency and minimal guarded capacity records needed for safe PASS. Typed Decimal-safe numeric columns and scoped foreign keys, append-only facts and indexed exact duplicate lookup; no full Phase-3 schema. Record this subset and future limits in an ADR.

Structured canonical schemas retain explicit nullable critical fields and string amounts, reject financial floats and forged scope/authority, and derive submitter on the server. Trusted seed approvals are separately persisted, version-bound records, not ordinary upload claims. Rules are pure over pinned immutable contexts and fixed supplied evaluation time; reference selection/evidence resolution is scoped and versioned. Implement VAL-001/002/003, VEN-001/002, EMP-001, DUP-002, EXP-003, BUD-001, APR-001 and SYS-001 with supporting PO/receipt checks only where required for the supported safe slice. Missing unsupported dependencies stay explicit and cannot PASS. No fuzzy/pHash/shared-receipt engine, advanced delegation/waivers or ML.

### Internal batches and expected files

| Batch | Tasks / output | Verification and checkpoint |
|---|---|---|
| A | P1-01: isolated tools/dependency pins/lockfiles, backend configuration and development identity, SQLAlchemy bounded models/Alembic migration, local private storage and queue foundation. | Real PostgreSQL clean migration/constraints where available; storage boundaries, baseline regression; coherent local commit. |
| B | P1-02/P1-03: validated canonical schemas, fixture-derived reference seeding, transaction/revision/import services, pure deterministic rule catalog and precedence. | Required fields, exact arithmetic, identity/date/policy/budget/approvals/duplicates/uncertainty tests; fixture preservation; local commit. |
| C | P1-04/API execution: atomic finalization/evidence/audit/report, idempotent async evaluation jobs, scoped endpoints and failure behavior. | Both-branch persisted API E2E, idempotency/auth/stale-write/immutable facts/audit rollback/job recovery tests; local commit. |
| D | P1-05: Next.js/React/TypeScript real-API workspace, overview/create/import/list/case/rules/evidence/queue/report, status polling and accessible states. | Typecheck/build and actual browser smoke with live API; loading/error/empty/responsive verification; local commit. |
| E | P1-06/exit: deterministic fixture-derived five-scenario demo, golden behavior integration, setup/migration/seed/run/test commands and formal review. | Full expanded tests, fresh database migration/seed/operations, UI E2E, all checksum sets/copy identity, docs/link/scope/secret/whitespace audit; final commit, one push and actual publication record. |

Frontend design: practical finance workbench with a restrained blue/navy palette (ink #16324F, action #185B8A, canvas #F3F6FA, surface #FFFFFF, warning #8A4B00, hold #A12636), locally available system sans-serif typography, left-aligned factual tables, a compact navigation rail and rule/evidence inspector. Color always accompanied by text. Useful overview counts lead into the actual transaction table; avoid promotional hero, decorative cards and animation. Distinguish submitted canonical facts, trusted references and computed findings. The design is reviewed against the user's functionality-first brief; no visual extravagance or mocked outcomes.

Relevant requirements: specification sections 2, 4.2/4.6, 5–10, 12–15, 17–19, Phase-1 tasks/exit in 21, testing in 22 and applicable AC01–AC14/AC16/AC18–AC19. Prioritize actual supported T01/T02/T03/T11/T13/T14/T15/T16/T26/T32 plus authorization/idempotency/stale/audit/retry boundaries; only promote a scenario after its real behavior is tested. T01–T42 full release coverage remains later-phase work as appropriate.

### Verification and stop boundary

Preserve original spec/inputs and all prior fixture checksums; no fixture churn to fit implementation. Pin actual tested dependencies and commit locks/migrations. Validate fresh migration/upgrade/seed, then both branches from create/import through queued evaluation, persisted evidence/report/queue/UI. Run complete tests and browser checks; inspect live screens and failure/empty/loading states. Document actual commands, environments, counts and any limitations, never claim PostgreSQL/UI/model validation from source alone. Commit internally and continue; after the mandatory exit gate succeeds, attempt one normal push without auth repair/retry. Stop before Phase 2 with the required consolidated report.

### Phase-1 internal checkpoint — persistence foundation

Project-local Node 24.21.0 and PostgreSQL 16.15 are installed without system changes. The application uses PostgreSQL `ap_app` with NOSUPERUSER/NOBYPASSRLS and forced scope policies. Versioned migrations, immutable-fact triggers, strict intake schemas, private storage and pinned Python/npm dependencies are present. The npm peer dependency check required TypeScript 5.9.3 rather than incompatible TypeScript 7; installation and production build then passed.

The first PostgreSQL integration pass was 21 passed / 1 failed (migration table-count expectation changed when the evaluation-input migration was added); corrected against the actual schema. The next integration pass was 28 passed / 0 failed. A subsequent lease deadline guard exposed a cleanup-order bug in finalization; it was moved before lease cleanup. The targeted eight persisted golden-case tests then passed. A complete final regression/browser exit gate remains required before Phase-1 completion. The five combined demo decisions have been computed from actual rules, not copied from expected fixture outcomes. No Phase 2 or inference-runtime work has started.

### Phase-1 internal checkpoint — executable rules and API

The pure engine covers 15 controls for both branches. Strict API intake, revisions, idempotency, CSV/XLSX preview/commit, scoped evidence resolution, durable jobs and deterministic JSON/HTML reports are implemented. The original 488 tests remain intact. Thirty-one new pure rules tests passed; the 28-test PostgreSQL suite passed before the final deadline guard, and the eight affected persisted golden cases passed after its cleanup-order correction. Final complete regression is still pending. Rule implementation `rules-p1-v3` / `1.0.2` is checkpointed in Git; further rule changes require a new version.

### Phase-1 internal checkpoint — admission freshness and bounded execution

The complete Python regression run passed: **549 passed, 0 failed, 0 skipped** in 174.42 seconds, preserving all 488 Phase-0 tests. It adds 31 pure rules and 30 real PostgreSQL integration tests. A current-request generation now prevents older jobs for the same canonical version from publishing over a newer evaluation request; expiring leases, transaction-local database timeouts and minimal capacity effects are guarded. The pure engine now directly reuses P0 Money and state validation as well as typed evidence. `rules-p1-v4` / `1.0.3` is checkpointed with its tested source. Four targeted worker/seed/authority/arithmetic tests also passed after refinements; final aggregate count will be recorded at exit.

Production frontend compiled and ran. The first ten-browser-test pass found a same-origin proxy hostname bug (five passed/five failed including selector issues). It was corrected using explicit loopback host/origin pairs; cross-origin rejection remains enforced. Browser rerun and screenshot review are pending. The API and proxy now bound request bytes before structured parsing.

### Phase-1 internal checkpoint — specification catalog and reports

Formal review aligned the executable catalog with section 11: VAL-002 format/date/currency, VAL-003 arithmetic, VEN-001 identity, VEN-002 approval status, VEN-003 account verification, PO-001–004 reference/association/terms/capacity, and separate APR-001 chain/APR-002 authority. Twenty supported controls now persist under `rules-p1-v6` / `1.0.5`. The complete post-alignment Python run passed **559 passed, 0 failed, 0 skipped** in 198.23 seconds. Three migrations match ORM metadata (`alembic check`: no new upgrade operations).

JSON and HTML now include pinned metadata, all required passed/failed checks, observed/expected/tolerance values, reason codes and authorized evidence links. Review creation is separately audited in the same finalization transaction. All nine original inputs, 23 finance JSON files and 11 extraction JSON files pass their original checksums; the specification remains byte-identical. Eleven browser checks are running against the refreshed production app; ten already passed before the catalog expansion. The frontend has been visually inspected at desktop and 390-pixel mobile widths. No Phase 2 or GPU/inference work was started.

## Phase-1 completed local exit — 2026-10-03

| Task | Disposition and verified behavior |
|---|---|
| P1-01 | COMPLETE: isolated locked FastAPI/Next stack, real PostgreSQL, three migrations, private local storage, durable leased jobs/outbox. |
| P1-02 | COMPLETE: trusted scoped identity, canonical intake/revisions and retained CSV/XLSX preview/commit provenance. |
| P1-03 | COMPLETE: 20 deterministic controls, explicit applicability/UNKNOWN, exact duplicates, party/PO/GRN/policy/budget/approval checks for the bounded synthetic slice. |
| P1-04 | COMPLETE: HOLD-first decisions, immutable input/evaluation/rules/evidence/report, atomic audit and minimal guarded capacity effects. |
| P1-05 | COMPLETE: production-built API-backed overview, create/import, transaction list, case/rules/evidence, exception filters and report screens; inspected desktop/mobile. |
| P1-06 | COMPLETE: fixture-derived five-case demo computes PASS/HOLD/PASS/REVIEW/HOLD; eight supported golden alternatives pass separately. |

Final engine is **rules-p1-v7**, per-rule **1.0.6**, decision policy **hold-first-p1-v1**, report **report-p1-v2**. Null/empty operands now produce explicit unresolved findings, including incomplete duplicate search, missing PO/GRN values and empty hotel rows. No skipped lookup is presented as a completed clean search. Historical prototype evaluations remain immutable and superseded; old implementation source is preserved in coherent commits.

### Final executed verification

| Command/check | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider --tb=short` | Exit 0: **569 passed, 0 failed, 0 skipped**, 197.53 seconds. 488 original + 44 rules + 37 PostgreSQL integration tests. One upstream Starlette/httpx deprecation warning. |
| `npm run typecheck --prefix apps/web` | Exit 0, strict TypeScript. |
| `npm run build --prefix apps/web` | Exit 0, Next 16.3.8 production webpack build. |
| `PLAYWRIGHT_BROWSERS_PATH=... npm run test:e2e --prefix apps/web` | Exit 0: **11 passed, 0 failed, 0 skipped**, 9.4 seconds against the running production frontend, API and worker. |
| `.venv/bin/python scripts/seed/phase1.py` | Exit 0; five actual computed decisions: clean vendor PASS, paid duplicate HOLD, clean employee PASS, meals REVIEW, missing approval HOLD. Refreshes current rules without deleting/replacing old facts. |
| `.venv/bin/python -m pip check` | Exit 0: no broken requirements. |
| `python3 scripts/dev/bootstrap.py` | Exit 0, idempotent isolated tool/database/dependency setup on the tested host. |
| Alembic fresh/roundtrip migration and metadata check | Integration tests pass; application at 0003_generation; `alembic check` exit 0, no new upgrade operations. |
| Original source/finance/extraction manifests and specification `cmp` | All 9/23/11 files OK; copied specification byte-identical. |

The browser suite exercises both-branch create/evaluate/persist/reload, vendor/employee PASS and duplicate/meal exceptions, 20-rule evidence/report views, CSV valid/invalid retention, queue filtering/empty state, delayed loading/simulated API error and cross-origin mutation rejection. Desktop overview, vendor case/evidence and employee HTML report plus 390-pixel create screen were visually inspected. UI test cases remain as synthetic history in the development database.

See [exit criteria and AC01–AC20 review](phase1_exit_review.md), [current scenario tracker](test_coverage.md), [actual setup/runbook](runbooks/phase1-local.md) and [bounded persistence ADR](adr/0009-phase1-persistence-and-local-runtime.md). This is a local synthetic product, not a production pilot. INR/ordinary/full-receipt rules are bounded; shared/fuzzy/live extraction/ML, full settlement/approval workflow, policy-change replay and production restore/performance gates remain deferred. Phase 0 contracts/source corpora were preserved. No system/GPU/cloud changes or Phase-2 work occurred.

The user authorized exactly one final normal main push after verification; its actual failed-authentication result is recorded below. Do not repair credentials or retry. The next major batch is Phase-2 secure original intake/preprocessing behind the existing adapter, only after explicit approval.

### Final list-read refinement and documentation audit

The transaction list now reads current canonical facts and latest generation-ordered jobs in three batched queries, rather than fetching full history separately for each record. Full revision history remains available on detail. The first targeted check caught a missing `func` import (2 passed / 1 failed); corrected, then all three targeted list/auth/idempotency tests passed. The final complete rerun is **569 passed, 0 failed, 0 skipped** in 197.53 seconds. The refreshed live-browser suite is **11 passed, 0 failed, 0 skipped** in 9.4 seconds. No finance rule changes followed this gate.

`/tmp/audit_phase1.py` returned exit 0: 201 local documentation links/anchors resolve, all 42 original scenario/expectation strings remain exact, the 21/11/10 coverage disposition and all 20 user exit criteria/AC01–AC20 rows are present. Original contracts, extraction, 488 tests, datasets and inference research remain unchanged against Phase-0 HEAD. Saved OpenAPI matches the actual app. Private development directory/files are 0700/0600; generated credentials/passwords are absent from trackable text, common secret-pattern scan is clean, and runtime/build/browser output paths are ignored. These limited scans are not a security certification. Final Alembic drift check, pip check, all checksum sets, specification comparison, generated client/typecheck and preserved ten-case fixture CLI also passed.

The documented clean stop of the owned PostgreSQL cluster and restart through `setup_database.py` returned exit 0. The application supervisor restarted; readiness reported PostgreSQL migration 0003_generation, liveness retained explicit modes, and the production frontend returned HTTP 200. This is process recovery verification, not a backup restore exercise. The local application remains running for review.

## Phase-1 publication outcome — single authorized attempt

The fully verified implementation/closure commit is **49efc94a20afcbd633ea183c9548ada493bcb4fd**, `feat: complete Phase 1 review workspace and verified local exit`. The preceding Phase-1 checkpoints are ffec67a (persistence), 3559922 (persisted finance rules), f21acfa (freshness/bounded execution), e366e29 (unsupported partial receipts) and cd01866 (specification rule catalog/report evidence). Phase-0 history was preserved. The final closure contains 27 reviewed source/documentation files, 2,012 insertions / 106 deletions; staged whitespace and full scope/secret/source/documentation audit passed. `git commit`, HEAD and status checks returned exit 0; main was clean before publication.

A standard-library guard verified the exact authorized origin, main branch and clean tree, then executed **exactly one** `GIT_TERMINAL_PROMPT=0 git -c core.askPass= push origin main`. The Git process returned **exit 128**:

```text
fatal: could not read Username for 'https://github.com': terminal prompts disabled
```

**Phase 1 complete locally. GitHub publication blocked by local HTTPS authentication.** No retry, credential/configuration repair, token exposure, alternate publication path or force push was attempted. Remote branch SHA/published file-set verification is unavailable after failure and is not claimed. A documentation-only follow-up records this outcome; its final SHA and clean working tree are reported in the completion message. It does not change the verified application.

The local application remains running on loopback for review. All mandatory local Phase-1 exit criteria are SATISFIED. Phase 2 has not begun. Waiting for approval to begin Phase 2.

## Phase-2 continuous implementation plan — 2026-10-03

The latest direct approval authorizes P2-01–P2-05 in one continuous pass; it supersedes earlier per-task approval/stop-before-Phase-2 wording. Stop before Phase 3. Baseline HEAD is **523a28397c6377b5a197586c9af8c56bd91e61bf**, clean main; preserved regression is 569 Python / 11 browser tests. The original specification, source inputs, Phase-0 contracts/extraction fixtures and Phase-1 finance cases remain the authority. Existing CPU services and scoped storage/jobs are reused. No document processor/upload pipeline currently exists; document jobs will be an additive bounded queue alongside transaction-specific finance jobs, retaining the same durable lease/outbox pattern rather than weakening their mandatory transaction/snapshot FKs.

### Architecture and safety choices

- Typed document configuration: defaults 25 MiB original, 30 pages, 40 megapixels, bounded derived rendering/text/rows/time/attempts. Create scoped expiring upload session, stream/hash into server-generated private storage, finalize actual content/integrity, persist immutable original metadata and quarantine explicit unsafe/corrupt/encrypted/limit cases with no finance decision. Malware adapter status is NOT_CONFIGURED in development, never CLEAN; production required scanning fails closed. Parsers execute in resource/time-bounded child workers, never in request handlers.
- Add scope-qualified document/version/page, upload, document-job/outbox, extraction-run/observation/normalization/draft, transaction-document and human source verification/correction records with forced RLS/immutability. Migrations are append-only. Worker stages PREPROCESS/EXTRACT/NORMALIZE/VALIDATE/FINALIZE pin current generation and implementation keys, retain completed stages, stop permanent failures and prevent duplicate effects under recovery.
- PyMuPDF native spans/pages/rendering; Pillow orientation/safe variants; OpenCV measurable blur/exposure/grayscale quality. Preserve original hashes and actual transforms, original-page coordinates and one-based pages. Unknown coordinates stay null. No image fingerprint establishes a duplicate decision.
- Native text uses a conservative versioned labeled-document parser over actual bytes/spans, not golden expected answers. OCR is replaceable; attempt only bounded project-local Tesseract setup. Visual routing remains explicit when providers unavailable. TypeLLM remote client boundary uses flat scalar state/string questions and application-managed bounded page/row requests, rejects financial floats/finance authority/reasoning, reconciles critical disagreement and retains safe provider metadata. No SGLang/GPU/model setup or fabricated VLM metrics.
- Normalize raw strings with trace: NFKC/whitespace, conservative and aggressive candidate keys preserving leading zeros/I/O, known currency and grouping Decimal, locale-bound dates or AMBIGUOUS. A document draft retains uncertainty, coverage, arithmetic/source findings. Critical unresolved facts cannot silently create eligible data. Manual source verification is required for document-derived finance eligibility in this phase; synthetic benchmark results will not establish production auto-pass quality.
- Source-linked draft commit/revision uses trusted reviewer identity, actor/reason/old/new/source and immutable canonical versions. Finance controls remain authoritative; only minimal DOC/source-context/report adaptations are needed to consume actual document facts while preserving legacy structured synthetic behavior. Receipt/attachment IDs are actual scoped documents; multi-document links preserve roles/page ranges, uncertain segmentation requires confirmation, no implicit splitting or shared-receipt allocation engine.
- Add mapped CSV/XLSX preview preserving batch/sheet/row/column/raw/parsed/errors and actual attachment validation, alongside the unchanged legacy JSON-column path. Never execute formulas/macros. No fuzzy/pHash/shared allocation/advanced finance matching or Phase-3 work.

### Internal batches

| Batch | Tasks/files | Meaningful verification |
|---|---|---|
| A | P2-01/P2-02: config, additive DB migration, private streaming storage/safety/processor, isolated dependencies and real PDF/image fixture generator. | Sniff/size/page/pixel/encryption/unsafe cases, original identity, transforms/native spans/one-based pages, real PostgreSQL constraints/scope, preserved Phase-1 suite. |
| B | P2-03/P2-04: native/OCR/TypeLLM adapters, bounded reconciliation and normalization; durable stages, observations/drafts and API. | Contract/mock timeout/null/float/disagreement, real native/optional OCR inputs, date/money/key ambiguity, replay/retry/atomic audit/current generation. |
| C | P2-04/P2-05: source verification/canonical linkage/corrections/import mappings/attachments, narrow finance integration and report/evidence resolution. | Both branches actual-document-to-finance, no-pass uncertainty, material revision supersession, cross-tenant originals/pages/evidence, attachment spoofing and multi-page bundles. |
| D | P2-04/P2-05 UI: upload/status/document draft/source viewer/page/box/correction/attachment/import mapping. | Production build/typecheck, live API browser E2E for PDF/image upload and correction, loading/error/quarantine/uncertainty/mobile, screenshot visual inspection. |
| E | Exit: real synthetic corpus/benchmark and docs/ADRs/runbook/coverage/phase review. | Full regression/new suites, fresh migrations/drift, document source/checksum preservation, honest measured native/OCR versus deferred VLM metrics, clean local commits. One consolidated phase publication under the standing request; no credential repair. Stop before Phase 3. |

Requirements: spec 2.2/3.3/4.1–4.6/13–19/21 Phase 2/22–24 and direct Phase-2 approval. Prioritize T04 normalization support, T06 uploads, T29 uncertainty/disagreement, T35 actual document authorization, T37 staged retry, T39 unsupported segmentation/type and T41 untrusted document instructions; only promote full scenarios when implemented and exercised. The supplied Phase-2 prompt ends at optimization routing item 50; existing accepted architecture provides the remaining cascade intent without authorizing GPU changes.

The recorded driver/Docker blockers remain accepted external limitations. Tesseract is absent from PATH; package metadata offers a small user-space CPU OCR option. PyMuPDF/Pillow/OpenCV/TypeLLM client pins will be locked only after installation and actual tests. No change is claimed implemented or passing at this planning checkpoint.

## Phase-2 batches A/B — verified intake, preprocessing, extraction and drafts

Implemented typed limits; two-step scoped stream/hash/original finalization; MIME/content mismatch quarantine; private source/preview endpoints; immutable document/page/run/observation/draft records; additive document jobs/outbox; safe stage failure/retry semantics; native PDF text/spans; EXIF transformations; defined OpenCV quality measurements; native-first routing; conservative headers/explicit tables; replaceable CPU OCR; TypeLLM remote SDK boundary; disagreement and normalization/arithmetic/source validation. Twelve new tables have scope-qualified FKs, forced RLS and immutable fact triggers. Existing finance-job FKs remain intact. Current migration is 0004_documents.

The first parser test run was 11 passed / 1 failed: OpenCV default thread allocation exhausted the parser address-space bound on a valid PDF. Fixed by setting one OpenCV thread; resource exhaustion now has a distinct safe code. Rerun: 12 passed, 0 failed in 0.61s. Four real PostgreSQL intake tests passed in 27.40s; extraction/normalization/stage/actual CPU photo tests: 40 passed in 62.77s. Full executed command `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider --tb=short`: **exit 0, 625 passed, 0 failed, 0 skipped, 433.02s**. Preserved 569 baseline tests; 56 new tests. One upstream TestClient deprecation warning.

Actual Tesseract 5.3.4 + English asset were SHA-verified and extracted under ignored runtime/tools/ocr from four pinned packages; no system install. A first asset filename lookup missed Debian's encoded epoch; corrected filename discovery, verified its checksum, then actual photo OCR and setup_ocr.py passed. Source PDFs/images were rendered and visually checked for clipping/legibility. Fifteen synthetic byte/ground-truth files are in data/documents_phase2; encrypted/corrupt/unreadable sources are intentional safety cases. No expected.json file is consumed by extraction. All originals remain unchanged.

TypeLLM 0.5.1 wheel's real schema compiler accepted 42 flat state/raw header questions, without inference. Mocked generate responses exercise string money, null ambiguity, invalid authority/float responses, timeout and disagreement. SDK client/runtime/model execution remains externally deferred. Optional client installation and approved preprovisioned tokenizer are documented requirements, not attempted inference. Malware NOT_CONFIGURED is preserved and required scanning fails closed. No model confidence/accuracy or GPU performance is claimed.

P2-01/P2-02 core behavior is locally verified; P2-03 independent boundary and P2-04 normalization are implemented. Remaining current batch: source-verified canonical linkage/corrections, mapped import evidence, attachments and running-browser UI. Phase 2 is not yet complete. Continue within the existing continuous approval; no Phase-3 work or publication yet.

## Phase-2 batches C/D — source facts, imports and reviewer UI

Implemented source-verified canonical creation/revisions and automatic evaluations,
immutable correction actor/reason/old/new/page traces, multiple attachment roles,
actual receipt UUID validation, mapped CSV/XLSX cell evidence, authenticated source
and field evidence lookup, upload/status/page/box/zoom/correction/attachment UI.
OpenAPI and generated TypeScript match the current application. The original
pure Phase-1 engine/ruleset/rule versions remain unchanged. New document-source
DOC-001 reconciliation is an isolated pure extension; mapped evidence changes no
screening result. Old structured paths and immutable reports remain supported.

Automatic approval review rejected an earlier global ruleset/per-rule version
change because it risked changing established Phase-1 finance behavior. That patch
was not applied. The accepted smaller integration confines new source semantics
to physical document contexts and preserves core calculations/versions. No user
permission stop or rejected-action workaround was required.

Targeted verification (all executed exit 0 after repairs): 44 Phase-1 pure finance
checks (0.11s); six physical-document finance checks (49.27s); four mapped-import
checks (32.26s); two lease/scanner checks (15.25s); 44 parser/extraction pure checks
(1.20s). A strengthened instruction-bearing invoice and actual generated receipt
finance check also passed (1 test, 17.06s): printed amounts, missing approval HOLD,
and unchanged nonempty vendor-master records. Initial failures in the new finance
and import tests were incorrect test operands/selectors, repaired against actual
behavior; the 37 original PostgreSQL checks passed in the combined mapping run.

First new browser run: 13 passed / 3 failed (duplicate Next alert/text matches and
an exact label selector); corrected semantic/scoped selectors. Rerun: 16 passed
in 38.6s. Final production rebuild includes image zoom without changing box mapping;
refreshed owned services and browser suite: **16 passed, 0 failed, 0 skipped, 41.9s**.
Desktop source/actual highlight, employee case and 390-pixel document list were
visually inspected. Loading/error/quarantine/ambiguous date/multi-page/no-box paths
use real API data; only explicit outage UI tests intercept selected responses.
TypeScript and production webpack build exited 0. Pip check and Alembic drift check
exited 0; no broken dependencies/new migration operations.

First complete expanded Python run: **640 passed / 1 failed**, 634.70s. The new
no-provider test inherited the operator's configured local OCR from private
settings, producing NEEDS_INPUT instead of the intended DEPENDENCY_UNAVAILABLE.
Made test provider configuration explicit; the complete document-stage suite then
passed **10 tests**, 137.73s. The corrected full suite is running; no pending result
is claimed passed. Private developer OCR settings and application semantics remain
unchanged by this test isolation fix.

The actual CPU corpus benchmark exited 0: 14 sources, 7 READY / 5 NEEDS_INPUT /
2 PROCESSING_FAILURE; all clean native critical fields 6/6 and clean receipt/photo/
scan fields 4/4 match independently printed ground truth. Unreadable image retains
0/4 with input required. Actual per-source CPU timings 0.085895–0.371405s concern
this single small synthetic run only, not a service SLA or live VLM metric. Generated
reports/screenshots/original uploads stay ignored. All original 9/23/11 checksum
sets and the new 15-file corpus pass; specification byte comparison passes. Local
Markdown audit resolves 212 links/anchors and retains all 42 scenario/expectation
strings. T41 CPU document instruction behavior is now implemented/tested; remaining
full release scope stays explicit (22 implemented, 11 partial, 9 unimplemented).

Current next action: finish the corrected full regression, staged review and
[Phase-2 exit review](phase2_exit_review.md), commit verified work, then make one
consolidated normal phase push under the standing user request. Do not repair
credentials/retry after authentication failure. Stop before Phase 3.

## Phase-2 final local exit — COMPLETE, enterprise runtime explicitly deferred

All P2-01–P2-05 and the three specification exit criteria are locally satisfied
under the explicit runtime qualification in the direct approval. PDFs/photos now
produce immutable versioned source-linked facts and both branches reach the
existing finance application after validated human source verification. Critical
uncertainty and unsafe files cannot automatically PASS. Fixture/native/OCR/remote
provider modes remain distinct. Phase 3 has not begun.

| Executed command/check | Exact result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider --tb=short` | Exit 0; **641 passed, 0 failed, 0 skipped**, 554.98s. Preserves all 569 baseline checks and adds 72 actual document/provider/normalization/integration checks. One upstream TestClient deprecation warning. |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest apps/api/tests/integration/test_document_finance.py::test_document_instructions_cannot_clear_approval_or_mutate_master -q -p no:cacheprovider --tb=short` | Exit 0; 1 passed, 17.06s, actual malicious invoice and receipt cannot create approvals/change master. A repeat of one test, not another distinct suite count. |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest apps/api/tests/integration/test_document_finance.py::test_bundle_and_quarantine_cannot_commit_or_attach -q -p no:cacheprovider --tb=short` | Exit 0; 1 passed, 18.38s, after the final narrow coverage guard. Source confirmation cannot dismiss retained TABLE_COVERAGE_UNCERTAIN/TABLE_ROW_LIMIT findings; unsupported partial rows require clearer input. Core finance formulas/versions unchanged. |
| `npm run generate:api --prefix apps/web` | Exit 0; saved actual OpenAPI and generated TypeScript match. |
| `npm run typecheck --prefix apps/web` and `npm run build --prefix apps/web` | Exit 0 each; strict TypeScript and production webpack build, including original-coordinate source box zoom. |
| `PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright" npm run test:e2e --prefix apps/web` | Exit 0; **16 passed, 0 failed, 0 skipped**, 41.9s. Includes all 11 original checks. Live API/worker/production UI; actual uploads and revisions retained. |
| `.venv/bin/python -m pip check` | Exit 0; no broken requirements. |
| `.venv/bin/alembic -c apps/api/alembic.ini check` | Exit 0; no schema drift. Full PG suite also tests fresh setup, isolated downgrade/upgrade, 35 total tables including Alembic, precision/constraints and forced RLS. No meaningful development data reset. |
| `.venv/bin/python scripts/benchmark/documents_phase2.py` | Exit 0; 14 actual sources, seven ready/five needs input/two parser rejection cases. Clean native 6/6 and receipt/scan/photo 4/4 independent critical fields. Generated report ignored; VLM/GPU metrics unavailable. |
| `sha256sum -c docs/source_inputs.sha256`, `data/synthetic/fixtures.sha256`, `data/extraction_spike/fixtures.sha256`, `data/documents_phase2/fixtures.sha256` (each separate command) | Exit 0 each; all 9/23/11/15 pinned files OK. |
| `cmp AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md docs/AP_Exception_Assistant_Codex_Spec.md` | Exit 0; specification byte-identical. |
| Inline Python preservation/documentation/OpenAPI/secret audit | Exit 0; 65 earlier contract/extractor/test/corpus/core-rule/migration files untouched, all 42 scenario/expectation strings preserved, local links resolve, saved API matches, private credentials/common secret signatures absent from trackable text and runtime/originals/build/results ignored. |
| `git diff --check` | Exit 0; whitespace clean. Staged review/commit/publication are recorded below. |

The final coverage guard was added after the aggregate run and tested directly
against the actual malformed-row pipeline and commit rejection. No rule engine or
other behavior changed. Browser source/page/mobile screenshots were inspected;
unknown boxes remain absent and zoom scales measured boxes with the page image.

See [Phase-2 exit review](phase2_exit_review.md), [local document runbook](runbooks/phase2-local.md),
[ADR-0010](adr/0010-phase2-document-lineage-and-provider-boundary.md), glossary and
coverage. Scanner remains NOT_CONFIGURED, native layout support is conservative,
English OCR measurements are synthetic, source verification is manual, and live
TypeLLM/SGLang/model/latency/VRAM/cascade/quantization remain externally deferred.
No driver/Docker/model/cloud experiment was repeated. No production readiness or
full T01–T42 release claim is made. Next task: separately approved **P3-01**; stop.

### Phase-2 commits and publication outcome

A/B checkpoint: `e9a22da`, secure intake/preprocessing/provider/normalization
pipeline. Verified C/D/exit implementation: `87e24ca91172b790a23c1057685f6d93df5e394a`,
message `feat: connect source-verified documents to finance and reviewer workflows`.
Staged review executed: 44 intended files, no unstaged changes, 216 resolving
local links/anchors, matching actual OpenAPI and whitespace checks; credential and
original-source reviews were clean. Both commit commands returned exit 0. Local
main was clean before publication.

Exactly one consolidated authorized Phase-2 push was executed:
`GIT_TERMINAL_PROMPT=0 git -c core.askPass= push origin main`.
It returned **exit 128**: `fatal: could not read Username for 'https://github.com': terminal prompts disabled`.

**Phase 2 complete locally; GitHub publication remains blocked by HTTPS
authentication.** No push retry, credential/configuration repair, alternate
publication path or force push was attempted. Automatic approval review rejected
a subsequent read-only `git ls-remote --heads origin main` before execution,
interpreting it as another remote attempt under the no-retry instruction. No
workaround or further network check occurred. Remote SHA/published file-set
verification is unavailable and not claimed. The verified local commits remain
intact; a documentation-only follow-up records the actual result. The owned
API/worker/production web remain running at http://127.0.0.1:3000.
Next task: **P3-01**, only with separate approval; Phase 3 has not begun.

## User-provided invoice image check — 2026-10-03

User explicitly authorized a local extraction test of an attached invoice image.
No new phase, model provisioning or extraction-code change was authorized or made.
The actual authenticated running API create/upload/finalize flow and durable worker
processed its unchanged PNG original. The result was **NEEDS_INPUT**, LOCAL_OCR /
Tesseract 5.3.4, PARTIAL extraction, ENTERPRISE_VLM NOT_CONFIGURED, no canonical
transaction or screening decision. All **21 header observations were MISSING**
and **zero line rows** mapped; critical and table-coverage findings remained input.
Original SHA-256 matched the supplied bytes. The normalizer did not guess values.

A diagnostic call through the same installed OCRAdapter, on the preserved derived
preview, read the printed subtotal, tax, total, PO/due-date text, descriptions and
payment terms. Invoice identifier punctuation, invoice date separator and one
line amount were wrong. Token readability is not complete field/row accuracy.
The current mapper requires colon-labeled headers and explicit pipe tables; this
ordinary spatial invoice layout is outside its tested parser coverage. This test
confirms the previously recorded conservative-layout limitation and failure-closed
behavior, not successful general invoice extraction or a live VLM result.

Command: authorized inline Python using existing Settings/httpx upload/status API,
then scoped DocumentPage/LocalStorage/TesseractOCRAdapter diagnostic and comparison
assertions; all command exits 0. No automated-suite rerun was needed for unchanged
code. Supplied pixels, personal/source text and detailed raw/normalized outputs
remain in ignored private runtime storage with 0600 files; they are not fixtures,
logs, Git content or remote provider inputs. No publication attempt occurred.
Next technical responsibility, if separately requested: improve measured ordinary
layout header/table mapping within the extraction boundary, or connect the
separately approved suitable enterprise inference service. Phase 3 has not begun.


## Phase 3 — approved continuous implementation, started 2026-10-03

Direct user approval authorizes P3-01–P3-06 and their necessary additive schema, dependency, API/UI and synthetic verification work. Baseline HEAD 5f082b144dd70c3f1504d1ab15ab82df6e2c5576, clean main; recorded Python 641 / browser 16. Current coverage is 22 passing, 11 partial, 9 not implemented (the attachment's older 21/11/10 count is not authoritative). No new checks are claimed yet.

Plan: A staged versioned reference activation and identity; B PO/contract/GRN/service cumulative matching; C indexed duplicate candidates, pHash and version-bound dispositions; D policy/receipt/offset/split controls; E append-only ledger and atomic capacity; F server-authorized approvals/delegation/waivers; G working API/UI, end-to-end, migrations, performance and all 38 exit criteria. Expected changes are additive finance models/migrations, pure phase3 rules, orchestrators/routes, reviewer components, synthetic corpora, tests and documentation. Preserve the legacy pure engine for retained inputs; activated Phase-3 catalogs select a versioned extension. Verify each batch before continuing, then run full regressions and actual PostgreSQL/browser gates. Original inputs and Phase-2 extraction/provider constraints remain intact. Stop before Phase 4.

### Phase-3 batch A — references and additive persistence verified

Added 13 scoped tables at 0005_finance (47 business tables total), staged validation/activation API, immutable activated reference versions, exact/curated/fuzzy identity resolution and additive lifecycle fact models. Existing snapshots remain pinned. Commands: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider apps/api/tests/test_reference_phase3.py apps/api/tests/integration/test_references_phase3.py apps/api/tests/integration/test_vertical_slice.py::test_fresh_migrations_upgrade_downgrade_and_ready apps/api/tests/integration/test_vertical_slice.py::test_real_postgres_golden_end_to_end` exited 0: 16 passed, 140.65s. Initial 7-check run had one validator mismatch (vendor master does not require currency); corrected to the established schema, then the expanded gate passed. Legacy `test_rules_phase1.py`: exit 0, 44 passed, 0.11s. Existing table-count expectations changed solely for additive schema. Full Phase-3 completion is not claimed. Next internal batch: commercial and duplicate controls.

Phase-3 batches B–F implement the activated `rules-p3-v1` extension while retaining the legacy evaluator for historical contexts. The additive, frozen `0005_finance` migration adds 13 tables, forced RLS and immutable fact/source triggers. Matching accounts for net delivery, grouped line demand, explicit UOM, configurable tolerances, contracts and authorized service acceptance. Candidate comparisons/resolutions bind both versions; pHash and fuzzy similarity remain candidates. Append-only allocation/budget lifecycles transition all resources together. Approval requests/actions use authenticated identities, effective master/delegated ceilings, ordered distinct actors and computed exception requirements; waivers retain original findings.

Executed checks: the expanded PostgreSQL/migration batch returned **19 passed in 260.49 s**; the cross-month/split/cancellation, exact DISTINCT/policy replay and decline/payment-account batch returned **3 passed in 39.58 s**. Configured exceptional CFO approval returned **1 passed in 20.68 s** after supplying its explicit master authority. Pure control/reference/image checks and scale activation have also run; the final whole-suite gate remains pending. A full-suite attempt was deliberately interrupted after discovering the new CFO test fixture lacked master authority; it is not recorded as a passing gate. The additive scale corpus supplies 20 vendors, 30 employees, 50 PO/GRN lines, 3 cost centers, explicit fictional USD/INR FX and 200 unverified structured inputs. The first isolated 10,000-history PostgreSQL benchmark ran successfully; final measurements will be rerun against the final revision. No GPU/inference setup or Phase-4 work occurred.

### Phase-3 batch G — actual UI, integration repairs and measured benchmark

Local backend commit `e82803f` preserves a coherent verified B–F implementation.
The first complete aggregate returned **696 passed**, exit 0, **1163.50 s**; all
original 641 scenarios were preserved. Its ignored log also contains residual
stderr from an earlier interrupted process; the actual completed process result
and aggregate are authoritative. A later unique-log gate includes the additional
regressions and is still running; no final 704-test success is claimed yet.

Real browser work exposed and repaired three application issues: resident worker
identity selection was accidentally overwritten by the final restricted identity;
an imported nested budget ledger lacked its server-owned child source version;
worker claim and approval mutation used different lock order. Workers now select
an explicit finance identity per scope while retaining job actor; source ledgers
get immutable reference children/activation/links; claim, failure recording and
document DB persistence acquire the same finance lock before job/transaction/audit.
Bounded SQLState retries remain explicit. Actual synchronized claim/approval,
finance admission and preserved document-finance checks returned **11 passed in
137.74 s**, exit 0. Reference/ledger/split checks returned **5 passed in 112.18 s**.

Configured preapproval now has an independently activated versioned source with
explicit PREAPPROVER master, scope/currency/ceiling/category/business dates, rather
than an unsatisfiable client-independent flag. Delegated submitter/preapproval
positive and expiry negative passed (**1 passed, 10.89 s**). A combined check had
37 passing cases and one preapproval evidence resolver mismatch; using the real
reference fact kind repaired it. Stale-reference evidence and future-freshness
abstention, independent card AND advance proof, policy gap/overlap, malformed
collection shapes and minor image blur are exercised. The original label-based
verification string stays valid; post-fix reference units returned **7 passed in
0.22 s**, exit 0. Identity resolution denies employee master-catalog access.

Frontend controls expose real commercial capacities, budget components, lifecycle,
individual duplicate signals and paired actual pages, ordered authority, receipt
shares, policy/offset/split facts, waivers and reference activation. A loopback-only
server-configured synthetic identity picker never sends bearer tokens or accepts
arbitrary roles. Private setup was executed and kept mode 0600/ignored. Approval,
duplicate and source-view loading/error/empty/role/mobile paths were exercised.
Screenshots for matching/approval, duplicate, receipt share, waiver, reference and
paired source laptop/mobile were visually inspected. No fabricated field box.

After repairing the validator's mistaken object requirement on the established
verification string, and the old overview test's incorrect unique-invoice-number
selector, `npm --prefix apps/web run test:e2e` returned **exit 0, 23 passed, 82.625 s,
0 failed/skipped/flaky**. The original overview behavior now identifies its seeded
transaction by UUID. Expense browser fixtures use distinct fictional grade/policy
dimensions so repeated local runs do not consume one another's daily capacity.
The first 23-test attempt returned 18 pass/5 fail; it is not a passing gate.

`npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build` returned
exit 0 (production compile 642 ms). `.venv/bin/python -m pip check` returned no
broken requirements. Live Alembic current = `0005_finance (head)`; check = no new
upgrade operations. Earlier actual 0004→0005 upgrade preserved meaningful old
records; fresh/base-downgrade/re-upgrade is also integration-tested. Source checks
returned exit 0: nine original source entries, 23 finance/golden, 11 extraction and
15 actual document entries; spec `cmp` and legacy-engine diff are unchanged.

Final benchmark command `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python
scripts/benchmark/finance_phase3.py` returned exit 0. It actually persisted 10,000
generated histories and 200 unverified structured transactions, then removed only
its disposable schema. All ten complete target evaluations computed PASS.
Lookup median/p95 = **3.764/4.813 ms**, pure matching/rules **2.995/3.332 ms**,
transactional finalization/budget **140.317/185.991 ms**, enqueue/claim/context/
finalization **356.879/384.471 ms**. EXPLAIN uses `ix_history_exact`. Environment and
small warm-sample limits are recorded in the exit review; no SLA claim.

README, runbook, assumptions, dictionary, exact coverage/owners and all 38 exit
criteria are updated. Current supported matrix: **36 implemented, 4 partial,
2 not implemented**. Final Python gate, staged review, final commits and the single
authorized push remain pending. Phase 4 has not begun.


### Phase-3 final local exit gate

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`
completed with **exit 0, 704 passed, 1179.01 s, zero failures/skips**, one upstream
Starlette/httpx deprecation warning. The established verification-label correction
was independently checked by the post-fix seven reference units and the complete
23-browser gate against the running final API. Unique final gate log is ignored
`generated/reports/pytest-phase3-gate.txt`; earlier interrupted attempts are not
passing gates. Collect-only confirms 704 cases; it is not an application test pass.

All 38 approved exit criteria are SATISFIED in the formal review. Local Phase 3 is
complete. Final source check/diff/precision/RLS/migration/UI/API/self-review gates
are recorded above. The final local-link checker excludes actual URI schemes
(including the original conversation link), checked 177 targets and found none
broken. Its first check incorrectly treated that preserved external URI as a local
path; the source specification was not modified. Actual OpenAPI matches the saved
contract with 45 paths. Next step is final staged review/commits and the single
explicitly authorized normal main push. Phase 4 has not begun.


Final staged security review found that the proxy honored a supplied configured
demo cookie even when the identity-picker flag was disabled. The server resolver
now honors it only with explicit AP_ENABLE_DEMO_IDENTITIES=1. Actual module
boundary command `node --test apps/web/checks/development-identity.mjs` returned
exit 0: **1 passed**, disabled/0/enabled/unconfigured/default paths checked with
private temporary synthetic inputs. A Node module-type inference warning is
non-fatal and does not change the Next bundler setup. Final `typecheck` / `build`
returned exit 0 (compile 711 ms). Restarted the owned production server and ran
all browser cases again: **23 passed, 72.343 s**, exit 0, no failures/skips/flaky.
The Node check is separate from the 704 Python and 23 browser totals. Backend
finance/extraction code did not change after the completed aggregate.

### Phase-3 commits and publication outcome

Coherent local main commits:

- `e82803f` — Implement versioned Phase 3 finance controls and atomic allocations.
- `34a0c2345333cf29c1d0e08aa9e787687bdd1b5d` — Connect Phase 3 reviewer workflows and verify finance exit gates.

Final staged review examined 33 intended files (32 before the server-identity
regression check), whitespace, private ignores, original source preservation,
credential patterns and absent user invoice content. Actual OpenAPI matches
its saved 45-path contract. Both implementation commits returned exit 0; main was
clean before publication. No history was rewritten.

Exactly one authorized command executed:
`GIT_TERMINAL_PROMPT=0 git -c core.askPass= push origin main`.
It returned **exit 128**: `fatal: could not read Username for 'https://github.com': terminal prompts disabled`.

**Phase 3 complete locally; GitHub publication remains blocked by HTTPS
authentication.** No retry, credential repair, force push, alternate publication
path or further remote check was attempted. Remote branch SHA/published file set
verification is unavailable and not claimed. A documentation-only follow-up
records the actual failure. Verified implementation and private runtime data remain
intact. The owned API/worker/production web continue at http://127.0.0.1:3000.
Next recommended major batch is Phase-4 reviewer ownership/version conflicts,
dependency inspection, reconciliation and audit replay; recommendation only.
**Phase 4 has not begun. Waiting for approval to begin Phase 4.**

## Phase-4 tested internal batches and completed local gate

P4-01/P4-02 extend existing review_cases, retain immutable actions, guard legacy
claimed-case mutations, append source/canonical corrections, invalidate material
eligibility and approvals, preserve supersession, and compensate cancellation.
P4-03 extends retained jobs with safe classified/bounded failures, operations-only
manual recovery, minimal health, bounded reconciliation and pinned digest replay.
P4-04 adds operational dashboard, server-filtered/paged queues and transactions,
typed reviewer/receipt inputs, timeline and permissioned private JSON/HTML/CSV.

Executed internal checkpoints: initial workflow 7 passed; expanded actual-document
workflow 10 passed; correction/cancellation/authority/reconciliation suite 12 passed
and one failure identifying a completed-generation increment, then targeted repair
1 passed. Final reliability/eligibility boundaries: 16 passed in 397.78s, exit 0.
The wider 69-case finance batch found one historical JSON contract regression;
restored historical response and its targeted immutability test passed. Intermediate
browser runs identified stale primary review selection, selector ambiguity, missing
await of persisted approval creation and a fixed-seed assumption beyond the bounded
list. Repairs preserve assertions against actual records and source evidence.
The final regression/build/UI inspection completed successfully as recorded below.

Benchmark: actual 100 computed fictional transactions in an isolated migrated
schema, disposed after measurement. Median queue 18.470 ms, detail 3.095 ms, audit
3.439 ms, dashboard 6.762 ms, assignment 46.968 ms, CSV generation 72.753 ms and
reconciliation 690.823 ms; one correction/reevaluation sample 631.204 ms and one
cancellation sample 49.628 ms. Warm local single-process samples, no production SLA.
EXPLAIN ANALYZE covers scoped queue/owner/audit/job predicates. Existing scoped
indexes and one ownership index suffice for this measured dataset; no speculative
index collection was added.

The approval reviewer rejected widening existing development identities. The safer
authorized setup creates separate scope-bound fictional operational, audit and
review-manager identities and leaves existing roles unchanged. No credential,
permission, driver/Docker or production infrastructure repair occurred.

Final self-review found that exhausted temporary preprocessing failures could enter
QUARANTINED instead of recoverable FAILED_FINAL. The worker now preserves transient
classification and the last successful stage. The actual PostgreSQL recovery test
passed (exit 0, 1 passed, 24.31s): three automatic timeouts, one authorized manual
cycle, restored preprocessing, one READY document and one page artifact. Permanent
corrupt input remains quarantined. The final 720-case regression includes this fix.
The final owned stack was restarted; minimal live/ready and the operations page
responded 200. An initial smoke used the unprefixed health URL and received 404;
the established `/api/v1/health/` routes passed without adding duplicate routes.

### Phase-4 final verification and exit

The fresh final command `.venv/bin/pytest -q` returned **exit 0: 720 passed,
1 upstream Starlette/httpx deprecation warning, 1452.86s (24m12s)**, zero failures
or skips. This is the complete final code, including the transient document recovery
fix; earlier interrupted runs are not passing gates. The ignored log is
`generated/reports/pytest-phase4-exit-final.txt`.

`npm --prefix apps/web run test:e2e` returned **exit 0: 27 passed, 1.6m**, zero
retries, against the real API/worker/production web. The final browser screenshots
were inspected for operational counts, dead-letter failure details, correction/
audit timeline and retained reports; laptop/mobile/error/empty/focus checks passed.
`npm --prefix apps/web run typecheck`, `run build` and `run generate:api` returned
exit 0. The independent server identity check returned exit 0, 1 passed.

`.venv/bin/alembic -c apps/api/alembic.ini current` and `check` returned exit 0:
`0006_workflow` head, no new upgrade operations. Fresh isolated database migration,
base downgrade/re-upgrade, constraints, immutable history, precision, RLS and
tenant boundaries pass in the full suite. `.venv/bin/python -m pip check` returned
exit 0. Original source, synthetic finance and extraction SHA-256 manifests passed
with exit 0; the working spec is byte-identical to the retained source. All five
prior migrations and both original finance evaluators remain unchanged.

The final local-link check found 124 resolving targets. Scope/ignore/credential-
signature review examined 43 intended changed files and found no private runtime
artifacts or detected credentials. `git diff --check` and staged whitespace checks
returned exit 0. This limited scan is not a production security certification.

P4-01, P4-02, P4-03 and P4-04 are complete locally. The specification exit is
verified: a reviewer resolves an exception while retaining its original decision,
and failure/retry/reconciliation tests produce no duplicate financial effects.
See [the final exit review](phase4_exit_review.md) and
[local operational runbook](runbooks/phase4-local.md). External enterprise VLM,
scanner, server-side PDF exports, real organization identity/policies/deployment
and production availability guarantees remain explicitly outside this gate.
T01–T42: 38 implemented/passing, 2 partial, 2 not implemented — Phase 5.

Local implementation commits are `c07e6ad` and `81b7c96`. The next task is Phase 5
only after separate approval. No Phase-5 implementation began.

### Phase-4 local commits and publication outcome

Coherent commits on main:

- `c07e6ad` — Add versioned review ownership and guarded operational recovery.
- `81b7c96` — Add accessible review operations and private report exports.
- `55a0d5d32f98afceabfa92029a972f36fadc1ffc` — Verify Phase 4 exit and document review recovery operations.

The branch and requested origin were verified; main was clean, with 43 intended
Phase-4 files changed from the retained Phase-3 baseline. Exactly one new Phase-4
push executed: `GIT_TERMINAL_PROMPT=0 git -c core.askPass= push -u origin main`.
It returned **exit 128**:

```text
fatal: could not read Username for 'https://github.com': terminal prompts disabled
```

**Phase 4 complete locally; GitHub publication remains blocked by HTTPS
authentication.** No push retry, credential repair, force push, alternate publication
or further remote check was attempted. Remote branch SHA and published file-set
verification are unavailable and not claimed. This documentation-only follow-up
records the observed outcome. The final owned API/worker/web are running at
http://127.0.0.1:3000. Stop before Phase 5; separate approval is required.

## P5-01–P5-05 continuous implementation record

| Batch | Behavior, files and verification |
|---|---|
| P5-01 | `app/risk/features.py`/`anomaly.py`: cutoff/current/version/currency leakage guards, median/MAD/cold starts, explicit missing operands and actual score direction. Initial pure batch: 22 passed, exit 0. Canonical/evaluation integration uses the original enqueue reference snapshot, cutoff ledger events and branch-specific actual source observations. |
| P5-02 | `app/risk/datasets.py`, `services/intelligence.py`, `db/risk_models.py`: immutable taxonomy adjudication with owner/version/source checks, stable PASS audits, connected temporal groups and synthetic representative gate. Core first batch: 33 passed, exit 0; expanded backend batch: 64 passed, exit 0. No correction or PASS routing became an automatic label. |
| P5-03 | Data inventory/gate, frozen schemas/manifests and reproducible offline run metadata; supervised requests persist SUPERVISED_DEFERRED and produce no model. Current statistical artifacts are private verified JSON, not learned weights or production-generalization evidence. Public contracts/model card live under `ml/`. |
| P5-04 | Separate combiner/report/feature factors plus `apps/web/src/app/intelligence.tsx`: actual high statistical score escalates PASS→REVIEW, actual score 0 cannot clear mandatory HOLD, required unavailable artifact/model remains null/explicit. Compatible retained replay is tested. No unsupported calibration, probability, SHAP or T31/T34 was manufactured. |
| P5-05 | Independent ML author/governor, append-only events/deployments, shadow prerequisite, explicit activation/rollback, configuration freshness and actual monitoring. Optimistic two-governor conflict has one accepted action and one 409. Manual offline proposal only; no auto-training or online learning. |

### Final verification commands and actual results

| Command/check | Exit and result |
|---|---|
| `.venv/bin/pytest -q apps/api/tests` | 0; 753 passed, one existing Starlette/httpx deprecation warning, 2637.19 s. Collected before the last five integration cases were added. |
| `.venv/bin/pytest -q apps/api/tests/test_risk_phase5.py apps/api/tests/integration/test_intelligence_phase5.py` (stable final code) | 0; 38 passed (22 pure + 16 PostgreSQL), one warning, 403.68 s. Includes all five newly collected cases and final outage status checks. |
| `.venv/bin/pytest -q apps/api/tests/integration/test_document_finance.py` | 0; 7 passed, one warning, 241.08 s. |
| `.venv/bin/pytest -q apps/api/tests/integration/test_document_finance.py -k real_document_to_finance` (final source checks) | 0; 2 passed, 5 deselected, one warning, 63.98 s. Actual PDF/receipt quality uses four correct critical source observations. |
| `.venv/bin/pytest --collect-only -q apps/api/tests` | 0; 758 collected; collection is not itself a passing execution. All current cases are covered by the full/final affected runs above. |
| `PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH" npm --prefix apps/web run test:e2e` | 0; 31 passed, 2.1 min. Core flows use actual backend; deliberate error/empty state tests inject only those UI responses. |
| Same npm command with `-- tests/intelligence.spec.ts` (stable final code) | 0; 4 passed, 20.6 s. Live adjudication, governance permissions/gate/shadow/activation/rollback/outage and responsive/error/empty flows; inspected screenshots. |
| `npm --prefix apps/web run typecheck` with bundled Node PATH | 0; TypeScript passes. |
| `npm --prefix apps/web run build` with bundled Node PATH | 0; production build passes. |
| `PYTHONPATH=apps/api .venv/bin/alembic -c apps/api/alembic.ini check` | 0; no new upgrade operations. Fresh migrated PostgreSQL schemas, scoped constraints, 61 forced-RLS business tables and immutable SQL writes verified by integration tests. Live head is 0008_intelligence_audit. |
| `.venv/bin/python -m pip check` | 0; no broken requirements. No new ML/model runtime dependency installed. |
| OpenAPI and public feature contract comparison against actual code | 0; exact matches. Generated TypeScript contract is retained. |
| `sha256sum -c` for original inputs, synthetic, extraction spike and documents_phase2 manifests; spec `cmp` | 0; all 9/23/11/15 hashes match and working spec is byte-identical to original. |
| `git diff --exit-code HEAD -- apps/api/app/rules apps/api/app/domain` | 0; deterministic rule/domain modules unchanged. |
| `.venv/bin/python scripts/benchmark/intelligence_phase5.py` | 0; owned temporary 10k synthetic schema, cutoff reproducibility assertion and real query plan. Query median/p95 328.732/351.310 ms; feature build 138.161/139.970 ms; score 0.001/0.006 ms. No classifier/generalization metrics. |
| Governed final development activation and fresh actual evaluation | 0; configuration 39 RULES_PLUS_ANOMALY/AVAILABLE, score 91.214299, REVIEW with ANOMALY_ESCALATION and all deterministic rule effects NONE. |

Failures were repaired before closure: early fixture monetary/source identity problems,
PASS audit constraint (new frozen migration), asynchronous browser notices/ownership
refresh, stale sidebar mode, and a test that wrongly expected a per-claim ratio
for a daily taxi allowance. The final taxi ratio remains explicitly missing; a real
supported per-night hotel case verifies a usable policy denominator. Branch-specific
source field names were corrected and retested with actual documents. Incompatible
intermediate development artifacts remain historical and unavailable; no retained
history was erased.

Next approved work: none. **Stop before Phase 6.** Representative supervised data
and pilot infrastructure require their own authorization. Publication is recorded
after the single authorized consolidated push; no credentials will be repaired.

### Phase-5 publication result

`GIT_TERMINAL_PROMPT=0 git -c core.askPass= push -u origin main` returned **exit 128**
after the complete local fallback gate and clean phase commits. Attempted SHA:
`6b84cd4f3bd0aee018aedd3793b99759e4006c34`. Safe error: `fatal: could not read Username for
'https://github.com': terminal prompts disabled`. No authentication repair, retry,
alternate transport, credential disclosure or force-push occurred. Remote branch
SHA and published file set cannot be verified after failed publication. A local
documentation-only commit records this external blocker; no verified code changed.

## Phase-6 approved continuous scope and verification plan

P6-01–P6-04 are authorized together. Goal: a clear Finance Workspace, separately authorized business Admin Console, deployable CPU control-plane definitions, governed delivery pipeline, actual local recovery/security/performance checks and final handoff. Expected files: existing web components/API/reference services, narrowly scoped authentication/configuration/release helpers, `infra/azure/`, `.github/workflows/`, CPU Dockerfiles, release tests, ADR and handoff documents. Preserve finance rules, reference/evaluation history and original fixtures.

Verification plan: meaningful PostgreSQL policy-version/authorization tests; real-backend browser finance/admin/document flow and viewport checks; contract tests for external deployment boundaries; Bicep compilation; full backend/browser/strict TypeScript/build, fresh migrations and drift, OpenAPI consistency, dependency/source/security checks; owned local restore and concurrency/performance exercises. No Azure provisioning without required inputs; no GPU work or supervised classifier/SHAP. The completed supported local results follow.

### P6-01 — Local infrastructure and operational boundaries complete

Files: `infra/azure/`, `deploy/`, `apps/api/app/core/{config,enterprise_identity,observability}.py`, `integrations/blob_storage.py`, database session and existing worker/storage service integration; `docs/adr/0014-enterprise-release-boundaries.md` and enterprise/failure/recovery runbooks. Bicep defines private CPU Container Apps/PostgreSQL/Blob/Key Vault/registry/DNS/logging and separate narrowly scoped identities. Entra RS256 server memberships, required TLS, managed-identity immutable private storage with remote hash verification and content-free telemetry are implemented. Development and enterprise configuration are explicit. Ordinary finance reviewers cannot read infrastructure health. No new business schema or finance-rule replacement.

Verification: both Bicep templates compile without warnings (0.47.16, exit 0); 12 pure signed-token/Blob/TLS cases and the real PostgreSQL enterprise submitter context pass in the final release suite. Live cloud resources, EasyAuth/API token exchange, Blob/egress/managed identities, monitoring acceptance and private network behavior are **DEFERRED_EXTERNAL**, not proved by mocks. Known inference runtime remains external; no driver/Docker repair.

### P6-02 — Delivery artifacts complete locally

Files: `.github/workflows/{validate,pilot}.yml`, CPU Dockerfiles/ignore rules, action pins and `scripts/release/{contracts,ci_database,deployment_gate,pilot_dispatch,check_artifacts,install_bicep}.py`. CI defines locked restore, lint/domain types, real-database tests, frontend tests/build, migrations/drift, generated contract checks, dependency/source/secret checks and separate CPU image artifact checksums. Protected manual pilot release requires private approvals, reviewed commit/parameter digest, exact target account/group/region, immutable image references and explicit migrations; rollback skips destructive DDL.

Verification: YAML/pins and 11 shell blocks pass, approval mismatches fail before migration/deployment, Bicep compiles and missing approval returns expected exit 1. Actual standalone web build/server health passes. Current Docker authorization prevents image builds; hosted CI/registry/staging/rollback and disposable hosted CI bootstrap are **DEFERRED_EXTERNAL**. No image digest, workflow success or Azure rollout is invented.

### P6-03 — Local security, integrity, performance and recovery complete

Files: `apps/api/tests/test_release_boundaries.py`, `tests/integration/test_release_phase6.py`, narrow existing workflow test updates, release scanner/restore/persistence helpers, benchmark scripts and security/performance runbooks. Four eight-way PostgreSQL batches verify budget, GRN, duplicate and shared-receipt admission with retry count stability. Actual on-behalf enterprise submission uses enabled server authority; disabling it yields a new HOLD and retains the prior report. Existing audit/tenant/evidence/approval/waiver/stale-write/cancellation/retry/reconciliation/replay controls remain covered.

Verification: full backend **777 passed, 2550.42 s**, final affected release suite **21 passed, 152.39 s**, unique current collection **779**; no failed/skipped cases. Counts are separate. Dependency integrity/known-vulnerability checks and Gitleaks zero-finding/redacted positive probe pass. A disposable restore verifies 62 tables/61 forced-RLS, 362 transactions, 392 reports, 5,047 audit-chain entries and 263 object hashes in **167.846 s**, source unchanged. Real document report/version/evaluation survives API/worker/web restart. Actual machine/scope/samples/timings and unmeasured targets are in [performance](performance_phase6.md). No penetration test, cloud RTO/RPO or VLM throughput is claimed.

### P6-04 — Finance/Admin demonstrations and handoff complete

Files: existing web workspace/documents/finance controls, new `admin.tsx`/`business-facts.tsx`/minimal health, source/case business forms, strict generated contract, release and loaded viewport browser cases; handoff-quality README, architecture/data flow, capability matrix, exit review and runbooks. Finance navigation leads with upload/source verification, plain unresolved result/next actions, evidence/review/report; internal IDs/rule JSON are optional. Read-only observed fields use source corrections; business reference mapping/revisions use forms. Separate typed Admin drafts retain old versions, actor/reason/time and effective dates; no arbitrary SQL/code/set-PASS or policy-admin vendor/budget bypass.

Verification: actual-backend **36 browser tests passed, 2.7 min**, no retries; strict TypeScript/normal production build pass. Loaded Finance/Admin views inspected at 1280/1024/390 with keyboard/labels/focus and existing error/loading/empty tests. A real PDF goes through upload/process/verification/canonical/HOLD/audit/report/reload. Future hotel 8,000→9,000 change retains reports and integration verifies both effective-date sides and 409 conflict. Original team pack/ZIP/spec and 9/23/11/15 manifest entries pass; historical Phase-0–5 exits and finance rule/domain modules remain unchanged.

### Final Phase-6 command record and disposition

The [exit review](phase6_exit_review.md) records exact full/focused/backend/browser/static/migration/contract/security/recovery commands and AC01–AC20. Original T01–T42 scenario text remains preserved: **39 complete, T30 partial, T31/T34 data-deferred**. Statistical anomaly is measured; no classifier, calibrated probability or SHAP is manufactured. AC17 is data-deferred and AC20 requires an actual deployed pilot. Other ACs satisfy the documented supported local scope, including explicit unmeasured performance targets.

**PHASE 6 COMPLETE LOCALLY — CLOUD PROVISIONING DEFERRED EXTERNAL INPUT.** No institutional data, live VLM, GPU provisioning, cloud spending, production-readiness certification or payments. Next task: **none; STOP after delivery**. External gates require separately supplied/approved infrastructure, policies, identities and representative labels. Publication result is recorded below after exactly one authorized normal main push.

### Phase-6 publication result

Coherent local commits: `2999d9d` release/CI artifacts, `a838450` verified application/enterprise/Finance/Admin/tests and `74f9c52` final handoff/coverage/runbooks. The complete local gate and clean working tree preceded publication. Exactly one `GIT_TERMINAL_PROMPT=0 git -c core.askPass= push origin main` attempted SHA **`74f9c529d666440df8a39d51978cad6c15b1f2c7`** and returned **exit 128**. Safe error: `fatal: could not read Username for 'https://github.com': terminal prompts disabled`.

**LOCAL DELIVERY COMPLETE — GITHUB PUBLICATION BLOCKED BY AUTHENTICATION.** No credential repair, retry, alternate transport, force-push or remote-history change was performed. The remote branch SHA/published file set cannot be verified after failed authentication. A final documentation-only commit records this outcome; verified application code remains `a838450`. Final HEAD is that local documentation commit, available with `git rev-parse HEAD` and in the delivery report. The owned loopback application remains available at http://127.0.0.1:3000. Stop; no further phase or cloud/GPU provisioning.

### Subsequent user-authorized publication request

After Phase-6 delivery, the user explicitly requested another `git push -u origin main` of the whole codebase. Fresh inspection verified the requested `Vansh-A1/microsoft_inovate` origin, clean `main`, 310 tracked files and HEAD `12d87c511a37954fb91cb5801608e9d8a2484592`. Automatic review initially rejected the action under the earlier phase restriction, then accepted the same ordinary push with the latest user authorization explained. The actual command `GIT_TERMINAL_PROMPT=0 git -c core.askPass= push -u origin main` returned **exit 128**: `fatal: could not read Username for 'https://github.com': terminal prompts disabled`. Authentication remains unavailable; no credentials were changed, further push attempted, history rewritten or remote publication claimed. This documentation-only checkpoint records the failure and preserves all application commits.

### Token-authorized publication — workflow permission required

The user subsequently supplied a token and explicitly authorized authentication/publication. The ordinary main push of `266377ad78afe6d48464b3d002037e7d21dc8b90` authenticated using Git's non-echoing password prompt with credential helpers disabled; no secret was written to a file, remote URL or command argument. GitHub rejected the ref update with **exit 1**, because updating `.github/workflows/pilot.yml` requires the token's `workflow` scope. The complete CI/code/history is preserved; workflows were not removed to evade the permission boundary and no force-push or additional authenticated attempt occurred. Publication requires an authorized credential with workflow write permission. Token values are omitted from this record.

### Connected GitHub plugin verification

At the user's explicit request to publish through the plugin, its authenticated account is verified as `Vansh-A1`; repository metadata reports the user's push/admin rights, and Plugin Management confirms GitHub is installed/enabled. The actual connected-account contents API write of the unchanged `.github/workflows/pilot.yml` returns **GitHub 403: Resource not accessible by integration**. No file or branch was created. A separate read-only credential check returns HTTP 200 and current OAuth scope **`repo` only**, confirming that `workflow` has not been granted. No other Git credential/helper is configured locally. The full source/history remains committed; publication is blocked by the credential/integration permission boundary, not a code/build failure. The user is asked to enable the required workflow permission on GitHub; no further write, permission bypass or secret storage occurs.

### Publication resolved after user-confirmed permission update

The user replied **Done** after enabling the required workflow permission, authorizing the requested complete publication. Fresh source/security checks pass (296 text files; Gitleaks zero findings plus positive redacted probe). Normal `git push -u origin main`, with the credential entered at a non-echoing prompt and helpers disabled, returned **exit 0** and created remote `main`, preserving the full existing history. No token was placed in a command argument, repository file, remote URL or credential helper; no force-push or workflow removal.

Independent `git ls-remote` verified **`3bc70198b14d5c21d8fe9a05456e3334836b75d5`**. GitHub's recursive tree at that immutable commit matched **all 310 local tracked file modes/blob hashes**, including `.github/workflows/pilot.yml` and `validate.yml`; the local working tree was clean. **COMPLETE SOURCE/HISTORY PUBLISHED TO Vansh-A1/microsoft_inovate/main.** This documentation-only follow-up updates the README/exit review to avoid a stale blocked-publication claim and is published as part of the same handoff. Actual hosted CI, cloud provisioning and external/data gates remain unverified/deferred. No new phase or code behavior change.
