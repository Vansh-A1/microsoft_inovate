# microsoft_inovate

Accounts-Payable Exception Assistant · Microsoft Innovate 2026 · AI BATTALION 1 · Team ID 152

The planned assistant screens vendor invoices and employee expense claims against verified evidence, versioned finance rules, reference records, budgets, and approvals. Every finding must explain which control applies and which source or matched record supports it.

## Development status

**Implementation in progress: Phase 0 — Contracts and feasibility.** P0-01 established the local repository/documentation baseline; GitHub publication remains blocked by authentication. P0-02 adds tested, framework-independent state, Money/currency, and evidence contracts. P0-03 adds 38 synthetic root references and ten golden finance cases. P0-04A adds extraction contracts, deterministic fixture response replay, ten separately annotated structured extraction cases, and a comparison harness. P0-04B completes official-source research and a gated runtime plan: the recorded image-tested checkpoint exceeds local VRAM, CUDA 13 needs a supported newer driver, and Docker access is blocked. P0-04C1 rechecked prerequisites and stopped at BLOCKED_DRIVER plus Docker access denial before any downloads. Parent P0-04 remains IN PROGRESS; text/image smoke, real provider execution and P0-04C2 have not started. All T01–T42 business behavior remains NOT IMPLEMENTED. No API server, frontend, database, worker, finance rules, or model exists yet. No payment execution exists or is in the initial scope.

Screening terminology:

- **PASS:** eligible under the configured screening and approval policy at the recorded snapshot; it does not mean paid.
- **REVIEW:** uncertainty, a correction, or judgment needs human examination.
- **HOLD:** a mandatory control or condition must be resolved before eligibility.

Processing status and human review/approval status are separate from these screening decisions.

## Planned architecture

The specification proposes a Next.js/TypeScript reviewer workspace, a FastAPI/Pydantic backend, PostgreSQL persistence, and separate workers sharing deterministic Python finance logic. Local storage and fixture extraction are the development defaults; Azure deployment and verified TypeLLM/VLM extraction are later work. Optional ML can escalate a case to REVIEW, but cannot clear mandatory finance controls.

The intended flow is intake → extraction/normalization → validation → branch and shared controls → immutable evaluation and evidence report → authorized human review. Monetary calculations use Decimal and explicit currencies.

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
│   ├── source_inputs.sha256
│   └── adr/0001-repository-and-specification-authority.md
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

The `docs/` specification is the implementation reference, copied byte-for-byte from the preserved source pack. The original folder and ZIP are intentionally version controlled as project inputs. The ADR explains their relationship; do not edit the originals or silently diverge from the specification.

## Setup status

There is no runnable application, project dependency manifest, startup command, or migration. Tests use the existing Python/pytest environment; no dependencies were installed in P0-01–P0-04B. Production modules and fixture validation use the Python standard library and existing domain contracts. From the repository root:

```bash
python3 -m pytest apps/api/tests/unit/domain -q
python3 -m pytest apps/api/tests/fixtures -q
python3 -m pytest apps/api/tests/unit/extraction -q
python3 -m pytest -q
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
python3 scripts/benchmark/extraction_spike.py --dataset data/extraction_spike --output generated/reports/extraction-fixture.json
```

The harness replays structured responses, compares each critical field, preserves abstentions, and measures row coverage/value agreement and source-locator availability. Its generated report is ignored by Git. Perfect fixture agreement is expected by construction and says nothing about visual extraction or production accuracy; absent boxes/latency remain unavailable. See the extraction dataset README for denominators and limitations.

The root `pytest.ini` supplies test discovery and the import path; no shell `PYTHONPATH` override or package installation is required. Tests are verified on Python 3.13.11. The source avoids features newer than Python 3.10, but other interpreter versions have not been runtime-tested. Environment observations and missing prerequisites are recorded in the assumption register. Each next bounded task requires approval; moving to another phase also requires a verified phase exit review.

Repository: [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate).

The initial verified documentation baseline is authorized for publication to `main`. After this baseline, consolidate local task commits and push only when the entire phase has been completed, verified, and approved, unless the user explicitly directs otherwise. Never force-push without explicit authorization.
