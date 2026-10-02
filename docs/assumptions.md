# Assumptions and external inputs

This register separates proposed development defaults, currently missing inputs, and observed environment facts. None establishes a live company's finance policy or a production capability. Basis: [specification](AP_Exception_Assistant_Codex_Spec.md), repository reconnaissance, and the user's Phase-0 approvals and continuous Phase-1 approval on 2026-10-03.

## Business defaults and missing inputs

| Item | Current basis/status | Required before live use |
|---|---|---|
| Data | P0-03 adds 38 fictional root references and ten independently adjudicated golden alternatives. Source documents are JSON facts only, with no real documents or extraction claims. | Authorized representative documents/data and permitted uses. |
| Company/entity scope | All fixture finance activity uses one fictional entity/cost center. A second entity and second tenant's entity are sentinel scopes for malformed-link tests. Phase 1 implements server-side authorization and forced PostgreSQL tenant/entity policies. | Actual entities, visibility, and policy owners. |
| Currency/tax | P0-03 is explicitly INR-only; its 18% tax, hotel/meals/taxi limits and half-open approval bands are labeled demo arithmetic/configuration. No FX was needed or invented. | Approved currencies, jurisdiction/tax/rounding/FX policies. |
| Finance policy | No real company policy or approved authority matrix is supplied. | Signed-off control, approval, waiver, and separation-of-duties rules. |
| Payment execution | Outside the initial scope; none exists. | Separate explicit design and authorization for any future integration. |

## Technical defaults and unverified work

| Item | Current basis/status |
|---|---|
| Architecture | The specification proposes Next.js/TypeScript, FastAPI/Pydantic, PostgreSQL, shared Python finance logic, local storage and durable PostgreSQL jobs/outbox initially, and private Azure storage later. ADR-0003–0008 accept those decisions and separate CPU control plane from shared GPU inference. The CPU services now run locally; inference remains deferred. |
| Extraction | P0-04A implements provider-independent contracts and deterministic fixture response replay. It observes no actual document pixels and does not normalize or decide financial eligibility. |
| Extraction spike data | Ten structured synthetic cases declare raw/candidate/state/row ground truth separately from replay responses. Poor text, rotation, obstruction and repeated headers are annotations/metadata, not generated or processed visual artifacts. Page references are synthetic declarations; all bbox/artifact slots are null. |
| Spike metrics | Fixture agreement is expected by construction, not an independently measured extractor's accuracy. Absent candidates, abstention denominators, locators and adapter timings produce null metrics where unavailable. Locators measure availability only, not factual correctness. |
| TypeLLM/VLM | P0-04B verifies official interfaces/revisions and proposes an isolated experimental 4B image tuple; end-to-end compatibility, image quality, row discovery and latency remain unverified. Recorded image-tested 27B derivative exceeds local VRAM; CUDA 13/host driver and Docker access block the selected plan. No provider installed. See [spike plan](typellm_spike_plan.md). |
| Deterministic controls | P0-02 implements immutable standard-library state, exact-decimal Money/currency, and evidence contracts. Phase 1 adds pure typed controls, screening, immutable records and atomic guarded finalization. |
| Fixture conventions | P0-03 uses fixed UUIDs, version 1, half-open reference dates, fixed UTC evaluation time, exact decimal strings including night quantities, and independent case snapshots. Test-only validation and operand assertions are not production transaction schemas or evaluators. |
| Finance-risk ML | Initial RULES_ONLY mode is accepted design: risk model NOT_CONFIGURED, no score/zero-risk fallback. Phase 1 implements reports and rules in authorized RULES_ONLY mode. Extraction VLM is independent; no adjudicated training data or trained risk model exists. Synthetic tests do not establish generalization. |
| Operational readiness | No latency, extraction-quality, availability, backup, or restore target has been measured. Targets in the specification are proposals. |

## Historical Phase-0 environment observations

