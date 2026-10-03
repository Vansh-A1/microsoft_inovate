# microsoft_inovate

Accounts-Payable Exception Assistant · Microsoft Innovate 2026 · AI BATTALION 1 · Team ID 152

The assistant screens vendor invoices and employee expense claims against verified evidence, versioned finance rules, reference records, budgets, and approvals. Every finding must explain which control applies and which source or matched record supports it.

## Development status

**Phase 3 complete locally — finance matching and controls.** Versioned reference activation, cumulative PO/contract/delivery matching, duplicate comparisons, receipt allocations, append-only budgets and authenticated approval/waiver actions extend the preserved document pipeline. See [progress](docs/progress.md), the [Phase-3 runbook](docs/runbooks/phase3-local.md) and [exit review](docs/phase3_exit_review.md) for actual gates and limitations.

The original Phase-0 contracts, fixture adapters, synthetic corpora and Phase-1 pure finance engine remain intact. **STRUCTURED_SYNTHETIC** and separate P0 **FIXTURE** remain available; actual document runs identify **NATIVE_TEXT / LOCAL_OCR** and source-derived reports **DOCUMENT_DERIVED**. Document facts require explicit human source verification; unresolved critical fields cannot PASS. Finance risk is **RULES_ONLY / NOT_CONFIGURED**, with no score. Real TypeLLM/SGLang/VLM execution remains deferred under the recorded infrastructure gate; its remote adapter boundary is implemented and contract-tested. No GPU configuration change, VLM download, payment execution or Phase-4 work was performed.

The seeded demos compute clean vendor PASS, paid duplicate HOLD, clean employee PASS, daily meal REVIEW and missing approval HOLD. Ordinary submissions cannot assert approval authority; new examples commonly HOLD until a trusted chain exists. This is a synthetic local development product, not a production pilot.

Screening terminology:

- **PASS:** eligible under the configured screening and approval policy at the recorded snapshot; it does not mean paid.
- **REVIEW:** uncertainty, a correction, or judgment needs human examination.
- **HOLD:** a mandatory control or condition must be resolved before eligibility.

Processing status and human review/approval status are separate from these screening decisions.

## Architecture

The intended CPU-friendly control plane contains the Next.js/TypeScript client, FastAPI/Pydantic API, PostgreSQL, deterministic Python finance rules, approvals, budgets, review/audit/reporting and durable jobs/outbox. A separate shared enterprise inference plane contains preprocessing/router, TypeLLM, compatible VLM, SGLang and GPU workers/caches. **Finance-user laptops do not require GPU/VLM runtime.** They need supported browser/client access; no CUDA, weights, TypeLLM, SGLang or GPU Docker.

The [accepted inference design](docs/inference_architecture.md) uses reliable native text → cheap structured extraction → small VLM if needed → stronger fallback if needed → unresolved facts/human review. It supports bounded actual pages/crops, persistent resident models, safe scoped caching, supported batching, async jobs and independently scaled inference workers; autoscaling and quantization are later benchmarked options. Neither the router nor the VLM decides finance PASS/REVIEW/HOLD. Money remains raw string → trusted normalization → Decimal/currency, with honest uncertainty and no invented source boxes.

Initial Phase-1 finance-risk mode is [RULES_ONLY](docs/adr/0007-rules-only-finance-risk-baseline.md): no ML risk score or fake zero risk. Document-extraction VLM is a separate concern. The CPU application services and actual native/OCR extraction are implemented; shared VLM runtime execution remains deferred.

## Current repository layout

