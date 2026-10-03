# Assumptions and external inputs

This register separates proposed development defaults, currently missing inputs, and observed environment facts. None establishes a live company's finance policy or a production capability. Basis: [specification](AP_Exception_Assistant_Codex_Spec.md), repository reconnaissance, and the user's Phase-0 approvals and continuous Phase-1 approval on 2026-10-03.

Later phase sections supersede earlier historical capability limits; they do not
change the original assumptions or pretend synthetic policy is company policy.

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

## Phase-2 verified CPU document boundary

Native extraction supports explicit labeled headers and pipe-delimited tables; arbitrary layout completeness is not claimed. Unknown coverage, date/currency ambiguity and disagreements remain unresolved. Actual PyMuPDF/Pillow/OpenCV versions are pinned in the lock. Project-local Tesseract 5.3.4 provides English CPU OCR; this is independently replaceable and can be absent (NOT_CONFIGURED). The 15-file actual synthetic corpus is a bounded development benchmark, not production accuracy evidence. Malware scanning is NOT_CONFIGURED in development; requiring it blocks processing. Source verification remains manual for document-derived finance eligibility. TypeLLM real service/model execution and all GPU metrics remain explicitly deferred; no driver/Docker/model provisioning occurred. Private blob orphans after rollback remain possible and are not silently treated as finalized documents.

Physical facts require trusted source confirmation and reference mapping. The
development UI supplies editable synthetic reference choices; it cannot assert
approvals. Source verification appends immutable facts linked to actual document
and transaction revisions. Critical corrections are re-normalized/validated and
reevaluated; raw observations and old evaluations remain intact. Other mandatory
controls can still HOLD or REVIEW. The Phase-1 engine is unchanged; separately
versioned DOC source reconciliation applies only to physical contexts.

Mapped imports require text money cells; numeric Excel money is rejected rather
than recovered through a binary float. Formulas remain raw invalid evidence and
are never executed. Actual linked document IDs are mandatory; a boolean attachment
claim or fixture fact does not prove a receipt. Multi-document roles and page
ranges exist; automatic invoice segmentation, shared receipt allocation and
duplicate decisions remain Phase-3/later work. Current scanner/parser/English OCR
and manual verification are local development boundaries, not production approval.

Phase-2 publication observation: the single consolidated normal main push of
verified implementation `87e24ca` returned exit 128 (HTTPS username unavailable,
terminal prompts disabled). No credential changes, push retry or alternate
publication occurred. Approval review blocked a later read-only remote branch
check under the no-retry instruction before execution. No further network attempt
occurred. Local completion is distinct from remote publication; remote SHA/file-set
verification is not claimed. See progress for the recorded outcome.

## Phase-3 finance boundary

P3-01–P3-06 are directly approved continuously. An explicit activated profile selects
28 versioned Phase-3 controls; the original pure 20-control evaluator remains for
retained contexts. Future evaluations pin reference versions and live cumulative
capacity at finalization. Current vendor restriction is rechecked under the same
scoped admission lock; it cannot mutate an older retained evaluation.

All master/authority/receipt/payment/contract/FX values remain fictional. The
additive catalog includes 20 vendors, 30 employees, 50 PO/GRN lines and 3 cost
centers. Its 200 structured inputs are explicitly unverified, not eligible cases.
The configured finance profile is INR-only. USD and fictional USD/INR rate facts
demonstrate reference handling; there is no automatic cross-currency arithmetic.
Credit/refund accounting and segmentation confirmation remain safely incomplete.

Fuzzy ratio and 64-bit pHash distance are individual candidate measurements, never
probability or authority. Initial pHash distance <=6, number cutoff 85 and 7-day
window are bounded synthetic configuration requiring independent validation.
Actual resize/JPEG/brightness/minor-blur tests and a different-purchase template
negative prove the stated candidate/abstention behavior, not general image accuracy.
Fingerprints use actual safe derived pages, retain versions/dimensions, and skip
low-information images. Synthetic JSON source facts have no uploaded preview.

Gross append-only budget and allocation lifecycles model screening exposure.
Consumption is an explicitly authenticated fictional ledger action, not payment
execution or ERP settlement proof. Scope-wide locking favors correctness over
parallel throughput; actual PostgreSQL concurrency tests cover budget, GRN and
duplicate admission plus simultaneous worker claim/approval mutation. Worker
claim, failure recording and document persistence follow the same lock order.
Production throughput, restore, availability and scale SLAs remain unverified.

