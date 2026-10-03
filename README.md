# microsoft_inovate

Accounts-Payable Exception Assistant · Microsoft Innovate 2026 · AI BATTALION 1 · Team ID 152

The application screens vendor invoices and employee claims using source evidence, versioned finance rules, matching, approvals and budgets. It produces **PASS / REVIEW / HOLD**, preserves the original decision and shows the next action. It executes no payments.

Phase 6 delivers the local application and release/handoff artifacts under an explicit external-infrastructure fallback. This is a **synthetic development demonstration**, not a deployed production pilot. Final verified results and acceptance dispositions are in the [Phase-6 exit review](docs/phase6_exit_review.md); [capability matrix](docs/release_matrix.md) distinguishes completed work from actual cloud/VLM/data gates.

## Finance Workspace

Use an ordinary browser: **Upload invoice or receipt → Processing → inspect source facts → verify/map business references → Result**. The default screen leads with unresolved checks and plain next actions. Source previews, corrections, ownership, approvals, queue, audit and report are available; rule IDs/full facts are expandable details. Both vendor and employee records persist. A missing/ambiguous critical fact, missing dependency, stale approval or insufficient capacity cannot silently PASS.

PASS means current screening eligibility at the recorded snapshot, not paid. REVIEW needs uncertainty/judgment resolved. HOLD blocks eligibility until a mandatory condition is resolved. Processing, human ownership and approvals are separate states. Historical reports remain immutable after correction, cancellation or supersession.

## Admin Console

Administration has separate navigation and permissions. Typed business forms edit supported allowance/effective-date/approval-band/delegation/master fields through validated drafts and new reference versions; budgets use audited ledger adjustments. A policy administrator cannot activate vendor/budget masters. The future hotel allowance demonstration retains 8,000 and creates 9,000 from 2026-11-01, with actor/reason/time. Model author/governor and operational health permissions remain separate. There is no arbitrary code/SQL or set-PASS control.

## Architecture and modes

[Architecture](docs/architecture.md) and [data flow](docs/data_flow.md) explain the CPU Next.js/FastAPI/PostgreSQL/private storage/leased worker application and separate future enterprise inference plane. Finance laptops need no GPU/CUDA/weights/TypeLLM/SGLang.

| Area | Current status |
|---|---|
| Deterministic finance | 28 controls; Decimal/currency, source coverage, vendor/employee, duplicates, PO/contract/GRN/service, policy, offsets/shared receipts, budgets and approvals. |
| Actual documents | PyMuPDF native text/pages and local Tesseract CPU OCR; bounded parsing, preserved originals, uncertainty and source-linked human verification. |
| TypeLLM | Provider-independent remote adapter implemented/contract-tested; money is extracted as strings. |
| VLM / SGLang | DEFERRED_EXTERNAL: suitable separately approved runtime absent; no GPU/driver/Docker repairs or weights download. |
| Intelligence | RULES_ONLY (NOT_CONFIGURED/null score) or governed RULES_PLUS_ANOMALY with 20 PIT features and transparent statistical factors. Statistical scores are not probabilities. |
| Classifier / SHAP | DEFERRED_DATA: representative independently adjudicated labels required; no fabricated training/metrics/attribution. |
| Azure | Private CPU Bicep/CI/deployment definitions locally validated; provisioning, image builds, hosted SSO/Blob and pilot recovery/rollback remain externally gated. |

The anomaly layer may escalate PASS to REVIEW and cannot clear mandatory HOLD. Shadow scoring, feedback/datasets, registry, explicit promotion/rollback and monitoring remain separate from VLM extraction. Historical code-bound artifacts remain unchanged; incompatible artifacts require a newly governed compatible candidate.

## Local setup

The supplied ordinary-user bootstrap targets Ubuntu 24.04 x86_64 with Python 3.13.11, Node 24.21.0 and PostgreSQL 16.15. Language dependencies are locked. These established setup/start commands were validated for this project; preserve an existing private database/settings rather than reset them:

```bash
python3 scripts/dev/bootstrap.py
.venv/bin/alembic -c apps/api/alembic.ini upgrade head
.venv/bin/python scripts/seed/phase1.py
.venv/bin/python scripts/dev/setup_ocr.py
.venv/bin/python scripts/dev/setup_finance_identities.py
.venv/bin/python scripts/dev/setup_workflow_identities.py
.venv/bin/python scripts/dev/setup_intelligence_identities.py
.venv/bin/python scripts/dev/setup_release_identities.py
export PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH"
npm --prefix apps/web run build
.venv/bin/python scripts/dev/run.py
```