Observed in the checked shell/Python environment on 2026-10-02–03. These are not project lockfile selections or compatibility approvals; an executable missing from PATH may exist elsewhere.

| Tool/package | Observation |
|---|---|
| Python | 3.13.11 (`/opt/conda/bin/python3`). |
| Git | 2.43.0; an existing author/committer identity is configured. |
| GitHub publication | The initial and single consolidated Phase-0 HTTPS pushes returned exit 128: `fatal: could not read Username for 'https://github.com': terminal prompts disabled`. Phase 0 is complete locally at a5d09b7b7192e8829f4e4ac0adf28affd2bdf3e1; publication is blocked by authentication. No credentials/configuration were changed or push retried; no remote SHA/file verification is claimed. |
| pytest | Installed, version 9.1.1 in the checked Python environment; P0-01 found no tests, and P0-02 introduces domain unit tests configured by root `pytest.ini`. |
| FastAPI / Pydantic | Installed environment distributions: 0.137.1 / 2.12.4. No project dependency manifest or compatibility test exists; neither is used by the P0-02 domain modules. |
| Node / npm | Not available on the checked PATH. |
| SQLAlchemy / Alembic | Not installed in the checked Python environment. |
| Docker | CLI 29.1.3; P0-04B daemon/image metadata commands return exit 1, permission denied at /var/run/docker.sock. GPU passthrough/configuration NOT YET VERIFIED. NVIDIA container tools 1.20.0 available; no configuration changed. |
| Docker Compose | `docker compose version` returned exit 1, unknown command. |
| PostgreSQL tools | `psql` not available on the checked PATH; no project database exists. |
| uv / GitHub CLI | Not available on the checked PATH. |

No dependencies were installed in Phase 0. P0-04B proposes conditional experiment pins; they are not installed project dependencies. Production domain/extraction modules and fixture support use the standard library and existing contracts; pytest uses the preexisting environment. Source syntax targets Python 3.10, but execution is verified only on Python 3.13.11. No project dependency manifest or tested GPU compatibility claim is introduced. Subsequent runtime setup must use separately approved suitable infrastructure. Phase 0 closes with this explicit external-runtime deferral; it is not an inference validation. The [compatibility checklist](extraction_compatibility.md) preserves the original 20-topic source snapshot and adds the final P0-05 matrix. **RESEARCH PIN** differs from **PRODUCTION APPROVED PIN: NONE**; no proposed tuple has executed. Read-only inventory records Ubuntu 24.04.2, 20-core Intel Ultra 7 265, 62 GiB RAM (43 available), one 16,380 MiB RTX 2000 Ada GPU/SM8.9, driver 550.120/CUDA driver capability 12.4, nvcc NOT AVAILABLE, /data ~790 GiB free and root/home/tmp ~238 GiB free. Existing Torch 2.10.0+cu128 can enumerate CUDA; that does not verify SGLang CUDA 13. Python 3.12.3 lacks ensurepip/pip; proposed inference uses container Python 3.12. Full version/source/storage details are in the [plan](typellm_spike_plan.md). P0-04C1 executed only the prerequisite gate: driver 550.120 / supported >=580 requirement and Docker access denial; text/image smoke NOT RUN. Current gate had 42 GiB available RAM; prior research inventory had 43 GiB. P0-04C2 and real extraction measurements are deferred to suitable infrastructure; no gate rerun during closure.

## External dependencies

- Azure subscription, deployment destination, region, access, and budget have not been supplied. No resources were provisioned.
- Authorized ERP/vendor/employee/PO/GRN/master sources and freshness requirements are not available.
- Production identity/role mapping, retention, legal-hold, provider data terms, and real-data permissions remain external inputs.
- The user selected [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate) and authorized initial baseline publication plus one consolidated Phase-0 end push to `main`; remote publication status belongs in [progress](progress.md).

Record future decisions or changed observations with evidence. Do not replace an unresolved input with a permissive value or represent a planned adapter as implemented.