Authenticated synthetic roles live only in ignored private files. The loopback
supervisor enables a server-defined identity picker; it does not accept arbitrary
actor or role claims. Explicit Finance Submitter permits reviewer intake on behalf
of claimants; other submitters require a valid scoped delegation. Preapproval is
an independently activated record with explicit PREAPPROVER master authority,
scope, category, currency, ceiling and business dates; a client flag cannot prove it.
Approval and waiver remain separate. Mandatory nonwaivable controls remain binding.

The final benchmark uses 10,000 generated PostgreSQL histories plus 200 structured
transactions in its disposable schema. Reported local warm measurements are
descriptive, not a production SLA. Native/OCR and TypeLLM boundaries are preserved;
live enterprise VLM remains **DEFERRED — BLOCKED EXTERNAL PREREQUISITE**. No GPU,
Docker, cloud, ML, SLA/review leases or Phase-4 operations were introduced.

Phase-3 publication observation: one explicitly authorized normal main push of
verified `34a0c2345333cf29c1d0e08aa9e787687bdd1b5d` returned exit 128 because Git
could not obtain the HTTPS username with terminal prompts disabled. No retry,
credential repair, alternate publication or force push occurred. Remote SHA/file-set
verification is unavailable; local completion is distinct from publication.

## Phase-4 operational boundary

- Reuse the existing review and durable-job systems, with additive owner/version
  and immutable action/operation facts. Optimistic conflict handling uses the
  existing scoped finance lock; no separate reviewer service or payment flow.
- Current eligibility is derived separately. Master/authority/commercial source
  version changes, new company-payment evidence, expiry and invalid reservations
  make retained PASS stale; historical results remain unchanged. Freshness checks
  conservatively inspect the retained scoped reference catalog, so some unrelated
  reference revisions can require reevaluation. No source-wide permission bypass.
- Manual recovery is limited to classified transient failures and two additional
  three-attempt cycles. Required VLM assets/runtime remain externally deferred.
  NOT_CONFIGURED scanner/risk/VLM status is never CLEAN, zero risk or success.
- Reconciliation is a bounded local inspector with guarded repairs. Missing
  reports/originals/previews need retained artifact recovery; orphan objects and
  pending user finalization are preserved and surfaced. No retention periods,
  deletion sweep, production backup restoration or worker heartbeat is claimed.
- JSON/HTML/CSV exports use scoped explicit export permission, private snapshots,
  digest checks and audit. PDF generation remains deferred without a separately
  verified renderer; source values are not changed by CSV escaping.
- Separate fictional operational/admin, auditor and review-manager identities
  preserve existing roles. Production identity/role provisioning and retention
  policies remain external inputs. No Phase-5 ML exists.
- Warm local performance over 100 computed synthetic cases is measured by the
  Phase-4 benchmark. It does not establish production throughput, SLA or inference
  performance.

Phase-4 publication observation: the single normal consolidated main push of
verified `55a0d5d32f98afceabfa92029a972f36fadc1ffc` returned exit 128 because the
HTTPS username could not be read with terminal prompts disabled. Local Phase 4
is complete. No credentials changed, push retried or alternate publication occurred;
remote SHA/file-set verification remains unavailable.

## Phase-5 intelligence boundary (2026-10-04)

- Entry inventory found 200 synthetic vendor inputs, a disposable 10k vendor
  history generator and zero taxonomy-adjudicated training labels. Neither routing,
  golden expected decisions nor reviewer corrections are supervised targets.
  **SUPERVISED_TRAINING_NOT_JUSTIFIED**. No fitted classifier, Isolation Forest,
  calibrated exception probability or SHAP is delivered. The authorized fallback
  is transparent statistical anomaly review; representative labels remain required.
- The 20-feature schema uses latest known versions strictly before cutoff, excludes
  the current UUID/all revisions and compares same-currency cohorts. Historical
  facts describe submitted transactions, not presumed clean or settled outcomes.
  Reference registration records server-observed availability now, never a client
  backdate. Later lifecycle, approval, settlement, disposition and feedback cannot
  alter an existing feature snapshot. Identifiers support joins/grouping/lineage
  only; names, accounts, contact data and protected attributes are excluded.
