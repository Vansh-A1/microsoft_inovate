# Implementation progress

## Project status

- Session date: 2026-10-02–03 (Asia/Kolkata).
- Current phase: **PHASE 0 COMPLETE — Contracts and feasibility**, with explicit external-runtime deferral.
- Current task: **Phase-0 complete locally; publication BLOCKED by Git authentication; waiting for Phase-1 approval**.
- P0-01: **COMPLETE LOCALLY**; the single consolidated phase push failed authentication; remote publication remains blocked.
- P0-02: **COMPLETE**; tested Money/currency, states and evidence foundation.
- P0-03: **COMPLETE**; reproducible synthetic references and independent golden expectations.
- P0-04: **CLOSED WITH EXTERNAL RUNTIME DEFERRAL**; fixture/contracts/research verified, real inference not executed.
- P0-05: **COMPLETE FEASIBILITY CONSOLIDATION**; final compatibility matrix, research pins and honest unverified/blocked/deferred limitations.
- P0-06: **COMPLETE DESIGN DECISIONS**; identity, effective policy, durable jobs, private storage, RULES_ONLY risk and optimized shared inference.
- Real runtime: **BLOCKED_EXTERNAL_PREREQUISITE**; observed BLOCKED_DRIVER and BLOCKED_DOCKER_ACCESS, ENVIRONMENT_FAILURE, IMAGE_PATH_NOT_RUN.
- Development extraction: **VERIFIED FIXTURE ADAPTER**; enterprise target **OPTIMIZED SHARED VLM INFERENCE SERVICE**.
- Phase 1: **NOT STARTED**; separate user approval required.

The [formal exit review](phase0_exit_review.md) records the explicit runtime qualification and full-product acceptance limits. [T01–T42 coverage](test_coverage.md) remains 42 NOT IMPLEMENTED. Historical work records below describe the approval/status at each checkpoint; this current disposition supersedes their prior stop/parent-incomplete statements. No original record or specification is rewritten to suggest a passed real spike.

## Phase checklist

- [x] Phase 0 — Contracts and feasibility (local exit criteria satisfied; real runtime explicitly deferred, publication separately reported).
- [ ] Phase 1 — Rules-first vertical slice for both branches.
- [ ] Phase 2 — Real document ingestion and extraction.
- [ ] Phase 3 — Complete finance matching and controls.
- [ ] Phase 4 — Human workflow and operational reliability.
- [ ] Phase 5 — Measured ML and explanations.
- [ ] Phase 6 — Azure pilot and handoff.

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
