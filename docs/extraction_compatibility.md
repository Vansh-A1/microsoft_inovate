# Phase 0 extraction compatibility

P0-05 feasibility consolidation is COMPLETE under the 2026-10-03 approved external-runtime deferral. P0-04 is CLOSED WITH EXTERNAL RUNTIME DEFERRAL; the fixture/contracts/research are verified, and real inference remains unexecuted. The original P0-04B research snapshot and P0-04C1 observations below retain their source-specific status. Exact sources and research pins are in the [spike plan](typellm_spike_plan.md); [exit review](phase0_exit_review.md) records the qualified closure. Source verification never establishes an executed provider compatibility test.

Status meanings: **VERIFIED FROM OFFICIAL SOURCE** establishes the stated upstream behavior; **VERIFIED LOCALLY** requires an executed local check; **NOT VERIFIED** identifies an unanswered compatibility/measurement question; **BLOCKED** identifies an observed prerequisite that prevents the selected experiment; **UNSUPPORTED** identifies a rejected interface feature. Source verification does not establish end-to-end compatibility. Each row has one primary status; its evidence column preserves qualifications.

## Original P0-04B research snapshot

The table below is the original twenty-topic source-verification snapshot, with unchanged counts; the final matrix below adds deployment/design dispositions. Historical next-task gates are superseded by the approved Phase-0 closure; the runtime deferral remains.

| Topic | Status | Evidence and consequence |
|---|---|---|
| TypeLLM identity/version | VERIFIED FROM OFFICIAL SOURCE | S1/S2: TypeLLM/TypeLLM, stable 0.5.1, tag v0.5.1, commit `0c34f00251f850b4cd1b8060f24dd7066522fb5d`; Apache-2.0, Python >=3.10. |
| Python support | VERIFIED FROM OFFICIAL SOURCE | S2/S8/S9: TypeLLM and SGLang declare >=3.10; selected container uses Python 3.12. SGLang offers cp312 x86_64 wheels. This does not verify the full dependency set on the host's Python 3.13. |
| Installation | BLOCKED | S8/S9/S14 and local inventory: selected SGLang 0.5.21 container uses CUDA 13.0.3, host driver is 550.120, Docker daemon access is permission-denied. Plan only; no packages/layers installed. |
| Image input | VERIFIED FROM OFFICIAL SOURCE | S3/S6: local files/bytes/PIL are encoded by client; HTTP/data URIs accepted. An upstream one/two-image smoke report exists for the precise RadixArk checkpoint. Smaller 4B image behavior is unverified. |
| Nullable fields | VERIFIED FROM OFFICIAL SOURCE | S4/S5: one scalar type plus null supported; null alone does not encode the five observation states. Conditional skips omit fields and appear in `skipped`; adapter must explicitly map them. |
| Scalars | VERIFIED FROM OFFICIAL SOURCE | S4/S5: string/int/float/bool outputs; `number` parses via float. Authoritative money must use raw string extraction, then later trusted Decimal normalization. No exact Decimal-output contract verified. |
| Enums | VERIFIED FROM OFFICIAL SOURCE | S4: bounded enums, maximum 24 alternatives; five explicit uncertainty states fit. Typed output does not prove the model chose the correct state. |
| Line-item strategy | NOT VERIFIED | No native table API established. Proposed bounded header → row discovery → per-row scalar calls, using existing 200-row/16-field limits; visual row discovery, repetition and truncation need P0-04C measurement. |
| Nested schemas | UNSUPPORTED | S4: object/array property types raise NotImplementedError in 0.5.1. The existing flat project row contract can be retained; do not send it as a nested TypeLLM schema. |
| Backend/runtime | VERIFIED FROM OFFICIAL SOURCE | S5/S16: self-hosted native SGLang `/generate`, `/model_info`, `/server_info`; hosted API is a separate keyed mode. Explicit loopback URL prevents implicit environment-key routing. |
| SGLang compatibility | NOT VERIFIED | S7/S8: upstream small-model evidence uses 0.5.19/transformers 5.12.1; proposed release is 0.5.21. Image report omits its engine version and checkpoint revision. The exact proposed tuple has not run. |
| Model family/revision | VERIFIED FROM OFFICIAL SOURCE | S6/S10–S13: Qwen3.8-27B documented image family; actual report uses RadixArk NVFP4/BF16-LMHead. Qwen3.5-4B is TypeLLM text-tested only and is the proposed smaller experimental target. Exact revisions/bytes in plan. |
| GPU/CPU needs | BLOCKED | Local 1×16,380 MiB Ada GPU cannot hold stock 27B BF16 or recorded mixed-precision checkpoint plus overhead. CUDA 13 driver gate fails. No documented CPU-only substitute established; smaller 4B fit is an estimate. |
| Package/runtime licenses | NOT VERIFIED | S2/S8/S17: primary projects declare Apache-2.0; CUDA has separate NVIDIA terms. Complete transitive/container license inventory and redistribution assessment remain unverified. No production licensing claim. |
| Model license | VERIFIED FROM OFFICIAL SOURCE | S10–S13: examined stock/FP8/NVFP4/4B cards and metadata declare Apache-2.0, public and ungated at inspection. Preserve license/notices and exact derivative provenance. |
| Local/offline feasibility | BLOCKED | S5/S9 and local inventory: explicit local tokenizer/cache/offline plan exists, but Docker/driver gates block launch. Offline execution, JIT cache completeness and egress remain unverified until tested. |
| Latency | NOT VERIFIED | No model executed or timed. Upstream hardware timings are not this machine's measurements. Current fixture adapter latency remains null. |
| Provider/data retention | NOT VERIFIED | S5 establishes local vs hosted routing, not hosted retention guarantees. No hosted account/key/contract inspected; no finance documents uploaded. Local logs and cache retention require explicit control. |
| Source locators/bbox | VERIFIED FROM OFFICIAL SOURCE | S3/S5 expose image inputs and typed answers, not a native OCR-coordinate result contract. Plan uses known one-page input provenance and bbox=None; coordinate capabilities false. Model-generated coordinates are not evidence. |
| Malformed/timeout behavior | VERIFIED FROM OFFICIAL SOURCE | S4/S5: SchemaError/NotImplementedError, SGLangError, GenerationTimeout/Cancelled documented in source. Cancellation checks between requests; immediate server abort is not guaranteed. Project mapping remains unimplemented. |