## Accepted enterprise assumptions and deferred validation

[Inference architecture](inference_architecture.md) and [ADR-0008](adr/0008-optimized-enterprise-inference.md) keep TypeLLM/VLM/SGLang on shared enterprise GPU serving. Finance-user laptops need only supported client/browser access, with no GPU runtime. CPU-only fixture development needs no cloud account, model download or paid provider. The current developer host need not be repaired to finish Phase 0.

Reliable native text can use a cheap structured path; visual calls, actual bounded pages/crops, small/stronger tiers, persistent models, supported batching, private caches and independent worker scaling are future implementations. ExtractionRouter chooses a path under versioned source-quality/evidence criteria and cannot make a finance decision. Provider outage preserves incomplete/uncertain work and cannot create PASS or synthetic live answers. Future autoscaling balances queue depth, warm capacity, cold starts and cost; no zero-cost GPU claim.

Actual crop detection/transforms, real field-coordinate correctness, provider null/row/failure mapping and tier/quantized quality are unverified. FP8/FP4/INT4/AWQ/GPTQ are possible benchmark families only if officially supported by the selected tuple, compared with higher-precision baseline. Qwen3.5-4B is not production approved. All real image quality, latency, VRAM, throughput, quantization and cascade measurements are **DEFERRED — REQUIRES SUITABLE INFERENCE HOST**, with benchmark requirements in the architecture. Proposed specification targets remain targets.

At Phase-0 closure, identity/authenticated scope, effective policy ambiguity handling, durable/idempotent jobs and private immutable storage were accepted [P0-06 decisions](phase0_exit_review.md), not live services; Phase 1 now implements the bounded local subset. Production permissions, actual finance policy, live data/provider terms and complete transitive licenses remain gates. Phase-0 fixture-ready cases alone do not implement T01–T42 business behavior. Phase 1 was separately approved and its current executed coverage is recorded in the tracker.

## Phase-1 observed implementation and limits (2026-10-03)

- The tested host has project-local Node 24.21.0, PostgreSQL 16.15 and an isolated Python 3.13.11 venv. Earlier missing-tool observations above are historical Phase-0 reconnaissance, superseded for the CPU stack. There was no sudo, system installation or GPU gate retry.
- Exact dependencies are in `apps/api/requirements.lock` and `apps/web/package-lock.json`. TypeScript 5.9.3 satisfies the generated-client peer dependency; incompatible TypeScript 7 was not forced.
- INR ordinary exclusive-tax invoices and full-receipt ordinary employee claims are supported. Demo policies, tax/rounding/tolerances and trusted approval imports are synthetic. Foreign currency, credit/refund, partial/shared receipts, service acceptance and policy waivers/delegation remain unsupported without permissive PASS.
- Runtime storage, cluster data, generated credentials, reports and browser artifacts remain private/ignored. A file orphan after DB rollback is possible; storage reconciliation and production backup/restore are deferred.
- The UI uses a fixed trusted development FINANCE_REVIEWER token injected by the loopback server. It has no role/scope or approval-authority selectors. Enterprise SSO and complete human review/approval workflows remain later work.
- Minimal guarded capacity reservations prevent over-admission under tested concurrent budget/GRN scenarios. They are screening effects, not a full settlement/commitment transfer ledger.
- Bounded master/history queries fail explicitly when their configured ceiling is exhausted. There is no silent empty-history or SQLite application fallback. Full legacy/policy-change replay, operational SLAs and a deployed pilot are not claimed.

Phase-1 publication observation: the single authorized normal main push of verified implementation 49efc94a20afcbd633ea183c9548ada493bcb4fd returned exit 128 because Git could not obtain the HTTPS username (`terminal prompts disabled`). Local Phase 1 is complete. No retry/authentication repair occurred, and no remote SHA/file-set verification is claimed. See progress for the full actual outcome.
