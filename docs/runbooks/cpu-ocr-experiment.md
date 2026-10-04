# Optional ClearLedger CPU OCR experiment

The repository defaults to Tesseract. The current local demo explicitly selects
the experimental CPU engine; the finance and Qwen/TypeLLM environments are intact.
This is an operator configuration, never an uploaded document instruction.

The executed isolated environment is `runtime/ocr-rapid/.venv` (Python 3.13).
Twenty-five resolved package versions/archive hashes are in
`scripts/ocr/requirements-rapidocr.lock`. Installation was executed once from
public PyPI into that environment; no duplicate install or inference upgrade is
required. On an approved comparable Linux x86_64 host, reproduce separately:

```bash
.venv/bin/python -m venv runtime/ocr-rapid/.venv
runtime/ocr-rapid/.venv/bin/python -m pip install --index-url https://pypi.org/simple --require-hashes -r scripts/ocr/requirements-rapidocr.lock
runtime/ocr-rapid/.venv/bin/python -m pip check
```

This lock records the executed platform, including its source distribution.
It is not an approved cross-platform dependency set or a finance requirements
file. Keep the environment and bundled weights ignored. No runtime download or
external inference endpoint is required. Do not change GPU drivers or install
GPU ONNX Runtime for this engine.

In private `runtime/dev/settings.json`, configure `document_providers`:

```json
{
  "ocr_backend": "RAPIDOCR_CPU_EXPERIMENTAL",
  "ocr_python": "/data/vansh/microsoft_inovate/runtime/ocr-rapid/.venv/bin/python"
}
```

Existing validated Tesseract executable/data settings can remain a real fallback.
Other provider, authentication and database fields must be preserved. Restart
only the identity-verified owned app process using the existing lifecycle, then
`scripts/demo.py start` reuses the model service. Do not stop the inference service
just to change an OCR flag. To roll back, set `ocr_backend` to `TESSERACT` and
`ocr_python` to null, preserving all other current settings, and restart only the
owned app. No database reset or source deletion is required.

Startup attests RapidOCR 3.9.2, CPU ONNX Runtime 1.23.2 and actual CPU sessions.
The three bundled files are independently hash checked:

| Model | SHA-256 |
|---|---|
| PP-OCRv6_det_small.onnx | `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` |
| PP-OCRv6_rec_small.onnx | `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` |
| ch_ppocr_mobile_v2.0_cls_mobile.onnx | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` |

The RapidOCR wheel hash is
`04d6b8d151f823d930bd91910555f57bea897c0c44fa6794267b94cf9c1ef9a0`.
The [upstream repository](https://github.com/RapidAI/RapidOCR) states Apache-2.0
for its code and converted PaddleOCR weights. Its advertised `MODEL_LICENSES.md`
returned 404 during this review. Retain this attribution gap for a packaged or
commercial release; this document does not certify licensing compliance.
Package provenance was checked against [RapidOCR PyPI metadata](https://pypi.org/pypi/rapidocr/3.9.2/json)
and [ONNX Runtime PyPI metadata](https://pypi.org/pypi/onnxruntime/1.23.2/json).

Run actual isolated CPU integration against a fresh scoped test database:

```bash
AP_RUN_CPU_OCR=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_cpu_ocr_live.py -q --tb=short
```

Use the benchmark commands in `docs/clearledger_validation.md` for frozen tuning
and reserved layouts. Engine scores are diagnostics; they cannot verify source
facts or authorize finance processing. Known wrapped-table disagreement remains
visible as Needs review. Missing/ambiguous date, currency and tax stay unresolved.