Counts for these **20 checklist rows**: VERIFIED FROM OFFICIAL SOURCE **11**; VERIFIED LOCALLY **0**; NOT VERIFIED **5**; BLOCKED **3**; UNSUPPORTED **1**. The separately executed hardware/package/fixture checks are VERIFIED LOCALLY in the plan and progress record; they do not promote provider rows to end-to-end compatibility.

Release gates: [string-only money boundary](adr/0002-extraction-money-and-provider-boundary.md), explicit uncertainty, reasoning suppression, truthful source locators, bounded rows, sanitized failures, pinned runtime and measured image checks. The current [fixture harness](../data/extraction_spike/README.md) remains operational and unchanged. No NOT CHECKED topics remain; no installation or next-task approval is implied.

## P0-04C1 observed prerequisite gate — 2026-10-03

Primary runtime classification **BLOCKED_DRIVER**; independent **BLOCKED_DOCKER_ACCESS**; failure stage **ENVIRONMENT_FAILURE**. Fresh local checks found driver 550.120 (approved CUDA 13.0.3 path requires supported >=580), Docker CLI 29.1.3 but docker info exit 1 with socket permission denial. Container tooling 1.20.0 is present; actual GPU passthrough and DockerRootDir remain NOT VERIFIED. Filesystem capacity meets the numerical reservations; complete Docker storage validation remains unresolved. These host observations are VERIFIED LOCALLY, not passing provider compatibility checks.

