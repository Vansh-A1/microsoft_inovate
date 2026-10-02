# P0-04B/P0-04C compatibility checklist

P0-04A supplies contracts, structured synthetic cases, replay and comparison only. This checklist records future verification work; P0-04B has not started. No TypeLLM/SGLang source was fetched or installed, model downloaded, runtime launched, OCR integrated, or provider called in P0-04A. Every topic below is **NOT CHECKED**. The [specification](AP_Exception_Assistant_Codex_Spec.md) states the intended architecture; it does not prove current package/runtime compatibility.

For P0-04B, inspect current official repositories/documentation and model cards. Record exact URLs, inspection dates, release/commit/package versions and supporting evidence. Tutorials are not authoritative. A documentation claim may become DOCUMENTED; only an executed, recorded check may become VERIFIED LOCALLY. BLOCKED and UNSUPPORTED require stated evidence. Unresolved claims remain NOT CHECKED/NOT VERIFIED. No installation is authorized by this document.

| Topic | Status | Evidence required in later approved work |
|---|---|---|
| TypeLLM identity/version | NOT CHECKED | Official repository, exact release/commit/package identity; distinguish similarly named projects. |
| Python support | NOT CHECKED | Declared interpreter range plus compatibility of proposed local interpreter. |
| Installation | NOT CHECKED | Official installation method and full dependency/runtime impact; propose exact environment changes before installing. |
| Image input | NOT CHECKED | Actual accepted input forms, page/image requirements, limits and model/backend support. |
| Nullable fields | NOT CHECKED | Null/missing behavior and how it maps to explicit extraction uncertainty. |
| Scalars | NOT CHECKED | String/Decimal-like candidates, coercion/failure behavior; preserve raw text. |
| Enums | NOT CHECKED | Supported enum constraints, invalid-value handling and explicit observation states. |
| Line-item strategy | NOT CHECKED | Header then bounded line-region/row approach; row limits, missing/repeated row behavior. |
| Nested schemas | NOT CHECKED | Documented restrictions; do not assume native arbitrary recursive/nested table support. |
| Backend/runtime | NOT CHECKED | Required engines, API/protocol versions and supported deployment modes. |
| SGLang compatibility | NOT CHECKED | Whether required, exact compatible releases/commits and dependency constraints. |
| Model family/revision | NOT CHECKED | Official supported model family, exact revision, processor/tokenizer and input requirements. |
| GPU/CPU needs | NOT CHECKED | Supported hardware, memory/storage, CUDA/toolchain requirements and CPU feasibility. |
| Package/runtime licenses | NOT CHECKED | TypeLLM, backend and transitive runtime license obligations for intended use. |
| Model license | NOT CHECKED | Exact weights license, use/distribution limits and any required gated access. |
| Local/offline feasibility | NOT CHECKED | Artifact fetch/cache requirements, runtime network behavior and offline execution feasibility. |
| Latency | NOT CHECKED | Later measured hardware/model/input configuration, per-case elapsed time, warm/cold behavior and missing measurements. |
| Provider/data retention | NOT CHECKED | Local/hosted behavior, data transmission, retention/logging terms and permitted document use. |
| Source locators/bbox | NOT CHECKED | Whether page/box evidence is supplied, coordinate convention/transform mapping; absence remains explicit. |
| Malformed/timeout behavior | NOT CHECKED | Invalid/incomplete responses, retries/timeouts, error mapping and safe artifact references without private traces. |

P0-04B should produce a reviewable exact dependency/runtime plan and blockers before installation. P0-04C, if subsequently approved, must materialize suitable synthetic visual artifacts, version the manifest/input bindings, integrate a real adapter and execute the varied-document spike. The [structured harness](../data/extraction_spike/README.md) is reusable at the observation boundary; fixture agreement cannot substitute for those runtime checks. Parent P0-04 remains incomplete.
