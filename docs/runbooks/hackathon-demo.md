# Hackathon release runbook

This profile is a synthetic local demonstration. It executes no payments and
does not replace the externally gated [enterprise pilot](enterprise-pilot.md).
Run from the repository root. Existing evidence and financial history are retained.

## Prerequisites and first setup

Follow the [README setup](../../README.md#local-setup) for the isolated Python
3.13.11 finance environment, Node 24.21.0, PostgreSQL 16.15 and locked dependencies.
Explicitly migrate to `0008_intelligence_audit`, seed the existing reference/demo
catalog and configure development identities. Build the frontend with the app
stopped. Startup does not install dependencies, run migrations or reset data.

For visual extraction use the [accepted local inference setup](local-inference.md)
and ADR-0015. Keep Python 3.12.3, Torch 2.6.0+cu124/CUDA 12.4, SGLang
0.4.6.post5, serving Transformers 4.51.1, CPU TypeLLM 0.5.1 and pinned Qwen
revision `66285546d2b821cf421d4f5eb2576359d3770cd3`. Do not merge them into
`.venv`, upgrade drivers, require Docker or change models. The launcher checks
actual shard SHA-256, runtime pins, GPU visibility and at least 13 GiB free VRAM
before loading the frozen BF16 model. This headroom is a conservative startup
requirement for this measured development tuple, not a universal capacity claim.

## Start, check and prepare

```bash
./scripts/start-demo.sh
./scripts/demo-health.sh --require-vlm
./scripts/prepare-demo.sh
```

Startup checks the non-superuser/non-bypass database role and migration head. It
may start only the existing initialized project-owned local PostgreSQL cluster.
It prepares a separate fictional tenant, starts/checks resident inference and
starts the established API :8000, worker and production frontend :3000. It refuses
an unrelated app already using those ports. Inspect failures in the private
`runtime/demo/services.log` and `runtime/inference/logs/local-server.log`.
Provider startup checks also retain their safe output in the private
`runtime/demo/inference-start.log`; an unavailable provider is reported explicitly.

Open http://127.0.0.1:3000/demo. Select **Hackathon finance reviewer**. All identities
are server configured and development only. **Hackathon manager** and
**Hackathon department head** are independent approval actors; **Hackathon auditor**
reads/exports; **Hackathon operations** inspects/retries/reconciles and cannot
approve or alter policy. The seed driver uses these actual authorities. No single
reviewer can manufacture PASS or self-approve.

The scenario builder calls the actual HTTP/worker pipeline and stores private
checkpoints at `runtime/demo/scenarios.json`. It preserves existing tenant data;
it never resets a database or removes earlier uploads. Source PDF/image bytes,
raw observations, canonical facts, approvals and retained evaluations are real
persisted artifacts. Rerunning uses stable idempotency keys and immutable history.

## Presenter walkthrough

| Case | Engine behavior to inspect |
|---|---|
| Visual ruled-table invoice | Original image → OCR mapping gap → real VLM/TypeLLM → string observations → Decimal normalization → human source verification → PO/GRN capacity → independent approvals → PASS. Open source/provider metadata and retained report. |
| Repeated paid invoice | Corroborated paid obligation → HOLD; candidate evidence remains visible. |
| Partial delivery | Order 100, available accepted receipt 50, billed 70 → HOLD for 20-unit shortfall. |
| Employee expenses | Clean taxi → PASS; daily meals above allowance → REVIEW. |
| Shared receipts | Authorized within-capacity allocation → PASS after explicit distinct-obligation inspection; exceeded capacity → HOLD. |
| Correction history | Source invoice version 1 PASS; introduced canonical transcription error version 2 HOLD; source correction and fresh independent approvals version 3 PASS. Original HOLD/report remains unchanged. |

The labels summarize checks, not hard-coded decisions. The walkthrough resolves
its outcomes from authorized retained evaluation records and links to current
cases. A historical PASS may be superseded; the screen states its evaluation and
current version. Always inspect current eligibility before describing a case.

## Stop, restart and no-GPU operation

```bash
./scripts/stop-demo.sh
./scripts/start-demo.sh --no-vlm
./scripts/demo-health.sh
./scripts/demo-health.sh --require-vlm
.venv/bin/python scripts/demo.py restart
```

Stop signals only owned processes and retains PostgreSQL, settings, evidence and
model caches. CPU startup reports DEGRADED with PROVIDER_UNAVAILABLE when visual
inference is stopped. Required-VLM health returns nonzero. Complete native-text
mapping can proceed independently; unknown critical visual facts cannot PASS.

Inference-only controls are `scripts/inference/local.py start|stop|health|restart`.
The server remains resident between documents. Health authenticates the gateway
and verifies served revision/BF16/GPU status, rather than merely checking a TCP
port. Actual TypeLLM image acceptance is a separate opt-in test below.
`cleanup --confirm-remove-runtime` removes only the isolated inference directory
after all owned services stop; it deletes weights and private inference reports.
Back them up first. Cleanup was guard-tested, not executed in release verification.

## Failure and recovery drill

Run only against the local development profile, sequentially:

```bash
./scripts/stop-demo.sh
./scripts/start-demo.sh --no-vlm
.venv/bin/python scripts/release/demo_drill.py offline
.venv/bin/python scripts/inference/local.py start
# Wait for authenticated inference health to be AVAILABLE.
.venv/bin/python scripts/inference/local.py health
.venv/bin/python scripts/release/demo_drill.py recover
```

The actual offline drill verifies native READY and three bounded visual provider
failures with no observations/draft/finance decision. Recovery uses authorized,
audited, idempotent manual retry of the retained original stage and requires real
VLM provenance. It does not grant a finance decision to an unverified document.

## Tests and known boundaries

Ordinary backend/CI tests require no GPU/model. Real acceptance is explicitly:

```bash
AP_RUN_REAL_VLM=1 \
AP_VLM_PRIMARY_DOCUMENT=/tmp/codex-clipboard-067b972e-08fe-4a54-925a-757c3e4edeca.png \
  .venv/bin/pytest -q apps/api/tests/integration/test_real_vlm.py
```

The attached East Repair invoice intentionally remains NEEDS_INPUT for currency
and date ambiguity and absent critical extras; reading rows does not authorize
finance PASS. The compact synthetic pipe-table model result can confuse net/gross;
source corrections are retained. The separately prepared ruled-table demo printed
one row and required zero row corrections in this execution. These small related
synthetic tests cannot establish universal or commercial accuracy.

The prior two-page measured case took 117.735 s near the configured 120 s document
budget. Do not silently truncate large documents. Quantization, model changes,
advanced segmentation/table families and production throughput are later work.
The checkpoint uses the Qwen RESEARCH LICENSE AGREEMENT; commercial model/license
selection, representative supervised labels and live Azure provisioning remain
external gates. JSON/HTML/CSV reports work; PDF export and configured malware
scanning remain deferred, with scanner status NOT_CONFIGURED rather than CLEAN.
