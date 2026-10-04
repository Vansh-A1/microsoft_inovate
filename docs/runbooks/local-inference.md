# Local real VLM experiment

This is the tested current-driver tuple from [ADR-0015](../adr/0015-current-driver-compatible-real-vlm.md).
It runs beside the finance application; ordinary finance browsers need no GPU.
It is a single-machine experiment with a research-licensed checkpoint, not a
production deployment. Do not change drivers, host CUDA, system Python or Docker.

## Installed locations and pins

Run commands from `/data/vansh/microsoft_inovate`.

| Artifact | Location / pin |
|---|---|
| GPU server environment | `runtime/inference/env`, Python 3.12.3; [serving lock](../../scripts/inference/requirements-serving.lock) |
| CPU TypeLLM gateway | `runtime/inference/client`, Python 3.12.3; [client lock](../../scripts/inference/requirements-client.lock) |
| Finance app | `.venv`, Python 3.13.11; unchanged application lock |
| Model | `runtime/inference/models/qwen2.5-vl-3b`; Qwen/Qwen2.5-VL-3B-Instruct, revision `66285546d2b821cf421d4f5eb2576359d3770cd3` |
| Model bytes | Two safetensors shards, 7,509,337,976 bytes total; tokenizer/processor/template/config also pinned |
| Private key/config/state | `runtime/inference/{gateway.key,gateway_config.json,local-state.json}`, mode 0600 |
| Cache, logs and reports | `runtime/inference/{cache,logs,reports,tmp}`; ignored by Git |
| Private originals/pages/crops | Existing development storage adapter; outside Git |
| Local Python headers | `runtime/inference/headers`; extracted files only |

Weights SHA-256:

```text
model-00001-of-00002.safetensors 41a8895c164b4d32bae6b302f4603fcbc1797f32dafa45c7e9bcda23c6755df8
model-00002-of-00002.safetensors 365531ff8752420e89dee707b79d021fb2d6e25abafe486f080555a4fe6972e4
```

The actual `LICENSE` is the Qwen RESEARCH LICENSE AGREEMENT. Review it before
any use beyond the authorized experiment. Do not substitute a similarly named
checkpoint without a new revision/license/compatibility check.

## Recreate isolated environments

The current installation was exercised; these recreation commands describe its
recorded pins, not a claim that a second clean rebuild was executed. Python 3.12.3
already exists at `/usr/bin/python3.12`. If venv lacks ensurepip, use a downloaded
official pip 25.1.1 wheel in `runtime/inference` through `PYTHONPATH`, rather than
installing an administrator package. Keep download caches and TMPDIR under /data.

```bash
mkdir -p runtime/inference/{cache,tmp,logs,reports,models}
/usr/bin/python3.12 -m venv --without-pip runtime/inference/env
/usr/bin/python3.12 -m venv --without-pip runtime/inference/client
# After downloading the official pip 25.1.1 wheel to runtime/inference/wheels:
PYTHONPATH="$PWD/runtime/inference/wheels/pip-25.1.1-py3-none-any.whl" \
  runtime/inference/env/bin/python -m pip install --no-index \
  runtime/inference/wheels/pip-25.1.1-py3-none-any.whl
PYTHONPATH="$PWD/runtime/inference/wheels/pip-25.1.1-py3-none-any.whl" \
  runtime/inference/client/bin/python -m pip install --no-index \
  runtime/inference/wheels/pip-25.1.1-py3-none-any.whl
runtime/inference/env/bin/python -m pip install \
  --extra-index-url https://download.pytorch.org/whl/cu124 \
  -r scripts/inference/requirements-serving.lock
runtime/inference/client/bin/python -m pip install \
  -r scripts/inference/requirements-client.lock
# Repair the upstream Decord wheel metadata as described below before pip check.
runtime/inference/env/bin/python -m pip check
runtime/inference/client/bin/python -m pip check
```

Download the exact revision's configs, tokenizer/processor/chat template, two
safetensors shards/index, README and LICENSE using the official Hugging Face
snapshot API into the model location above. Validate the recorded shard hashes
before starting. Do not download model weights into the finance environment.

The initial runtime needed Python.h. The official Ubuntu archive artifact
`libpython3.12-dev_3.12.3-1ubuntu0.17_amd64.deb` (5,683,746 bytes, SHA-256
`c123ddab7763e45199e21b4ac8545e705f20a0315b9ada4c236b52fb088c4e16`)
was downloaded and extracted with `dpkg-deb -x FILE runtime/inference/headers`.
This did not install a package or modify `/usr`. The launcher sets CPATH to those
local headers and `TORCHDYNAMO_DISABLE=1`. Required `decord==0.6.0` and all actual
resolved runtime dependencies are captured in the serving lock.