Open [Finance Workspace](http://127.0.0.1:3000); API docs are at http://127.0.0.1:8000/docs. The supervisor starts the loopback API, worker and web; Ctrl+C stops its own children. PostgreSQL uses :55432. Migrations through `0008_intelligence_audit` are explicit and never run by workers. Private development identity/settings files are ignored and 0600; browser JSON cannot supply scope/actor/approval authority. Enterprise mode disables demo selection and requires verified identity/private storage/TLS configuration.

For separate backend/frontend startup details, database/seed troubleshooting and browser prerequisites, use the validated [Phase-1 setup](docs/runbooks/phase1-local.md) and [Phase-6 runbook](docs/runbooks/phase6-local.md). [Phase-2](docs/runbooks/phase2-local.md), [Phase-3](docs/runbooks/phase3-local.md), [Phase-4](docs/runbooks/phase4-local.md) and [Phase-5](docs/runbooks/phase5-local.md) retain their original stage-specific instructions.

## Tests and demo

With the application running and the project Node PATH/Chromium configured:

```bash
.venv/bin/pytest -q apps/api/tests
npm --prefix apps/web run typecheck
PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright" npm --prefix apps/web run test:e2e
.venv/bin/alembic -c apps/api/alembic.ini check
.venv/bin/python scripts/release/contracts.py
.venv/bin/pip check
.venv/bin/python scripts/release/source_security.py
.venv/bin/python scripts/release/secret_scan.py
sha256sum -c docs/source_inputs.sha256
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
sha256sum -c data/documents_phase2/fixtures.sha256
.venv/bin/python scripts/release/restore_drill.py
```

Use **Synthetic finance workspace** to upload `data/documents_phase2/vendor_native.pdf`, inspect/verify source and see the real evaluated result. Use **Synthetic policy administrator** for the separate future-allowance demonstration. Retained clean vendor/employee, duplicate, partial GRN, allowance, shared receipt, approval and capacity scenarios are exercised by real backend/browser tests. New submissions require actual authorized approval actions; no fixture authority is accepted from clients. [Demo/recovery instructions](docs/runbooks/phase6-local.md) explain correction/report/audit and governed anomaly demonstration.

CSV/XLSX supports explicit mapping with retained raw/parsed cell evidence and the established `transaction_json` development format. Formulas are rejected. JSON/HTML/CSV reports require scoped permission; CSV exports escape executable prefixes. PDF report export remains deferred. Source documents/derived pages are private; a spreadsheet attachment flag is not a receipt link.

## Deployment and handoff

One Azure Bicep implementation and separate CPU Dockerfiles are under `infra/azure` and `deploy`. `.github/workflows/validate.yml` defines tests/builds/scans/immutable artifact checksums; protected manual `pilot.yml` binds reviewed release inputs and separates migration/deployment from PR validation. Neither workflow has been claimed successful on GitHub or Azure. Current Docker authorization prevents local image builds; actual cloud inputs are absent.

Follow the [enterprise pilot gate](docs/runbooks/enterprise-pilot.md), [backup/recovery](docs/runbooks/recovery.md), [failure operations](docs/runbooks/failure-operations.md), [security review](docs/security_release_review.md) and [measured performance](docs/performance_phase6.md). No cloud spend, institutional data, real malware scanner, production model or GPU deployment is authorized by local validation.

The original team-pack folder/ZIP and all fixtures remain preserved. The byte-identical working specification is [docs/AP_Exception_Assistant_Codex_Spec.md](docs/AP_Exception_Assistant_Codex_Spec.md), governed by [ADR-0001](docs/adr/0001-repository-and-specification-authority.md). See [progress](docs/progress.md), [assumptions](docs/assumptions.md), [dictionary](docs/data_dictionary.md), [T01–T42 coverage](docs/test_coverage.md), [inference architecture](docs/inference_architecture.md), [compatibility](docs/extraction_compatibility.md), [model card](ml/model_card.md) and [release ADR](docs/adr/0014-enterprise-release-boundaries.md).

Repository: [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate), branch main. Phase-6 publication outcome/final commits are recorded in the exit review and progress after the one authorized push. Credentials are never repaired or retried by this delivery.
