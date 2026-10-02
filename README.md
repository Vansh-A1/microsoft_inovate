# microsoft_inovate

Accounts-Payable Exception Assistant · Microsoft Innovate 2026 · AI BATTALION 1 · Team ID 152

The planned assistant screens vendor invoices and employee expense claims against verified evidence, versioned finance rules, reference records, budgets, and approvals. Every finding must explain which control applies and which source or matched record supports it.

## Development status

**Implementation in progress: Phase 0 — Contracts and feasibility.** P0-01 established the local repository/documentation baseline; GitHub publication remains blocked by authentication. P0-02 adds tested, framework-independent state, Money/currency, and evidence contracts. No API server, frontend, database, worker, extraction adapter, finance rules, or model exists yet. This is not a production-ready system. No payment execution exists or is in the initial scope.

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
│   ├── app/domain/                 # states, Money/currency, evidence value types
│   └── tests/unit/domain/          # domain unit and invariant tests
├── docs/
│   ├── AP_Exception_Assistant_Codex_Spec.md
│   ├── progress.md
│   ├── assumptions.md
│   ├── data_dictionary.md
│   ├── test_coverage.md
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

The `docs/` specification is the implementation reference, copied byte-for-byte from the preserved source pack. The original folder and ZIP are intentionally version controlled as project inputs. The ADR explains their relationship; do not edit the originals or silently diverge from the specification.

## Setup status

There is no runnable application, project dependency manifest, startup command, or migration. Domain tests use the existing Python/pytest environment; no dependencies were installed in P0-01 or P0-02. Production modules use only the Python standard library. From the repository root:

```bash
python3 -m pytest apps/api/tests/unit/domain -q
python3 -m pytest -q
```

The root `pytest.ini` supplies test discovery and the import path; no shell `PYTHONPATH` override or package installation is required. Tests are verified on Python 3.13.11. The source avoids features newer than Python 3.10, but other interpreter versions have not been runtime-tested. Environment observations and missing prerequisites are recorded in the assumption register. Each next bounded task requires approval; moving to another phase also requires a verified phase exit review.

Repository: [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate).

The initial verified documentation baseline is authorized for publication to `main`. After this baseline, consolidate local task commits and push only when the entire phase has been completed, verified, and approved, unless the user explicitly directs otherwise. Never force-push without explicit authorization.
