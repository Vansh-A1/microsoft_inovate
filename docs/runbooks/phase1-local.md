# Phase-1 local runbook

This is a synthetic local development product. Tested on Ubuntu 24.04.2 x86_64, Python 3.13.11, Node 24.21.0 and PostgreSQL 16.15. Use an ordinary user with `python3`, venv support, `apt-get download`, `dpkg-deb` and the Ubuntu 24.04 runtime libraries (including libicu74). The bootstrap verifies exact official Node/archive and PostgreSQL package checksums and extracts tools locally. It never installs OS packages, runs sudo, changes Docker permissions or installs inference.

From the repository root:

```bash
python3 scripts/dev/bootstrap.py
.venv/bin/alembic -c apps/api/alembic.ini upgrade head
.venv/bin/python scripts/seed/phase1.py
export PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH"
npm run --prefix apps/web build
.venv/bin/python scripts/dev/run.py
```

Open [AP Review Desk](http://127.0.0.1:3000). Ctrl+C stops the supervisor's three child process groups. PostgreSQL stays running in the owned project directory. These commands were executed successfully on the stated host. On other platforms use separately installed compatible Node/PostgreSQL and configure the private development settings rather than substituting SQLite. The local package bootstrap deliberately stops if pinned Ubuntu packages or prerequisites are unavailable.

The API binds 127.0.0.1:8000; the web binds 127.0.0.1:3000; PostgreSQL binds 127.0.0.1:55432. API documentation is at [OpenAPI UI](http://127.0.0.1:8000/docs); authenticated API operations require the private trusted development bearer token. Do not print or copy that token into browser storage, public environment variables, commits or logs. The Next server injects it from `.env.local` and accepts only its explicit loopback host/origin pairs. This is not production identity or SSO.

Setup generates private 0600 `runtime/dev/settings.json`, `runtime/dev/admin.json` and `apps/web/.env.local`; the runtime directory is ignored. The bootstrap role belongs only to this owned cluster. Business sessions use `ap_app` NOSUPERUSER/NOBYPASSRLS, forced row-level policies and transaction-local scope. The default identity is a synthetic FINANCE_REVIEWER in tenant `10000000-0000-4000-8000-000000000001`, entity `20000000-0000-4000-8000-000000000001`, actor `51000000-0000-4000-8000-000000000001`. Tests provision separate trusted tokens for another tenant and a read-only auditor.

## Demo and intake

The seed command imports original synthetic references and trusted approval records, then executes the same durable worker and rules as ordinary intake. Repeating it does not duplicate existing logical effects. It preserves revised user cases and refreshes unchanged seed cases when the rule version changes. Seed results are clean vendor PASS, paid duplicate HOLD, clean taxi PASS, daily meal REVIEW, missing Department Head approval HOLD. UUIDs end in 001, 002, 005, 008 and 004 respectively. Golden cases are independently adjudicated alternatives; the five-case demo combines only these compatible cases. The eight supported cases are tested individually with fresh migrated schemas.

Create & import loads editable synthetic examples from the API. Ordinary submissions have no approval authority: complete chains are installed only through trusted seed provisioning, so newly created examples commonly HOLD. Edit primary fields or expand the full structured JSON. Money stays in decimal strings; dates use ISO storage. Corrections append versions and invalidate old eligibility and version-bound approval applicability. Historical reports remain available.

Imports use one header `transaction_json`, one JSON object per data row. CSV is UTF-8; XLSX cells must be text. Blank/invalid/formula rows are retained with sheet, row number, raw cell, errors and digest. Preview has no financial effect; commit creates valid rows, queues evaluation and keeps invalid rows visible. Maximums: 2 MiB file, 200 data rows, 10 sheets, 20 MiB ZIP expansion, 100 ZIP members; no macros/external links. JSON/multipart transport is capped at 2,300,000 bytes. Imports and mutations require Idempotency-Key. Same key and request return the original response; changed input returns 409.

## Verification

With the owned database running:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
.venv/bin/python -m pip check
npm run --prefix apps/web generate:api
npm run --prefix apps/web typecheck
npm run --prefix apps/web build
PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright" npm exec --prefix apps/web -- playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright" npm run --prefix apps/web test:e2e
sha256sum -c docs/source_inputs.sha256
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
cmp docs/AP_Exception_Assistant_Codex_Spec.md AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md
```

Browser tests require the production server, API and worker from `run.py`. Outputs live under ignored `output/playwright/`. They create retained synthetic UI-TEST/UI-IMPORT cases in the development database; they do not delete immutable business history. PostgreSQL integration tests create and remove their own UUID-named schemas in `ap_phase1_test`, exercise actual migrations and non-superuser RLS, and never reset `ap_phase1`. They skip only when private database settings are absent; the recorded local gate ran with no skipped tests. One upstream Starlette/httpx deprecation warning is currently non-fatal.

For individual processes:

```bash
PYTHONPATH=apps/api .venv/bin/python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
PYTHONPATH=apps/api .venv/bin/python -m app.services.worker
npm run --prefix apps/web start
```

## Development backup and recovery boundary

The application does not have a production backup/restore, monitoring or deployment system. Preserve the ignored private credentials and `runtime/postgres` together. Stop the owned cluster cleanly before making a filesystem backup; never copy a running cluster as a claimed valid backup. A clean stop command is:

```bash
LD_LIBRARY_PATH="$PWD/runtime/tools/postgres/usr/lib/x86_64-linux-gnu" runtime/tools/postgres/usr/lib/postgresql/16/bin/pg_ctl -D "$PWD/runtime/postgres" -w stop
```

Restart through `setup_database.py`. Fresh migration, downgrade/upgrade and re-seeding were tested in isolated databases; a backup restore exercise remains a later operational gate. Do not run migration downgrade against meaningful development data: it removes schema objects. No destructive reset command is part of setup.

## Limits

INR, ordinary exclusive-tax invoices, goods PO/GRN lines and fully attributed ordinary receipts are supported. Partial/shared receipt allocations, fuzzy/image duplicates, service acceptance, sophisticated ledger settlement/cancellation, waivers/delegation, live master imports and human approval/resolution workflows remain future work. Partial receipt allocation, unsupported currency/type or unresolved facts cannot receive PASS. Capacity reservations are minimal guarded screening effects, not a payment or settlement ledger. History/catalog limits produce explicit failures; they never become empty history or unlimited budget.

Extraction is STRUCTURED_SYNTHETIC; the P0 FIXTURE adapter remains available separately. Synthetic JSON facts provide no source pixels or bounding boxes. Risk is RULES_ONLY / NOT_CONFIGURED with no score. No live TypeLLM/SGLang/VLM, PDF/OCR/preprocessing, ML or cloud deployment has been introduced. Initial development evaluations are retained and superseded; full legacy-engine replay and retained policy-change replay (T42) are not claimed. Private orphan import objects can remain after transaction failure; reconciliation is deferred.
