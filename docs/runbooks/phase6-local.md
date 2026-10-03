# Phase-6 local operation and demonstration

Use only synthetic sources in this development deployment. It binds loopback and uses explicit synthetic identities. This is not enterprise SSO or a production pilot.

## Start and verify

Prerequisites: Ubuntu 24.04 x86_64 for the supplied ordinary-user tools, Python 3.13.11, Node 24.21.0, PostgreSQL 16.15 and the locked packages. The bootstrap uses project-local tools, never sudo. See the earlier [setup](phase1-local.md) and [document](phase2-local.md) runbooks for downloads and platform limits. It preserves existing private settings/data; do not delete a working database to refresh a demo.

Validated setup/start commands from the existing stack and release pass:

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

Open http://127.0.0.1:3000. The supervisor starts API :8000, worker and production web :3000; Ctrl+C stops only its own children. PostgreSQL :55432 stays available. Existing migrations through `0008_intelligence_audit` are explicit; workers do not migrate. Seed commands are development-only and retain existing evaluations. Configuration/tokens are in ignored 0600 files. Never paste their contents into a ticket/log/Git.

## Finance demonstration

Select **Synthetic finance workspace** for small finance-only navigation. Upload `data/documents_phase2/vendor_native.pdf`, wait for processing, inspect source page/facts, pick relevant business references, enter a verification reason and confirm source inspection. Click **Verify facts and evaluate**. The actual source-derived case receives HOLD when approvals/other controls remain unresolved. This is computed, not a prescribed outcome. **View detailed checks** retains rule/source evidence. The audit timeline and report remain available after reload and application restart.

Use source correction fields for observed amounts/dates/numbers. Mapping values backed by source are read-only; business reference choices remain editable. A correction/revision appends history and requires fresh evaluation/approvals. Never use a JSON outcome or supplied actor/role to assert eligibility.

Seeded retained cases show clean vendor PASS, paid duplicate HOLD, clean taxi PASS and daily meal REVIEW. Browser/integration tests separately exercise ordered approvals, partial GRN, budget conflicts, actual shared receipts, DISTINCT/duplicate dispositions, waivers, stale writes, correction/re-evaluation, cancellation, report exports and degraded providers. Re-evaluating a seed against new reference/allocation state may change the current decision; its original report remains immutable.

## Separate administration demonstration

Select **Synthetic policy administrator**, open Admin Console and select HOTEL. Change 8,000 to 9,000 per eligible night with effective-from **2026-11-01**, preserve effective-until **2027-01-01**, and provide a reason. **Save draft** runs existing validation; only a VALID draft can be activated. Activation creates another reference version. Version history shows reason/time and optional actor/details; original snapshots/reports remain intact. The integration test proves pre/post-effective-date selection and 409 conflicts.

Master stewards use their separate REFERENCE_ADMIN authority. A POLICY_ADMIN cannot edit/activate vendors, bank records, budgets or arbitrary JSON/code. Budget adjustment uses LEDGER_ADMIN and the existing ledger. Approvers cannot approve their own submissions; auditor/export roles are read-only. System health needs OPERATIONS_ADMIN/OPERATIONS_READER or auditor authority and is not exposed to an ordinary finance reviewer.

## Intelligence demonstration

New scopes default RULES_ONLY, NOT_CONFIGURED, null score. The release regression scope was explicitly governed to RULES_ONLY while incompatible old artifacts remained historical. For measured statistical demonstration, use separate author/governor identities and the [Phase-5 workflow](phase5-local.md): freeze a development manifest, register/evaluate candidate, approve, shadow, observe real scores, then activate with expected deployment version. No training action activates itself. Roll back through the same governed deployment endpoint.

A release that changes artifact-bound code requires a newly compatible candidate/shadow record; do not overwrite the old model or scores. Backend/browser tests demonstrate actual statistical PASS→REVIEW, low statistical score plus mandatory HOLD→HOLD, required artifact outage→MODEL_UNAVAILABLE and immutable replay/rollback. Classifier/SHAP remain absent for the valid data gate.

## Release verification

Run the backend before destructive-looking cleanup; it creates and removes only its own migrated test schemas. Browser tests retain synthetic records in the running demo.

```bash
.venv/bin/pytest -q apps/api/tests
npm --prefix apps/web run typecheck
npm --prefix apps/web run test:e2e
.venv/bin/alembic -c apps/api/alembic.ini check
.venv/bin/python scripts/release/contracts.py
npm --prefix apps/web run generate:api
.venv/bin/pip check
.venv/bin/python scripts/release/source_security.py
.venv/bin/python scripts/release/secret_scan.py
sha256sum -c docs/source_inputs.sha256
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
sha256sum -c data/documents_phase2/fixtures.sha256
.venv/bin/python scripts/release/restore_drill.py
```

Playwright uses project Chromium at `PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright"`. The earlier browser installation command/runbook remains applicable. See [exit review](../phase6_exit_review.md) for exact executed counts, [performance](../performance_phase6.md), [recovery](recovery.md) and [enterprise gate](enterprise-pilot.md). No database reset, retention cleanup, cloud provisioning or next phase is part of this runbook.
