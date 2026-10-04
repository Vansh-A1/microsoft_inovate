# ADR-0015 — Current-driver-compatible experimental invoice extraction

Status: accepted for the user's 2026-10-04 priority override and local experiment.

The priority override authorizes isolated model/runtime downloads and application
integration on the existing machine. It supersedes the earlier prohibition on
running local inference for this task. It authorizes no host changes, cloud
deployment, Git publication, production licensing decision or finance-rule change.

## Decision

Run `Qwen/Qwen2.5-VL-3B-Instruct`, revision
`66285546d2b821cf421d4f5eb2576359d3770cd3`, in BF16 using SGLang
`0.4.6.post5`, PyTorch `2.6.0+cu124`, Transformers `4.51.1` and the wheel's
CUDA 12.4 runtime. This actually executes on the RTX 2000 Ada Generation
(16,380 MiB, SM 8.9) with the unchanged NVIDIA 550.120 driver. Docker socket
access is still denied. The earlier CUDA-13 tuple cannot run on that driver;
an ordinary-user Python 3.12.3 environment avoids Docker and host upgrades.

Keep TypeLLM `0.5.1` in a separate CPU Python 3.12.3 client environment with
Transformers `5.3.0`. Its dependency requirements conflict with the serving
environment's Transformers version. The existing Python 3.13 finance environment
retains its dependencies. The application calls an authenticated HTTP gateway
through its existing ExtractionAdapter boundary. TypeLLM's actual compiler,
finite-state selection and SGLang inference remain in the real path.

The transport bridge handles three measured incompatibilities: greedy requests
omit the unsupported legacy `sampling_seed`; single-token label IDs come from
the identical pinned local tokenizer instead of absent tokenization endpoints;
multimodal batches become ordered actual single requests because the legacy
server exhibited a batch completion/cache race. Provider field names use
`observation_status` to avoid the small model interpreting `state` as a US state.
They map back to the unchanged five-state application contract.

One resident model handles multiple documents. The gateway serializes generation
and flushes the backend cache before and after each call. A failed post-call
flush poisons the gateway and blocks further calls until restart. This deliberately
trades throughput for isolation and reliable legacy serving. SGLang's unauthenticated
backend is loopback-only and unsuitable as a shared multi-user host service.

## Evidence and routing

Actual raw vision inference, TypeLLM text/image smokes, header extraction and three
visible invoice rows succeeded. Five actual source variants were measured through
the application adapter. Full live upload/normalization/correction/finance tests
are recorded in the [acceptance record](../real_vlm_acceptance.md). They assert
real provider metadata and cannot pass using fixture answers. Expected values
are compared only after inference; document content is never an instruction source.

Native/OCR mapping sufficiency now checks critical header and invoice row coverage,
rather than assuming that high text coverage or a parsed total is sufficient.
Complete native PDFs retain their cheap path. Incomplete mapping reaches visual
inference; independent disagreements and unresolved arithmetic require input.
Known multi-invoice segmentation uncertainty requests human confirmation directly.

Uniform ruled tables can use measured header-plus-row composite crops after their
row count agrees with actual inference. Extents, offsets, dimensions, hashes and
the parent transform are retained. Crop extents are not field boxes: VLM fields
retain `bbox=null`. Receipt lines remain optional; a receipt with no explicit
table candidates uses one bounded header call rather than inventing summary rows.

## Integrity and limitations

Money remains nullable printed strings, then the existing trusted Decimal
normalizer. No inference endpoint accepts finance decisions. Old originals,
observations, transaction versions, evaluations and finance controls are preserved.
Missing native observations cannot downgrade a visual AMBIGUOUS/ILLEGIBLE state.

The small model confused net and gross amounts in compact pipe tables and can
invent semantic fields. Arithmetic validation and source review remain mandatory.
No confidence percentage, universal accuracy, automatic approval or production
availability claim follows from this five-variant smoke. The Northstar file was
not found; the available user-supplied invoice was used as permitted.

The actual pinned checkpoint includes the **Qwen RESEARCH LICENSE AGREEMENT**;
it is not an Apache-2.0 model. This selection is an experiment, not approval for
commercial deployment or redistribution. Production model licensing, representative
quality evaluation, private hosted serving and capacity remain separate gates.
See the [pinned upstream license](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct/blob/66285546d2b821cf421d4f5eb2576359d3770cd3/LICENSE).

All weights, environments, caches, credentials, private documents and raw reports
remain in ignored user-owned paths. Local extracted development headers solve the
missing Python.h build prerequisite without installing an OS package; eager mode
avoids torch.compile. No NVIDIA driver, host CUDA, GPU configuration, system Python,
Docker configuration or administrator package was changed. No sudo was used.

## Reproducibility

[Local inference runbook](../runbooks/local-inference.md) describes pinned assets,
separate environment locks, configuration, start/health/stop and opt-in tests.
This ADR supplements ADR-0008's separate CPU/inference planes and supersedes the
historical local-runtime deferral for this tested tuple only. Historical Phase-0
research and exit records remain unchanged.
