# Phase-2 local document runbook

Use the [Phase-1 setup](phase1-local.md) for the owned CPU stack and private
development identity. Apply the additive migration and locked Python dependencies:

```bash
.venv/bin/python -m pip install -r apps/api/requirements.lock
.venv/bin/python -m pip check
.venv/bin/alembic -c apps/api/alembic.ini upgrade head
.venv/bin/alembic -c apps/api/alembic.ini check
.venv/bin/python scripts/dev/setup_ocr.py
export PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH"
npm run --prefix apps/web generate:api
npm run --prefix apps/web typecheck
npm run --prefix apps/web build
.venv/bin/python scripts/dev/run.py
```

The OCR command is optional and was tested on Ubuntu 24.04 x86_64. It downloads
four checksum-pinned CPU packages and extracts them under ignored runtime/tools;
it never runs sudo or installs OS packages. It records only executable/data/library
paths in private settings. Without OCR, native PDFs still work and visual inputs
show DEPENDENCY_UNAVAILABLE. PyMuPDF 1.28.2, Pillow 12.3.0, OpenCV headless
5.0.0.93, NumPy 2.5.3 and ReportLab 5.0.1 are locked. Only the synthetic fixture
generator uses ReportLab. Do not downgrade meaningful databases or delete originals.

Open [Documents](http://127.0.0.1:3000/documents). Choose purpose and PDF/PNG/JPEG
files; the browser creates an upload session, stores bytes and finalizes each file.
The worker produces pages, raw observations and a validated normalized draft.
Inspect page/zoom/field provenance; fields without measured boxes stay page-level.
Correct raw text with source page and reason, confirm the source, and choose actual
master/reference IDs in the canonical mapping. Verification appends a canonical
version and queues the existing deterministic finance engine. Missing approvals
still HOLD. Case detail retains source history and supports additional documents.

An existing case's source-correction link loads its current facts, retaining other
receipt items. Corrections append versions and reevaluate; old reports/raw source
observations remain immutable. Receipt attachment requires a stored scoped UUID
and actual item index; attaching alone does not verify source facts. An uncertain
bundle cannot be silently split or committed. Upload separately confirmed documents.

CSV/XLSX supports the existing `transaction_json` column and explicit ordinary
column mappings. In Create & import, supply canonical defaults/reference choices,
a column-to-field mapping and optional DMY/MDY date order. Money cells must be text;
formulas/numeric money cells remain invalid and visible. Cell evidence retains
batch/sheet/row/column/raw/parsed/validation. A receipt flag or fixture source UUID
does not satisfy actual-document attachment proof. No spreadsheet export exists.

Configuration lives in ignored 0600 `runtime/dev/settings.json`. Typed
`document_limits` and `document_providers` are defined in
[config.py](../../apps/api/app/documents/config.py). The default scanner is
NOT_CONFIGURED; set `malware_required=true` to fail closed until a real scanner
adapter is provided. Safe rendered previews are PNG; quarantined originals cannot
be downloaded. Scope and FINANCE_REVIEWER authority come from the server identity.
Original storage keys are internal UUIDs, never client paths. Keep originals,
private database/settings and runtime outputs out of Git.

Remote TypeLLM boundary: configure an approved HTTP endpoint/model pair and local
`tokenizer_path`, bounded timeout/rows/calls, then use the optional pinned client
requirements only on the separately authorized compatible host. The transport
requires approved preprovisioned tokenizer assets, uses local-only loading and
never downloads models. No enterprise endpoint/model is configured here. The
current driver/Docker blocker must not be repaired as part of this runbook.
Mocked provider tests establish the application boundary; actual GPU runtime and
model-quality benchmarking are deferred. Larger fallback/crops/quantization are
not configured. A provider outage cannot substitute fixture answers.

Verification from the repository root, with the owned database and app running:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright" npm run --prefix apps/web test:e2e
.venv/bin/python scripts/benchmark/documents_phase2.py
sha256sum -c data/documents_phase2/fixtures.sha256
sha256sum -c docs/source_inputs.sha256
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
```

Benchmark output is ignored and covers actual synthetic CPU native/OCR execution,
not real VLM metrics. Browser tests retain synthetic cases and screenshots under
ignored output/playwright. Integration tests use isolated migrated test schemas;
they never reset the development database. Full production readiness is not claimed.