Image classification **IMAGE_PATH_NOT_RUN**; text smoke NOT RUN. No container/client/model download/install, environment/adapter/artifact setup, provider request, measured model latency/VRAM, reasoning validation or ten-case provider benchmark occurred. All 20 provider topic statuses/counts above remain unchanged; none is promoted to VERIFIED LOCALLY. The [observed-results appendix](typellm_spike_plan.md#p0-04c1-observed-prerequisite-gate) and [progress](progress.md) record exact commands and preservation checks. P0-04C2 did not run and is now deferred to separately authorized suitable infrastructure.

## P0-05 final compatibility matrix

**COMPLETE FEASIBILITY RECORD**, with fixture fallback functional and observed prerequisites explicitly blocked. VERIFIED UPSTREAM means the pinned official source establishes only that interface fact. DOCUMENTED OBSERVATION refers to the already executed host gate. ACCEPTED DESIGN is not implemented behavior. DEFERRED means no real measurement exists. Source IDs S1–S18 resolve through the plan's source registry; no new provider experiment was run.

| Requirement | Final status | Evidence and boundary |
|---|---|---|
| TypeLLM version | VERIFIED UPSTREAM / RESEARCH PIN | S1/S2: 0.5.1, immutable commit `0c34f00251f850b4cd1b8060f24dd7066522fb5d`; no installed or production-approved tuple. |
| Python requirement | VERIFIED UPSTREAM | S2/S8/S9: >=3.10 declared; selected image uses 3.12. Project fixture tests run on existing 3.13.11, not a GPU compatibility result. |
| Primary licenses | VERIFIED UPSTREAM, TRANSITIVE REVIEW PENDING | S2/S8/S10–S13: TypeLLM, SGLang and examined model cards Apache-2.0; complete container/transitive notices and NVIDIA terms remain a deployment gate. |
| Scalar/string output | VERIFIED UPSTREAM | S4/S5: bounded strings/int/float/bool; string default bound 128 tokens and scalar truncation require benchmark validation. |
| Nullable output | VERIFIED UPSTREAM | S4/S5: one scalar type plus null; conditional skips omit keys. Adapter must explicitly map five observation states, not assume missing means zero or valid absence. |
| Enum output | VERIFIED UPSTREAM | S4: <=24 alternatives; constrained syntax does not establish factual accuracy. |
| Image input | VERIFIED UPSTREAM | S3/S6: client local files/bytes/PIL and HTTP/data URI support; upstream image report uses the precise large RadixArk checkpoint, not the proposed 4B tuple. |
| Selected image runtime | BLOCKED LOCALLY / IMAGE PATH NOT RUN | Existing C1 gate: CUDA 13.0.3/driver mismatch and Docker access denial prevented install, model load and smoke. |
| Nested arrays/objects | UNSUPPORTED PROVIDER SCHEMA | S4: object/array properties raise NotImplementedError. Existing project flat rows remain provider-independent. |
| Monetary number output | UNSAFE FOR AUTHORITATIVE MONEY | S4: number parses via float. No Decimal(float), float amounts, guessed tax or invented FX. |
| Money string strategy | ACCEPTED DESIGN / CONTRACT VERIFIED | [ADR-0002](adr/0002-extraction-money-and-provider-boundary.md): raw string → later trusted normalization → exact Decimal/currency. Existing Money rejects floats; real provider mapping/normalization not implemented. |
| Bbox / field coordinates | NOT ESTABLISHED | S3/S5 provide no verified native field-coordinate contract. Current boxes None; known input-page provenance is not factual bbox accuracy. Future actual crop transforms cannot become guessed field boxes. |
| Line-item strategy | APPLICATION-MANAGED DESIGN | Bounded header/row discovery/per-row scalar calls; project <=200 rows/16 fields. No real row discovery/repetition/truncation quality measured. |
| Model compatibility | PARTIAL UPSTREAM EVIDENCE | S6/S7: small 4B is TypeLLM text-tested; proposed image path and exact SGLang 0.5.21 tuple unverified. Image-tested 27B derivative cannot establish 4B performance. |
| GPU requirement | DOCUMENTED OBSERVATION AND SIZE LIMITS | S9/S10–S14, C1: one 16,380 MiB Ada GPU; stock/mixed 27B weights exceed local VRAM. 4B fit is estimated, not a measured load. No verified CPU-only replacement. |
| Driver prerequisite | DOCUMENTED OBSERVATION / BLOCKED | S14 and C1: observed 550.120, proposed CUDA 13 requires supported >=580. Existing Torch CUDA enumeration does not validate this runtime. |
| Local host runtime | BLOCKED EXTERNAL PREREQUISITE | Docker info permission denied; passthrough and actual DockerRootDir unknown. Filesystem numerical capacity adequate; no gate rerun or host change. |
| Measured latency | DEFERRED — REQUIRES SUITABLE INFERENCE HOST | No TypeLLM/VLM timing exists; fixture adapter latency null. Proposed spec targets are explicitly separate from measurements. |
| Measured VRAM | DEFERRED — REQUIRES SUITABLE INFERENCE HOST | No weights loaded; loaded/peak VRAM unavailable. Hardware total/idle usage is not model peak. |
| Provider terms / retention | FUTURE LIVE-PILOT GATE | S5 distinguishes self-hosted/keyed hosted routing, not retention guarantees. No hosted keys/contract or real documents used; validate retention/egress/permissions before live use. |
| Backend / SGLang | RESEARCH PIN, TUPLE UNVERIFIED | S5/S8/S9/S16: intended native /generate integration, exact image digest/source recorded. Container dependency imports and image/model interaction unexecuted. |
| Failure / cancellation | VERIFIED UPSTREAM INTERFACE; PROJECT MAPPING FUTURE | S4/S5 document errors and between-request cancellation. [Jobs ADR](adr/0005-durable-jobs-and-isolated-workers.md) chooses explicit incomplete/failure handling; no immediate GPU abort guarantee or live fixture substitution. |
| Extraction quality / evidence correctness | DEFERRED — REQUIRES SUITABLE INFERENCE HOST | Replay validates contract/comparison logic only. Actual critical fields, abstention, row coverage and independently checked locators need visual benchmark. |
| Offline feasibility / privacy | PLANNED, UNVERIFIED | Explicit local base URL/tokenizer/offline cache plan; actual egress, cache completeness, retention, reasoning suppression and tenant isolation require execution. |
| Tier selection / quantization | ACCEPTED BENCHMARK DESIGN, UNMEASURED | [ADR-0008](adr/0008-optimized-enterprise-inference.md): small first, stronger fallback; officially supported FP8/FP4/INT4/AWQ/GPTQ only, compared with higher-precision baseline. No production model/format approved. |
| Enterprise serving / routing | ACCEPTED DESIGN, NOT IMPLEMENTED | [Architecture](inference_architecture.md): CPU control plane, shared persistent GPU service, native-text fast path, actual page/crop provenance, durable async jobs, supported batching, horizontal scaling and future warm-capacity autoscaling. |

## Pin approval boundary

**RESEARCH PIN:** TypeLLM 0.5.1, SGLang 0.5.21, source SHAs, container `lmsysorg/sglang@sha256:2dbe4c7f53230b09aaa8fa41891c13c51d9d2e253f486a70822aaf08783fff75`, proposed `Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, and planned client versions in the unchanged spike plan. They are reproducible research inputs, not an installed lockfile or successful inference tuple.

**PRODUCTION APPROVED PIN: NONE.** Real image quality/latency/VRAM, null/row/money/failure mappings, supported quantization/cascade, package/license inventory and privacy/operational gates must pass on suitable separately approved infrastructure. No assumption was filled by inventing a successful provider result. Qualified P0-05 completion records those findings and deferrals; it does not promote them to verification.

## Phase-2 application integration update — 2026-10-03

The historical research pins and external runtime observations above are preserved.
Phase 2 now implements bounded CPU preprocessing and native-first routing, actual
English CPU OCR, raw observations/normalization/source corrections and a remote
TypeLLMExtractionAdapter. The optional pinned 0.5.1 SDK generate contract uses flat
state/string questions and application-managed bounded page/row requests. Its
real wheel schema compiler accepted 42 flat header questions without inference.
Mocked generate tests exercise null/float/authority/timeout/disagreement behavior.
The transport requires an approved endpoint/model and preprovisioned local tokenizer
assets, with local-only loading; no tokenizer/model download or local serving occurs.

Actual CPU document results identify NATIVE_TEXT or LOCAL_OCR. FIXTURE replay is
separate and is never a provider-outage substitute. Routing/status metadata lives
in extraction-routing-v1 beside the unchanged strict extraction-v1 contract.
Unknown critical facts and uncertain table/segmentation coverage require input;
manual source verification remains mandatory for document-derived screening.
The router never chooses PASS/REVIEW/HOLD. The Phase-1 engine remains authoritative.

No enterprise model/endpoint is configured here. Live TypeLLM/SGLang/VLM execution,
GPU latency/VRAM/quality, production model selection, stronger model fallback,
actual crops, batching and quantization remain explicitly deferred to suitable
separately authorized infrastructure. The NVIDIA/Docker prerequisites were not
retested or repaired. Native/OCR synthetic measurements establish no live-model
accuracy. See the [Phase-2 exit review](phase2_exit_review.md) and
[local runbook](runbooks/phase2-local.md) for implemented behavior and limits.
