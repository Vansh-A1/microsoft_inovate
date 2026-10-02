# ADR-0008 — Optimized shared enterprise inference

- Date: 2026-10-03.
- Status: Accepted architecture direction; serving, router, crop detector and production model selection are future work.
- Basis: latest user-approved Phase-0 closure; specification sections 3–4, 18–19 and P0-06.

## Decision

Keep TypeLLM + compatible VLM + SGLang as the intended enterprise structured extraction stack, isolated behind ExtractionAdapter. Finance laptops require only the supported client/browser, with no CUDA, weights, TypeLLM, SGLang or GPU Docker. CPU-friendly control-plane services own authentication, API, database, deterministic finance rules, approvals, budgets, audit/review/reporting and durable work status. Separately scalable inference workers/services own preprocessing, model clients, caches and GPU serving.

Adopt selective routing: trustworthy native PDF text → cheap structured extraction → small VLM only when required → stronger fallback only for unresolved supported facts → explicit unresolved observations/human review. Routing evaluates source quality, coverage, family/layout/row complexity, critical-field sufficiency, resource budgets and availability under a versioned policy. It never decides PASS/REVIEW/HOLD. A stronger model does not automatically resolve disagreement or outrank source evidence.

Use bounded pages and actually detected crops/regions (header/totals/reference/table/receipt) rather than whole documents at maximum resolution. No crop detector/coordinates are invented. Preserve the existing immutable observation/state/source contract, string-only money boundary and missing bbox. Future routing/attempt/transform metadata is a versioned sidecar; no speculative keys are added to strict extraction-v1 payloads.

Load each selected model once into a persistent service and share requests through the async queue; do not reload per invoice. Benchmark supported scheduling/continuous batching with tenant isolation and bounded memory/concurrency. Independently scale worker/model pools; future autoscaling may use queue depth, warm capacity and cold-start/cost budgets. It is not a zero-cost serverless GPU promise.

Model tiers and quantization are selected by representative comparative benchmarks: critical fields, abstention, row coverage, factual locators, latency/cold start, throughput, peak VRAM, weight size, operational cost/complexity and precision degradation against a higher-precision baseline. FP8/FP4/INT4/AWQ/GPTQ are candidate formats only when the chosen model/runtime officially supports them. No production model or quantization pin is approved; Qwen3.5-4B remains a text-tested, image-unverified research candidate.

## Consequences and rejected alternatives

Reject GPU dependencies on finance laptops, synchronous long browser inference, a blind full-document VLM call, biggest-model selection and live-outage fallback to synthetic fixture answers. FIXTURE is the verified synthetic development implementation; ENTERPRISE_VLM is a future deployment mode. TEXT_FAST_PATH is a routing path, not a finance-risk mode.

P0-04/P0-05 close under the verified external-runtime deferral allowed by the latest approval. This accepts the architecture/contract boundary, not real image quality or latency. No inference environment or new model is installed/searched, and no Phase-1 service is scaffolded. [Inference architecture](../inference_architecture.md) specifies metadata/safety/benchmark profiles; [phase exit review](../phase0_exit_review.md) records the qualified completion and deferred gates.
