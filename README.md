# microsoft_inovate

Accounts-Payable Exception Assistant · Microsoft Innovate 2026 · AI BATTALION 1 · Team ID 152

The planned assistant screens vendor invoices and employee expense claims against verified evidence, versioned finance rules, reference records, budgets, and approvals. Every finding must explain which control applies and which source or matched record supports it.

## Development status

**PHASE 0 COMPLETE — Contracts and feasibility, with explicit external-runtime deferral.** P0-01–P0-03 establish the local repository, tested Money/state/evidence contracts and reproducible synthetic finance fixtures. P0-04 provides the replaceable extraction contract, verified deterministic fixture adapter, ten structured extraction cases, comparison harness, official-source research and observed runtime prerequisite gate. P0-05 consolidates compatibility findings; P0-06 records identity, effective-policy, durable-job/private-storage, RULES_ONLY risk and optimized enterprise-inference decisions. See the [formal exit review](docs/phase0_exit_review.md).

Real TypeLLM/VLM execution is **DEFERRED — INFRASTRUCTURE PREREQUISITE**: observed driver 550.120 does not meet the proposed CUDA 13 >=580 prerequisite, Docker daemon access is denied, and GPU passthrough is unverified. No model/runtime was installed or downloaded; actual image quality, latency and VRAM remain unavailable. Research pins are not production-approved pins. The development extraction implementation is the verified fixture adapter.

All T01–T42 business behavior remains **NOT IMPLEMENTED**. There is no API server, frontend, database, durable worker, finance rule engine or trained risk model. Architecture acceptance is not service implementation. Phase 1 has not started; Git publication outcome is recorded in [progress](docs/progress.md). No payment execution exists or is in the initial scope.

Screening terminology:

- **PASS:** eligible under the configured screening and approval policy at the recorded snapshot; it does not mean paid.
- **REVIEW:** uncertainty, a correction, or judgment needs human examination.
- **HOLD:** a mandatory control or condition must be resolved before eligibility.

Processing status and human review/approval status are separate from these screening decisions.

## Planned architecture

The intended CPU-friendly control plane contains the Next.js/TypeScript client, FastAPI/Pydantic API, PostgreSQL, deterministic Python finance rules, approvals, budgets, review/audit/reporting and durable jobs/outbox. A separate shared enterprise inference plane contains preprocessing/router, TypeLLM, compatible VLM, SGLang and GPU workers/caches. **Finance-user laptops do not require GPU/VLM runtime.** They need supported browser/client access; no CUDA, weights, TypeLLM, SGLang or GPU Docker.

The [accepted inference design](docs/inference_architecture.md) uses reliable native text → cheap structured extraction → small VLM if needed → stronger fallback if needed → unresolved facts/human review. It supports bounded actual pages/crops, persistent resident models, safe scoped caching, supported batching, async jobs and independently scaled inference workers; autoscaling and quantization are later benchmarked options. Neither the router nor the VLM decides finance PASS/REVIEW/HOLD. Money remains raw string → trusted normalization → Decimal/currency, with honest uncertainty and no invented source boxes.

Initial Phase-1 finance-risk mode is [RULES_ONLY](docs/adr/0007-rules-only-finance-risk-baseline.md): no ML risk score or fake zero risk. Document-extraction VLM is a separate concern. These are accepted designs; application services and live extraction remain future implementation.

## Current repository layout

```text
.
├── README.md
├── AGENTS.md
├── .gitignore
├── pytest.ini
├── apps/api/
│   ├── app/domain/                 # states, Money/currency, evidence, extraction contracts
│   ├── app/extraction/             # Protocol, fixture adapter, synthetic comparison
│   └── tests/                      # domain, fixture integrity, extraction tests
├── data/
│   ├── synthetic/                 # reference JSON, README and fixture checksums
│   ├── golden_cases/              # vendor/employee finance expectations and manifest
│   └── extraction_spike/          # structured inputs/annotations, responses, own checksums
├── scripts/benchmark/extraction_spike.py
├── docs/
│   ├── AP_Exception_Assistant_Codex_Spec.md
│   ├── progress.md
│   ├── assumptions.md
│   ├── data_dictionary.md
│   ├── test_coverage.md
│   ├── extraction_compatibility.md
│   ├── typellm_spike_plan.md
│   ├── inference_architecture.md
│   ├── phase0_exit_review.md
│   ├── source_inputs.sha256
│   └── adr/                       # ADR-0001–0008
├── AP_Exception_Assistant_6_Person_Team_Pack/
│   ├── AP_Exception_Assistant_Codex_Spec.md
│   ├── AP_Exception_Assistant_6_Person_Work_Plan.md
│   └── AP_Team_Task_Briefs/
└── AP_Exception_Assistant_6_Person_Team_Pack.zip
```