- History is bounded to 10k inputs and a usable statistical cohort requires five
  prior observations. Incomplete history, zero MAD, missing sources and incompatible
  currencies remain explicit. Policy ratios currently support PER_CLAIM and
  ELIGIBLE_NIGHT; daily/trip/month ratios stay missing until a cutoff-safe aggregate
  exists. Finance policy controls continue to evaluate those units independently.
- ROBUST_STATISTICAL produces a defined 0–100 anomaly score from median/MAD/amount
  ratios. The threshold of 60 and minimum shadow observation are development
  governance defaults, not calibrated probability, validated review capacity or
  sufficient production approval. Scoring only escalates PASS to REVIEW. Mandatory
  HOLD and existing REVIEW remain authoritative, including actual low-score tests.
- Default new scopes retain RULES_ONLY/null score. The local synthetic product can
  explicitly use RULES_PLUS_ANOMALY after independent approval and shadow evidence.
  Required unavailable scoring produces MODEL_UNAVAILABLE/null score and REVIEW
  where controls otherwise permit PASS. No implicit outage fallback or ML-only HOLD.
- Feedback is immutable evidenced adjudication with FINAL/PROVISIONAL quality.
  PASS audit sampling opens the existing review workflow without changing screening
  or inferring clean labels. Dataset origin remains server-owned synthetic; no
  client assertion can authorize representative data. Connected revisions/documents/
  duplicate groups cannot leak across chronological folds. Gate defaults are
  documented in the runbook and are not organization-specific training policy.
- Private JSON statistical artifacts bind dataset/schema/code/run/SHA-256. Code
  changes make incompatible artifacts unavailable rather than silently rescore.
  Replay needs retained compatible scoring code/artifact; unavailable old code is
  explicit failure. Training cannot activate, self-approval is rejected, deployment
  and rollback append versions and invalidate current eligibility pending screening.
- Monitoring records actual bounded distributions/missingness/feedback and may
  request evaluation. No online learning, automatic retraining, automatic promotion
  or institutional ML-data authorization exists. VLM runtime remains externally
  deferred. No Phase-6 deployment work has begun.

Phase-5 publication observation: the single authorized ordinary main push of
verified `6b84cd4f3bd0aee018aedd3793b99759e4006c34` returned exit 128 because the HTTPS username
could not be read with terminal prompts disabled. The local fallback exit is
complete; publication and remote SHA/file-set verification remain blocked. No
credential changes, retries, alternate publication or force-push occurred.

## Phase-6 approved local delivery assumptions

- Phase 6 authorizes P6-01–P6-04 together and permits explicit local delivery when cloud inputs are absent. No suitable Azure subscription/region/permissions/spend ceiling/approved identities/residency/private runner is available; actual provisioning, hosted authentication/Blob validation, container builds/publication and cloud recovery/rollback remain external gates.
- Bicep is the single Azure definition. Private CPU control services use managed identities/Key Vault and private data endpoints. Tenant/entity membership and worker scopes are approved server inputs; development identities are forbidden in enterprise mode. Actual network/TLS/EasyAuth/egress behavior must be tested on authorized infrastructure.
- Required database TLS and non-bypass business roles are enforced. Real Blob reads verify remote metadata/hash rather than trust a stale cache. Configured-but-unverified dependencies remain explicit. Ordinary finance reviewers cannot read infrastructure health.
- Business administration reuses immutable reference versions and typed existing ledger services. It cannot overwrite historical reports, edit arbitrary code or grant PASS. POLICY_ADMIN cannot activate masters or budgets, including replay after permission revocation.
- Local restore validation covers an actual disposable copy and private object hashes. Cloud point-in-time/object recovery remains a separate gate. No organization-specific retention period, SLA, spend, FX rate or production model has been invented.
- The existing code-bound anomaly artifact became incompatible with the release storage integration; an explicit governed RULES_ONLY deployment preserved all old scores. Compatible candidates/shadow/activation/rollback continue through existing governance. No classifier/SHAP or online learning is introduced.
- The single authorized ordinary main push occurs only after final local verification. Authentication failure is recorded without credential repair, retry, alternate publication or force-push.
