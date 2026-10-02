# Phase 0 exit review — contracts and feasibility

Review date: 2026-10-03 (Asia/Kolkata). Final verification results are recorded below after execution. The latest user approval authorizes continuous completion of P0-04–P0-06 and explicitly accepts closure using the already verified external-runtime blocker. The authoritative specification remains unchanged. P0-05 permits fixture fallback when prerequisites are blocked; specification section 24 directs continued independent work. This approval qualifies the original P0-04 real-spike requirement; it does not claim that spike passed.

## Completion disposition

**PHASE 0 COMPLETE** after the recorded local exit checks. Real TypeLLM/VLM execution is **DEFERRED — INFRASTRUCTURE PREREQUISITE**. Development extraction is the **VERIFIED FIXTURE ADAPTER**; enterprise target is the **OPTIMIZED SHARED VLM INFERENCE SERVICE**. Phase 1 is not implemented or authorized by this closure.

| Task | Final disposition | Evidence / qualification |
|---|---|---|
| P0-01 | COMPLETE LOCALLY | Repository, exact spec copy, provenance, ignore rules and documentation preserved. Publication is a separate external authentication gate; one end-of-phase push authorized. |
| P0-02 | COMPLETE | Immutable Money/currency, explicit states and scoped evidence contracts; 241 domain unit/invariant tests. No business rules implemented. |
| P0-03 | COMPLETE | Reproducible 38 fictional root references and ten independent golden finance cases; 123 fixture/operand tests. Expected decisions are data, not evaluation outputs. |
| P0-04 | CLOSED WITH EXTERNAL RUNTIME DEFERRAL | ExtractionAdapter, deterministic fixture adapter, ten structured extraction cases, comparison harness, 124 extraction tests, compatibility research and observed prerequisite gate. Real image spike did not run. |
| P0-05 | COMPLETE FEASIBILITY CONSOLIDATION | Final [compatibility matrix](extraction_compatibility.md#p0-05-final-compatibility-matrix), exact research pins, null/row/money/evidence limitations, licenses/hardware/latency disposition. No production-approved tuple. |
| P0-06 | COMPLETE DESIGN DECISIONS | ADR-0003–0008: identity, effective policies, durable jobs/outbox, private storage, RULES_ONLY finance-risk mode, optimized shared inference. Services remain future implementation. |

```text
REAL_RUNTIME_EXECUTION = BLOCKED_EXTERNAL_PREREQUISITE
FIXTURE_ADAPTER = VERIFIED
PROVIDER_CONTRACT = VERIFIED
COMPATIBILITY_RESEARCH = COMPLETE
REAL_IMAGE_QUALITY_AND_LATENCY = DEFERRED UNTIL SUITABLE GPU RUNTIME
```

PROVIDER_CONTRACT means the locally tested provider-independent boundary. It does not mean a real TypeLLM implementation was integrated or image validated. P0-04C1 completed the prerequisite assessment; its text/image smoke is NOT RUN and P0-04C2 is deferred.

## Specification exit criteria

| Exit criterion (specification section 21) | Status | Verification and practical limit |
|---|---|---|
| Versioned contracts | SATISFIED | Git-versioned P0-02 foundation, extraction-v1, explicit fixture/schema/report/adapter versions and hash-pinned datasets; [catalog](data_dictionary.md#phase-0-contract-version-catalog). Existing Money/uncertainty/evidence/extraction code and tests unchanged. No unversioned speculative router fields added. |
| Compatibility notes | SATISFIED | Twenty original researched topics plus final P0-05 matrix, immutable pins/source references, observed driver/Docker gate, explicit unsupported schemas/bbox and unavailable metrics. Source evidence is not local inference proof. |
| Reproducible synthetic fixtures | SATISFIED | Existing 23 finance JSON and 11 extraction JSON checksum sets, stable normalized digests, ten-case deterministic fixture replay, independent annotations and preserved golden expectations. No visual accuracy claim. |
| No unsupported provider assumptions | SATISFIED | Research pins distinguished from production approval (NONE); image compatibility/quality, latency/VRAM, quantization, cascade, transitive licenses and live provider terms remain explicit gates. Typed answers cannot authorize finance decisions; no fabricated bbox, money float, confidence, throughput or success. |

Money stays exact Decimal with currency; missing/ambiguous data never becomes zero or PASS. The canonical provider-independent boundary is replaceable. Normal development needs no GPU/cloud/paid provider. Shared inference separates finance laptops and the CPU control plane from future GPU workers. All four gates are satisfied under the explicitly approved external-runtime qualification; real inference measurements remain deferred, not completed or a failed product requirement.

## Acceptance and business coverage review

The specification's AC01–AC20 are full-product release criteria. Phase 0 provides foundations only; none is claimed satisfied as an end-to-end release criterion. T01–T42 remain **42 NOT IMPLEMENTED**, with no automated finance behavior paths. TEST FIXTURE READY means prepared synthetic operands/expectations; BUSINESS BEHAVIOR IMPLEMENTED requires actual production workflow and tests.

| Acceptance criterion | Phase-0 support and remaining release work |
|---|---|
| AC01 | Vendor/employee fixtures exist; persisted branch workflows unimplemented. |
| AC02 | Policy/reference fixtures prepared; deterministic screening/control implementation pending. |
| AC03 | Evidence types and source slots tested; actual findings and factual visual evidence pending. |
| AC04 | Explicit states/unknown invariants stable; complete PASS eligibility/finalization pending. |
| AC05 | Review decision vocabulary exists; review queue/UI/actions pending. |
| AC06 | Duplicate operands/candidate expectations prepared; identity/normalization and duplicate analysis pending. |
| AC07 | Versioned evidence foundation; persistent correction/history trace pending. |
| AC08 | Terms documented in contracts/README; application terminology/workflows pending. |
| AC09 | All T01–T42 remain NOT IMPLEMENTED; core deterministic/concurrency/security tests cannot be waived for production. Prepared fixtures do not satisfy the mandatory matrix. |
| AC10 | Scoped UUID/evidence contracts and identity ADR; server authorization/RLS/role isolation pending. |
| AC11 | Durable/idempotent design chosen; concurrent resource/finalization implementation and tests pending. |
| AC12 | Version lineage/audit design chosen; persistence and replay pending. |
| AC13 | Explicit extraction errors/uncertainty boundary and outage design; actual provider/reference outage routing pending. |
| AC14 | Synthetic-only inputs, no inference uploads or credentials; real-data authorization, retention and private-service security verification pending. |
| AC15 | TypeLLM research/pins/limitations recorded; actual image integration and benchmark DEFERRED — REQUIRES SUITABLE INFERENCE HOST. |
| AC16 | Initial RULES_ONLY risk decision accepted; actual visible NOT_CONFIGURED report and any validated ML metrics pending. |
| AC17 | No ML/explanations invented; SHAP only after a valid risk model, later phase. |
| AC18 | Fixture CLI/tests reproducible; application setup/migrations/seeding/backup/restore pending. |
| AC19 | Proposed targets distinguished from measurements; actual application and inference performance pending. |
| AC20 | Enterprise planes/profiles documented; pilot identity, deployment, monitoring, rollback and operations verification pending. |

[Coverage](test_coverage.md) preserves every original scenario and expected result. [Inference architecture](inference_architecture.md) records planned optimization without asserting deployed behavior.

## External gate and deferred work

The observed 2026-10-03 01:11:59 IST gate found NVIDIA driver **550.120**, while the proposed SGLang CUDA **13.0.3** path requires supported **>=580**. Docker CLI 29.1.3 exists, but daemon access is **permission denied**. GPU passthrough and actual DockerRootDir are **NOT VERIFIED**; observed filesystem capacity is adequate. Classification is **BLOCKED_DRIVER** with independent **BLOCKED_DOCKER_ACCESS**, stage **ENVIRONMENT_FAILURE**, image **IMAGE_PATH_NOT_RUN**. See the immutable [observed appendix](typellm_spike_plan.md#p0-04c1-observed-prerequisite-gate). This closure did not repeat the gate, install/download inference or change the host.

| Deferred gate | Status / requirement |
|---|---|
| Actual TypeLLM image smoke and full ten-case real-model benchmark | DEFERRED — REQUIRES SUITABLE INFERENCE HOST; separately authorize a compatible GPU host and controlled synthetic visual benchmark. |
| Measured critical-field quality, uncertainty and rows | DEFERRED — REQUIRES SUITABLE INFERENCE HOST and independently annotated actual visual inputs. Fixture replay cannot substitute. |
| Inference latency / cold start / throughput | DEFERRED — REQUIRES SUITABLE INFERENCE HOST; preserve unavailable values, compare targets only after measurement. |
| Loaded/peak model VRAM | DEFERRED — REQUIRES SUITABLE INFERENCE HOST; inventory VRAM is not model usage. |
| Quantized-model quality benchmark | DEFERRED — REQUIRES SUITABLE INFERENCE HOST; officially supported formats compared with higher-precision baseline. |
| Native-text routing / page-crop / model cascade benchmark | DEFERRED — REQUIRES SUITABLE INFERENCE HOST and later preprocessing/router implementation; measure whole-system quality and routing misses. |
| Live pilot permissions/terms/security/licenses | FUTURE LIVE-PILOT GATE; authenticated scope, retention/egress, complete transitive licenses, real-data permission and provider contracts remain unverified. |

These gates do not invalidate the tested local contracts or accepted enterprise architecture. No model/tier/quantization is production approved; the image-unverified Qwen3.5-4B remains a research candidate. The proposed optimized services and RULES_ONLY reporting are not implemented.

## Executed verification

| Exact command/check | Exit / result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | 0; **488 passed, 0 failed, 0 skipped**, 0.43s. No tests/code changed. |
| `sha256sum -c docs/source_inputs.sha256` | 0; 9 original inputs OK. |
| `sha256sum -c data/synthetic/fixtures.sha256` | 0; 23 finance fixture JSON files OK. |
| `sha256sum -c data/extraction_spike/fixtures.sha256` | 0; 11 extraction JSON files OK. |
| `cmp docs/AP_Exception_Assistant_Codex_Spec.md AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md` | 0; byte-identical 123,229-byte specification copy. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/benchmark/extraction_spike.py --dataset data/extraction_spike --output generated/reports/phase0-fixture.json` | 0; ten-case fixture report created outside tracked source. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_phase0.py` | 0; 16-doc scope, 187 local links/anchors, original T01–T42 preservation, all AC01–AC20 review dispositions, unchanged 20-topic research snapshot, 26 final compatibility requirements and actual contract-version catalog verified. |
| Same audit: reproducibility and development independence | Both stable fixture digests verified; repeated replay matches CLI except runtime timestamp. Ten application modules use stdlib/project imports and Python 3.10-compatible syntax. All 16 captured package states unchanged; no inference environment/experiment directory. |
| Same audit: artifact/limited security inspection | Generated report/model paths ignored; no common key/token patterns in changed documentation. Not a full security certification. |
| `git diff --check` | 0; no working-tree whitespace errors. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_phase0.py --final` | Exit 0; qualified Phase-0 completion, four exit criteria and Phase-1 boundary verified. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/audit_phase0.py --staged` | Exit 0; exactly 16 intended documentation files staged; no unstaged tracked changes; all link/scope/version/preservation checks pass. |
| `git diff --cached --check` | Exit 0; no staged whitespace errors. |

Fixture-only report: 10 attempted/completed cases, 130/130 state agreement, 7/7 expected abstentions, 12/12 rows, 48/48 important row values, 130 declared page locators and zero boxes; bbox ratio null. Adapter latency has zero available observations and null min/max/mean. These demonstrate replay/comparison behavior only, not real image accuracy or factual locator correctness. Finance digest is 1fdd167453d530ad286dbb633ed1e0abb5051f61b38b08bfd3b13a6ba52550b6; extraction manifest digest is db00315130436eb572065cad35b1b00edcb2c8058dad84ea862de5975387bd0a.

The final/staged documentation audit and staged whitespace review are recorded in progress before publication. No command in the gated runtime plan was executed during closure; no UI/database exists to inspect.

## Publication and next boundary

The end-of-phase publication policy authorizes exactly one normal main push after local verification, with no credential repair or force-push. Its actual outcome and final SHAs belong in [progress](progress.md) and the completion report. Authentication failure can leave Phase 0 complete locally with clean commits; it is distinct from extraction runtime deferral.

Recommend only the first major Phase-1 batch: **P1-01 — API/frontend scaffold, PostgreSQL migrations, local storage adapter and durable jobs/outbox foundation**, using explicit fixture development extraction and planned RULES_ONLY risk configuration. Implementation requires new approval. No Phase-1 code or deployment was created by this review.