Decord's official Linux 0.6.0 wheel has inconsistent internal CPython-3.6 tags
despite its Python-3 filename, and an invalid RECORD entry. The actual library
imports on Python 3.12; no CPython extension ABI file is included. Download the
official `decord-0.6.0-py3-none-manylinux2010_x86_64.whl` from its PyPI 0.6.0
release into `runtime/inference` (SHA-256
`51997f20be8958e23b7c4061ba45d0efcd86bffd5fe81c695d0befee0d442976`).
The following tested metadata-only rebuild uses wheel 0.45.1 and verifies that
every runtime file stays byte-identical. It changes only WHEEL/RECORD, never model
or library behavior; the repacked archive's SHA is printed for local provenance.

```bash
runtime/inference/client/bin/python -m pip install \
  --target runtime/inference/packaging wheel==0.45.1
.venv/bin/python scripts/inference/repack_decord.py \
  runtime/inference/decord-0.6.0-py3-none-manylinux2010_x86_64.whl --install
runtime/inference/env/bin/python -m pip check
```

## Configure and run

Preserve the existing private database and development settings. The configure
command changes only the document provider section of ignored settings. The
default SDK transport remains supported for separately hosted compatible servers.

```bash
.venv/bin/python scripts/inference/local.py configure
.venv/bin/python scripts/inference/local.py start
.venv/bin/python scripts/inference/local.py health
.venv/bin/python scripts/inference/local.py app
```

Wait for a successful health response before submitting a visual document. The
resident BF16 SGLang server uses loopback :30000, context 8192, torch_native/SDPA,
pytorch sampling, xgrammar, CUDA graphs disabled, static memory fraction .75.
The authenticated CPU gateway uses :30001. The app wrapper reads the private
gateway token into its environment without printing it and starts the established
API :8000/web :3000/worker supervisor. Do not run another app supervisor on those
ports. Ctrl+C stops the app supervisor's own children.

Provider settings: `transport=TYPELLM_GATEWAY`, configured endpoint/model/revision,
timeout 120 seconds, token environment `AP_TYPELLM_GATEWAY_TOKEN`. Domain finance
code contains no localhost or GPU requirements. Actual safe provider versions,
prompt hash, routing paths, calls/timings and source pages persist with each run.
Admin Console → System health & recovery shows authenticated provider health.

Upload PNG/JPEG/PDF in Finance Workspace. Complete native/OCR documents remain
cheap. Incomplete mapping reaches the real model. Inspect extracted facts and
source, correct any uncertain values, select authorized existing references, then
submit to the unchanged finance engine. A model response cannot approve a vendor
or waive a control. Empty/missing/ambiguous critical values cannot become zero or PASS.

## Benchmark and opt-in real tests

Ordinary CI needs no GPU, model download or gateway. The real tests require the
resident provider and the private primary invoice. The default skips are explicit.

```bash
.venv/bin/python scripts/benchmark/real_vlm.py \
  --primary /tmp/codex-clipboard-067b972e-08fe-4a54-925a-757c3e4edeca.png
AP_RUN_REAL_VLM=1 \
AP_VLM_PRIMARY_DOCUMENT=/tmp/codex-clipboard-067b972e-08fe-4a54-925a-757c3e4edeca.png \
  .venv/bin/pytest -q apps/api/tests/integration/test_real_vlm.py
.venv/bin/pytest -q apps/api/tests
```

For the measured crop comparison, use `--primary-only --disable-row-crops`
and a separate `--output runtime/inference/reports/full-page-comparison.json`.
Both branches still call the real model. Complete application browser tests and
production builds sequentially: do not rebuild Next.js while testing its running
development server; restart the app after a production build before browser checks.

The optional `--primary-expectations PATH` reads independent verification JSON
**after inference**. Keep this JSON private. No expected values enter prompts.
The benchmark forces the actual provider even for digital PDFs; the normal
application separately proves that complete native PDFs do not invoke VLM.
Raw outputs and benchmark traces are private reports, not committed training rows.

## Failure, stop and cleanup

```bash
.venv/bin/python scripts/inference/local.py stop
.venv/bin/python scripts/inference/local.py health
.venv/bin/python scripts/inference/local.py restart
```

After stop, health must fail rather than report AVAILABLE. `stop` verifies its
stored supervisor's command and UID before signaling only its owned processes.
No Docker or unrelated process is touched. Startup errors are in
`runtime/inference/logs/local-server.log`; no document/reasoning/token payload is
logged by the gateway. A timeout that leaves backend work/cache active fails
closed; stop/start the owned inference supervisor before retrying. Permanent
unsupported inputs and missing mandatory user input do not become endless retries.

Keep the working runtime after success. For deliberate future cleanup, first stop
the app and inference and back up required private reports/configuration. The
following removes **only this experimental runtime**, including its model/key:

```bash
# Destructive, optional future cleanup; not performed by this task.
.venv/bin/python scripts/inference/local.py cleanup --confirm-remove-runtime
```

The cleanup command refuses live owned services and an unsafe/symlink runtime location. The guarded command was tested without deleting the accepted runtime. See [hackathon lifecycle](hackathon-demo.md) for integrated start/stop/health.

Never remove the established `runtime/dev`, private finance storage, database,
`.venv`, source fixtures or original team pack as inference cleanup.
