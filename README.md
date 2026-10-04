# Kivo

Invoice and expense exception workspace · repository: microsoft_inovate

The application screens vendor invoices and employee claims using source evidence, versioned finance rules, matching, approvals and budgets. It produces **PASS / REVIEW / HOLD**, preserves the original decision and shows the next action. It executes no payments.

The normal UI presents **Ready for processing / Needs review / On hold**, separate
Finance and Admin workspaces, Auto intake, source uncertainty and versioned policy
forms. Open [Kivo locally](http://127.0.0.1:3000/welcome). The local entry uses
fictional server-configured identities; real organization SSO remains externally
configured. Set `NEXT_PUBLIC_PRODUCT_NAME` before the web build to change the name.
Kivo is the configurable working name for the existing ClearLedger/AP assistant; no trademark or domain availability is asserted. See the [first polished UI checkpoint](docs/kivo_ui_verification.md) and [policy guide](docs/kivo_user_guide.md).
See [ClearLedger hardening and measured limits](docs/clearledger_hardening.md).
The continued [twelve-layout validation](docs/clearledger_validation.md) records
before/after benchmarks, actual cold/warm and upload/queue timings, remaining
table failures and [optional isolated CPU OCR](docs/runbooks/cpu-ocr-experiment.md).
The [CL-06 table correctness checkpoint](docs/clearledger_table_correctness.md)
fixes the two spent failures, preserves genuinely unknown values and records
eight fresh reserved variants without rewriting the previous benchmark.
The [CL-07 row correctness checkpoint](docs/clearledger_row_correctness.md)
retains unread cells and distinct repeated items, bounds unassigned VLM generation
and records six fresh fictional variants. [Acceptance inputs](docs/clearledger_acceptance_inputs.md)
separate the functioning local demo from independent corpus, business-policy,
identity, scanner and production-pilot acceptance.
The [CL-08 independent public evaluation](docs/clearledger_independent_validation.md)
checks four externally authored licensed fictional sources through the unchanged
pipeline. It records wrong draft values and unresolved headers/European amounts:
the bounded judge walkthrough passes, broader invoice automation acceptance does not.

Phase 6 delivers the local application and release/handoff artifacts under an explicit external-infrastructure fallback. The subsequent approved priority override establishes **real local VLM + TypeLLM invoice extraction** on the unchanged GPU driver. This is a development experiment, not a deployed production pilot. See the [real inference acceptance record](docs/real_vlm_acceptance.md), [Phase-6 exit review](docs/phase6_exit_review.md) and [capability matrix](docs/release_matrix.md).

## Hackathon quick start

With the established local database, finance environment, production web build and isolated inference runtime installed:

```bash
./scripts/start-demo.sh
./scripts/demo-health.sh --require-vlm
./scripts/prepare-demo.sh
```

Open [the walkthrough](http://127.0.0.1:3000/demo) and select **Hackathon finance reviewer**. Eight persisted examples cover actual visual extraction/TypeLLM and PO/GRN PASS, paid duplicates, partial delivery, clean/over-allowance expenses, shared receipts and immutable correction history. Results are computed by the existing engine. The separate synthetic scope preserves existing data and permissions; rerunning preparation reuses guarded operations.

Stop with `./scripts/stop-demo.sh`; it retains PostgreSQL, evidence and model caches. Start CPU services with `./scripts/start-demo.sh --no-vlm` when no GPU is available; visual inference reports provider unavailability. Independently configured OCR can still read sufficient printed facts; unresolved facts cannot imply finance clearance. Use [the hackathon runbook](docs/runbooks/hackathon-demo.md) for prerequisites, recovery, identities and measured limits, and [the final project exit review](docs/final_project_exit_review.md) for release evidence/external gates. `.venv/bin/python scripts/release/judge_verify.py` checks all eight current computed scenarios and retained source/correction evidence without changing them.

## Finance Workspace

Use an ordinary browser: **Upload invoice or receipt → Processing → inspect source facts → verify/map business references → Result**. The default screen leads with unresolved checks and plain next actions. Source previews, corrections, ownership, approvals, queue, audit and report are available; rule IDs/full facts are expandable details. Both vendor and employee records persist. A missing/ambiguous critical fact, missing dependency, stale approval or insufficient capacity cannot silently PASS.

PASS means current screening eligibility at the recorded snapshot, not paid. REVIEW needs uncertainty/judgment resolved. HOLD blocks eligibility until a mandatory condition is resolved. Processing, human ownership and approvals are separate states. Historical reports remain immutable after correction, cancellation or supersession.

## Admin Console

Administration has separate navigation and permissions. Typed business forms edit supported allowance/effective-date/approval-band/delegation/master fields through validated drafts and new reference versions; budgets use audited ledger adjustments. A policy administrator cannot activate vendor/budget masters. The future hotel allowance demonstration retains 8,000 and creates 9,000 from 2026-11-01, with actor/reason/time. Model author/governor and operational health permissions remain separate. There is no arbitrary code/SQL or set-PASS control.

The local malware engine is **not configured**. An operator may connect an
already installed local clamscan with `AP_MALWARE_SCANNER_EXECUTABLE`; no scanner or
definitions are installed by the application. Intake/Admin disclose configuration
and availability explicitly. Required-scanning settings remain fail-closed;
configuration alone is not CLEAN. See the [local hardening runbook](docs/clearledger_hardening.md).

## Architecture and modes

[Architecture](docs/architecture.md) and [data flow](docs/data_flow.md) explain the CPU Next.js/FastAPI/PostgreSQL/private storage/leased worker application. The [experimental inference plane](docs/adr/0015-current-driver-compatible-real-vlm.md) runs in separate processes/environments. Finance laptops need no GPU/CUDA/weights/TypeLLM/SGLang.

| Area | Current status |
|---|---|
| Deterministic finance | 28 controls; Decimal/currency, source coverage, vendor/employee, duplicates, PO/contract/GRN/service, policy, offsets/shared receipts, budgets and approvals. |
| Actual documents | PyMuPDF native text/pages and local Tesseract CPU OCR; bounded parsing, preserved originals, uncertainty and source-linked human verification. |
| TypeLLM | Actual 0.5.1 text/image/header/row generation through the existing adapter; money is extracted as strings. |
| VLM / SGLang | OPERATIONAL FOR TESTED CASES: pinned Qwen2.5-VL-3B BF16, SGLang 0.4.6.post5/PyTorch CUDA 12.4, unchanged driver 550.120; isolated resident loopback service. Production hosting/license/quality gates remain. |
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

For the installed real extraction experiment, use the [local inference runbook](docs/runbooks/local-inference.md):

```bash
.venv/bin/python scripts/inference/local.py start
.venv/bin/python scripts/inference/local.py health
.venv/bin/python scripts/inference/local.py app
```

The app command supplies the private gateway token to the established supervisor.
Do not start a second supervisor on the same ports. Complete native/OCR mapping
stays cheap; incomplete mapping reaches VLM. Currency/date ambiguity, conflicting
providers and arithmetic errors require source-linked correction. This small
model's tested extraction is useful and imperfect; no universal accuracy is claimed.

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

Repository: [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate), branch **main**. The Phase-6 source and history were published at `6be40387d4c4268a83468dd112b0d5bf4f6e9f2b`; all 310 then-tracked file modes/blob hashes, including both CI workflows, were verified. The later real-VLM override explicitly excludes publication/authentication work: its changes are local commits only, with no push retried. [Exit review](docs/phase6_exit_review.md) and [progress](docs/progress.md) preserve earlier publication history. Credentials are not stored in repository files or remote URLs. Cloud/pilot deployment remains deferred.

The bounded [CL-09 source repair](docs/clearledger_source_repair.md) preserves the
working finance engine and approved BF16 runtime. It fixes source-context European
money, multi-page provider-null reconciliation, dense measured tables and inline
header ownership. Limited selected-field results improve on four spent public
fictional development invoices; all still require source/accounting confirmation.
The report retains failed attempts, actual timings, additional-probe limits and
unresolved rotated/multi-blank rows. No fine-tuning, data/model acquisition, push
or deployment follows from this checkpoint.

[CL-10 measured rotation/partial-row repair](docs/clearledger_rotation_robustness.md)
adds bounded source-preserving CPU orientation/deskew/crop projection and honest
missing-cell capture on the existing engine. It preserves original evidence,
conflicting-read/null holds and actual provider provenance. Baselines, first new
reserved-family results, spent replays and the repaired real border failure are
recorded separately. [Consolidated hackathon readiness](docs/clearledger_hackathon_readiness.md)
defines the local fictional demo claim, remaining real-data/business/identity/
scanner/pilot gates and the current core stopping point. Further UI redesign is
deferred; local commit only, no push or deploy.