## Documentation

- [Implementation specification](docs/AP_Exception_Assistant_Codex_Spec.md)
- [Repository working rules](AGENTS.md)
- [Progress and verified results](docs/progress.md)
- [Assumptions and external inputs](docs/assumptions.md)
- [Baseline domain glossary](docs/data_dictionary.md)
- [T01–T42 implementation coverage](docs/test_coverage.md)
- [Repository and specification authority decision](docs/adr/0001-repository-and-specification-authority.md)
- [Supplied six-person work plan](AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_6_Person_Work_Plan.md)
- [Original-input checksums](docs/source_inputs.sha256)
- [Synthetic reference inventory and validation](data/synthetic/README.md)
- [Golden case inventory and expectations](data/golden_cases/README.md)
- [Extraction cases and harness](data/extraction_spike/README.md)
- [Verified-source provider checklist and unresolved runtime gates](docs/extraction_compatibility.md)
- [Exact conditional TypeLLM/SGLang experiment plan](docs/typellm_spike_plan.md)
- [String-only money extraction boundary](docs/adr/0002-extraction-money-and-provider-boundary.md)
- [Optimized enterprise inference and deployment profiles](docs/inference_architecture.md)
- [Phase-0 exit criteria, acceptance review and deferrals](docs/phase0_exit_review.md)
- [Identity](docs/adr/0003-trusted-identity-and-record-keys.md), [policy selection](docs/adr/0004-effective-versioned-policy-selection.md), [durable jobs](docs/adr/0005-durable-jobs-and-isolated-workers.md), [private storage](docs/adr/0006-private-original-and-derived-storage.md), [risk mode](docs/adr/0007-rules-only-finance-risk-baseline.md), [inference ADR](docs/adr/0008-optimized-enterprise-inference.md)

The `docs/` specification is the implementation reference, copied byte-for-byte from the preserved source pack. The original folder and ZIP are intentionally version controlled as project inputs. The ADR explains their relationship; do not edit the originals or silently diverge from the specification.

## Setup status

There is no runnable application, project dependency manifest, startup command, or migration. Tests use the existing Python/pytest environment; no dependencies were installed in Phase 0. Production modules and fixture validation use the Python standard library and existing domain contracts. From the repository root:

```bash
python3 -m pytest apps/api/tests/unit/domain -q
python3 -m pytest apps/api/tests/fixtures -q
python3 -m pytest apps/api/tests/unit/extraction -q
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider
sha256sum -c docs/source_inputs.sha256
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
python3 scripts/benchmark/extraction_spike.py --dataset data/extraction_spike --output generated/reports/extraction-fixture.json
```

The harness replays structured responses, compares each critical field, preserves abstentions, and measures row coverage/value agreement and source-locator availability. Its generated report is ignored by Git. Perfect fixture agreement is expected by construction and says nothing about visual extraction or production accuracy; absent boxes/latency remain unavailable. See the extraction dataset README for denominators and limitations.

The root `pytest.ini` supplies test discovery and the import path; no shell `PYTHONPATH` override or package installation is required. Tests are verified on Python 3.13.11. The source avoids features newer than Python 3.10, but other interpreter versions have not been runtime-tested. Environment observations and missing prerequisites are recorded in the assumption register. The completed Phase-0 review permits the explicit external-runtime deferral. The next phase requires new approval; this closure creates no Phase-1 scaffold.

Repository: [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate).

The latest approval authorizes exactly one consolidated Phase-0 push to `main` after verification. If Git authentication fails, preserve clean local commits and report the blocker without credential repair or retry. Future phase pushes follow the user-approved publication policy. Never force-push without explicit authorization.