```text
.
├── README.md
├── AGENTS.md
├── .gitignore
├── pytest.ini
├── apps/api/
│   ├── app/domain/                 # states, Money/currency, evidence, extraction contracts
│   ├── app/extraction/             # fixture, native/OCR and remote TypeLLM boundaries
│   ├── app/documents/              # bounded processing, typed limits, normalization
│   ├── app/core, db, schemas/       # trusted context, relational persistence, intake
│   ├── app/rules, services/         # pure controls, worker, reports, imports
│   ├── migrations/                 # five versioned PostgreSQL migrations
│   └── tests/                      # original 488 tests plus rules and PostgreSQL integration
├── apps/web/                       # Next.js client, private API proxy, Playwright tests
├── packages/api-client/            # generated OpenAPI contract
├── data/
│   ├── synthetic/                 # reference JSON, README and fixture checksums
│   ├── golden_cases/              # vendor/employee finance expectations and manifest
│   ├── extraction_spike/          # preserved structured replay corpus
│   ├── documents_phase2/          # actual synthetic PDF/PNG/JPEG and independent ground truth
│   └── finance_phase3/            # additive reference catalog and 200 unverified scale inputs
├── scripts/benchmark/extraction_spike.py
├── scripts/dev/, scripts/seed/      # isolated bootstrap, supervisor, trusted demo seed
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
│   └── adr/                       # ADR-0001–0011
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

## Run locally

See the [Phase-1 setup](docs/runbooks/phase1-local.md), [Phase-2 document runbook](docs/runbooks/phase2-local.md) and [Phase-3 finance runbook](docs/runbooks/phase3-local.md) for prerequisites, private identities, source verification, imports, tests and limits. The automated tool bootstrap targets Ubuntu 24.04 x86_64 and runs as an ordinary user:

```bash
python3 scripts/dev/bootstrap.py
.venv/bin/alembic -c apps/api/alembic.ini upgrade head
.venv/bin/python scripts/seed/phase1.py
.venv/bin/python scripts/dev/setup_ocr.py
.venv/bin/python scripts/dev/setup_finance_identities.py
export PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH"
npm run --prefix apps/web build
.venv/bin/python scripts/dev/run.py
```

Open [AP Review Desk](http://127.0.0.1:3000). API docs: [OpenAPI](http://127.0.0.1:8000/docs). All three application processes bind loopback; PostgreSQL runs on port 55432. Credentials remain in ignored 0600 private files. The application role cannot bypass forced row-level tenant/entity policies. The Next proxy injects the trusted development token server-side; request bodies cannot supply scope, role, approval or outcome authority. This is not production SSO.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
npm run --prefix apps/web typecheck
PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright" npm exec --prefix apps/web -- playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright" npm run --prefix apps/web test:e2e
sha256sum -c docs/source_inputs.sha256
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
sha256sum -c data/documents_phase2/fixtures.sha256
.venv/bin/python scripts/benchmark/documents_phase2.py
python3 scripts/benchmark/extraction_spike.py --dataset data/extraction_spike --output generated/reports/extraction-fixture.json
```

The PostgreSQL integration suite uses separate migrated test schemas. Browser tests use the running application and retain synthetic records. CSV/XLSX supports the existing `transaction_json` column and explicit column mapping with retained raw/parsed cell evidence. Invalid rows and formulas remain visible; commit queues valid rows. Actual receipt links require stored document UUIDs. Case detail provides ordered approval, duplicate resolution, authorized receipt share and explicit waiver actions; the server checks configured identity, authority and current version. Source corrections append canonical versions and evaluations; reports remain immutable after supersession. Original files and derived previews stay private outside Git.

The harness replays structured responses, compares each critical field, preserves abstentions, and measures row coverage/value agreement and source-locator availability. Its generated report is ignored by Git. Perfect fixture agreement is expected by construction and says nothing about visual extraction or production accuracy; absent boxes/latency remain unavailable. See the extraction dataset README for denominators and limitations.

The root `pytest.ini` supplies test discovery and import paths. Python dependencies and npm packages are locked and installed locally. The original standard-library domain/extraction modules were not rewritten. The [coverage tracker](docs/test_coverage.md) separates implemented supported scenarios from partial and deferred later-phase cases; synthetic tests do not establish visual accuracy, company-policy correctness or production readiness.

Repository: [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate). The single authorized Phase-3 normal main push also failed HTTPS authentication (exit 128). Phase 3 is complete locally; publication remains blocked. Verified commits are preserved, with no retry or credential repair. See progress for the actual publication outcome; remote SHA/file-set verification is unavailable.
