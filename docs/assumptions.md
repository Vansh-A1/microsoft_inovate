# Assumptions and external inputs

This register separates proposed development defaults, currently missing inputs, and observed environment facts. None establishes a live company's finance policy or a production capability. Basis: [specification](AP_Exception_Assistant_Codex_Spec.md), repository reconnaissance, and the user's Phase-0 approvals and continuous Phase-1 approval on 2026-10-03.

Later phase sections supersede earlier historical capability limits; they do not
change the original assumptions or pretend synthetic policy is company policy.

## Current real-extraction experiment — 2026-10-04

### Final continuous release

The approved Phase-5 fallback is complete: cutoff-safe features, transparent
statistical anomaly factors, feedback/dataset provenance and governed model
lifecycle. Synthetic history and development feedback do not justify a
supervised classifier. **SUPERVISED_TRAINING_NOT_JUSTIFIED** remains the actual
gate; no held-out classifier metrics, calibrated probability or SHAP is claimed.

The hackathon profile now starts the owned API/worker/frontend and accepted native
inference without Docker, checking actual model hashes/pins/GPU headroom and
authenticated health. An actual bounded outage/recovery drill verifies native
independence and explicit visual failure. Start/stop never migrate/reset financial
data or delete evidence/model caches. Eight computed entries cover six families
in a separate fictional tenant; the partial-delivery case has independent capacity.
Policies, references, approvals and amounts are synthetic demonstration data.

Live Azure is **BLOCKED_EXTERNAL_INPUT**: approved subscription, region, spend,
identities, network/residency and deployment authority are absent. IaC/contracts
and runbooks are delivered; private gateway secret injection is conditional on
explicit approval. No GPU/cloud resources are created. Commercial checkpoint
licensing and institutional acceptance remain external. Current measured checks
are in the [final project exit](final_project_exit_review.md); earlier sections
retain their historical facts rather than describing the accepted current runtime.

The priority override authorizes the isolated local experiment in [ADR-0015](adr/0015-current-driver-compatible-real-vlm.md).
Actual Qwen2.5-VL-3B BF16, SGLang 0.4.6.post5/PyTorch CUDA 12.4 and TypeLLM 0.5.1
now execute with driver 550.120 unchanged. Separate Python 3.12 serving/client
environments avoid changing the working finance application's Python 3.13 packages.
Docker remains permission denied. Local extracted Python headers are files in
runtime, not an installed OS package. No sudo or host/GPU/system change occurred.

The exact Northstar invoice was unavailable; the supplied actual table-invoice
image was used as the primary case. Five actual source variants include three
related synthetic invoice renderings and one synthetic receipt photograph.
They establish compatibility and specific observed field/row behavior, not
independent representative accuracy. The small model can confuse compact tables
and invent semantic observations. Critical ambiguity, provider disagreement and
arithmetic errors still require source-linked correction and new finance evaluation.

The pinned checkpoint's actual LICENSE is the Qwen RESEARCH LICENSE AGREEMENT.
Commercial use/redistribution, representative quality, shared private serving and
capacity remain unapproved external gates. Earlier assumptions describing local
inference as unavailable apply to their historical tuples; the current measured
experimental tuple is operational. No classifier/SHAP or cloud gate is changed.
Private originals, outputs, keys, caches and weights remain outside Git. See the
[measured acceptance record](real_vlm_acceptance.md) and [runbook](runbooks/local-inference.md).

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

## ClearLedger hardening inputs — 2026-10-04

The three-layout benchmark is lawful generated synthetic content, frozen before
extraction development with one reserved layout. A 100% checked-value match on
this tiny set is not representative invoice accuracy. Cold/warm measurements are
separate; whole-device GPU usage includes other processes. The supplied invoice
still has date/currency and OCR glyph uncertainty. Missing tax semantics are not
inferred into canonical finance facts. See [the measurement record](clearledger_hardening.md).

ClearLedger local entry selects existing fictional server identities; it is not
an actual production SSO deployment. Synthetic policies remain visibly fictional
after business-form versioning. Company-approved masters/policies are not supplied.
No scanner executable/definitions were installed or configured. The new local
ClamAV adapter is a tested integration contract; production scanner/signature
acceptance is still external. A stronger inference provider and commercial use of
the research checkpoint remain unapproved. The accepted BF16 runtime and finance
Python 3.13 environment are unchanged. No Git push or deployment is authorized
for this delegated milestone.

Concurrent full fresh-schema regression and browser mutations exposed slow local
PostgreSQL writes: read-only activity showed CREATE TABLE waiting on
DataFileImmediateSync while some UI mutations exceeded existing timeouts. The
worker recovery fix keeps services alive, but does not establish throughput under
that load. Final functional browser checks run separately after the database suite;
production storage/capacity acceptance and suitable-infrastructure load validation
remain unproven. No host/database durability setting is weakened to accelerate tests.

## CL-04/CL-05 measured continuation — 2026-10-04

The twelve-source challenge was invented/frozen before tuning on 88f3559. Six
reserved layouts were opened after tuning. Shared fictional vocabulary/values
do not establish customer-distribution independence. Raw provider results and
the supplied invoice remain private/ignored. h01 incomplete rows and h04 wrapped
disagreement remain failures, not tuned-away reserved successes.

The optional CPU experiment installed one isolated 25-package environment:
RapidOCR 3.9.2/CPU ONNX Runtime 1.23.2, verified package/model hashes and actual
CPU providers. Finance Python and ADR-0015 inference pins remain intact.
Tesseract remains default; the private demo opts in reversibly. Explicit model
paths/download guards are application controls, not an OS network sandbox.
Upstream states Apache-2.0, but its advertised model-license file was unavailable;
packaged/commercial attribution is not claimed complete. No larger GPU model,
paid service, driver/configuration change or publication follows.

Pipeline scores, CPU cold/warm, model startup/resident and actual upload/queue
times are separate. Whole-device VRAM includes other processes. Missing accounting
facts cannot become canonical from model totals/zeros. The CPU route improves
three scans but still abstains on a reserved wrapped table. Business policies,
actual identity/scanner acceptance and a representative lawful adjudicated corpus
remain inputs; no universal accuracy/speed or production pilot is inferred.

The brief executor disconnect did not interrupt existing measurements or the
integration process; jobs were resumed/read, not duplicated. Only fictional
screenshots were saved to Library using its documented direct fallback. No
private invoice was transmitted. Temporary phone port 3001 remains closed.

## CL-06 table correctness — 2026-10-04

h01/h04 became spent development/regression layouts; their frozen prior outcomes
remain unchanged. Eight fresh fictional variants were frozen before tuning and
baseline output sealed until afterwards. These remain synthetic layout evidence,
not independently adjudicated customer data or a 40–60 acceptance corpus. r07's
intentionally absent quantity is checked for abstention but excluded from literal
row scoring; its source contains three candidate rows. VLM repeats/misassociates
them, and none becomes canonical. r02's unprinted tax-basis guess remains ambiguous.

Actual h04 evidence supports a bounded same-model CPU crop retry; no heavier table
stack or new inference dependency is justified/installed. Crop extents are not
field boxes, source values are not arithmetic, and complete printed mapping is
not finance clearance. Single shared-host measurements, resident inference and
worker cold/warm timings remain distinct. No generalized speed/VRAM/accuracy
improvement or real-company policy follows from these fixtures. The current
model, driver and isolated runtime pins are retained; phone access remains closed.

## CL-07 unread cells and source row identity — 2026-10-04

No OCR read is not proof of a genuinely blank versus illegible source. Retain the
known page/row context, raw/canonical null and no field box, then ask the reviewer.
Neither amounts nor a plausible quantity can fill that cell. A uniquely measured
partial row can stop VLM generation while still requiring source/accounting input.
Equal values or equal crop bytes do not prove duplicate items; document/version/
scope/page/actual region establish request identity. Unlocated repeated model
candidates stay ambiguous and accessible, remaining inventory slots stay unread.

Six reserved fictional variants were frozen before tuning and baseline sealed;
57/67 readable row checks pass after correction. q06 stays 0/10, while all five
canonical abstentions pass. No invoice-level/customer accuracy follows. The spent
r07 development improvement does not rewrite its prior excluded-row score. Current
corpora are now inspected; future unseen evidence needs fresh independently
adjudicated layouts. Cold worker 6.469 s and warm 6.883 s are single actual r07
queue observations, not a promise of faster warm processing. No cold GPU-weight
benchmark or per-request VRAM improvement is claimed.

[Acceptance inputs](clearledger_acceptance_inputs.md) distinguish fictional local
policies/identities/scanner paths from business/identity/security acceptance.
Missing real inputs remain missing; lawful independent source evidence is being
requested through the parent task. No restricted dataset, stronger provider, credential or
host change, private export, publication or production pilot was authorized.

## CL-08 independently authored public samples — 2026-10-04

Four public samples have explicit fictional provenance and pinned CC BY 4.0/MIT
reuse notices checked before downloads. English/selected facts were pixel-checked
by this agent before output, not by an independent business adjudicator. Author
truth/generators were not used; model-training overlap is unknown. They establish
an independent layout probe, not customer accuracy, the requested 40–60 real/
anonymized corpus or policy/accounting authority. Arabic fidelity is unscored.
p01 is raster-only despite its frozen "native" label; an erratum preserves truth/
score integrity. Current external sources are now spent regression inputs.

Source confirmation still matters: wrong p01 tax/repeated details can enter an
unconfirmed normalized draft. NEEDS_INPUT prevents current finance submission,
but does not mean every false value is quarantined. Provider null text must not
be mistaken for real source conflict; euro/comma reads are not trusted currency/
amount normalization. Unprinted tax basis, dollar currency and q06 quantity/price
remain unknown. No guessed accounting fact or zero is authorized by these results.

The resident-service observations of 31.523–90.736 s have no cold-weight, paired
before/after, load/VRAM or universal latency implication. Existing judge/browser
human-review gates pass within local fictional scope; actual organization identity,
scanner definitions, commercial attribution/provider and release approval remain
separate. No production pilot or broader acceptance is inferred. See
[CL-08 evidence](clearledger_independent_validation.md).

## CL-09 source repair — 2026-10-04

The four CL-08 sources are spent development inputs; their original truth/results
stay frozen. Two further lawful fictional files were acquired and pixel truth
frozen before tuning and before the latest no-more-acquisition instruction. No
further source/model/runtime acquisition or fine-tuning followed. These two files
share author/template families (u01 with p03/p04), so reserved execution is a check
of new facts and safety, not genuinely held-out layout-family/customer accuracy.
Model-training overlap and business adjudication remain unknown.

A uniform printed euro/rupee/ISO token can supply a source-bound currency candidate;
country/address/store currency and ambiguous dollar/yen/pound cannot. Explicit
source monetary separators can establish decimal-comma notation; strong mixed
conventions or isolated three-digit separators without supporting measured format
evidence remain unresolved. Dates do not inherit locale from currency. The trace
retains raw values, source IDs and v4; historical v2/v3 outcomes remain unchanged.

A model's null is an unread response, not a printed conflicting word. A known
measured source survives it; genuine non-null conflicts remain ambiguous. Dense
metadata/financial cells need independent anchors and actual nonoverlap. An inline
value must not be claimed as a stacked header. Unsupported summary tax/charge
candidates retain raw evidence but cannot become canonical. No zero, quantity,
tax treatment, FX, policy or finance decision is invented.

Source confirmation and required business facts still block submission. Measured
English/selected fields do not establish Arabic fidelity or complete accounting.
The rotated scan and spent multi-blank q06 still need improvement/authorized source
clarification. Resident model timings do not establish cold-weight/VRAM or a
universal warm-speed promise. See [CL-09 evidence](clearledger_source_repair.md).

## CL-10 measured rotation stopping point — 2026-10-04

Three invented CC0 layout families/ten correlated variants were frozen before geometry tuning. Seven reserved variants belong to two NEW synthetic families; baseline remained sealed until first final execution. They are now spent. This supplies bounded orientation/blank-cell evidence, not real-company adjudication, independent ten-layout accuracy or model-training holdout provenance. No new source/model acquisition/training occurred.

Measured orthogonal/small-global-skew transforms change layout and at most one bounded private CPU derivative, never originals. Source field boxes come only from actual detector regions inverse-projected to the unchanged preview/EXIF source. Crop extents are context. Out-of-canvas detector padding is excluded and recorded, never clipped into a fabricated field locator. Disagreeing measured reads remain ambiguous/canonical null even if a known expected value equals the second read. Missing quantity AND price can retain measured description/amount/other rows; no arithmetic fills them. Separate human confirmation/accounting/business controls still block clearance.

The repaired spent public p02 uses actual configured Qwen/TypeLLM for one unresolved header call, with 19.300 s actual upload/durable timing versus CL-09 39.226 s/three calls; selected facts remain complete. Initial real boundary fallback failure is retained. CPU startup/repeat and pipeline/API timings are separate observations with resident GPU weights/shared-host activity; no cold GPU/request VRAM/general latency guarantee. Four reserved supplier reads/two quantity conflicts/one tax conflict and Arabic/perspective/mixed rotations remain unresolved.

CL-10 closes bounded core extraction/readiness and stops before UI redesign. Existing small original rotated previews/technical source tables need separate polish; development role login is not hosted SSO. Original fictional policy version 46/history is preserved. Real adjudicated corpus/business sources, identity/scanner/hosted release inputs are unsupplied; no production readiness/accuracy/compliance is inferred. See [readiness](clearledger_hackathon_readiness.md).

## UI-01 Kivo working name and fresh probes - 2026-10-04

Kivo is an autonomously selected configurable working name under explicit user approval, not a registered/available trademark or purchased domain. The existing ClearLedger/AP engine, rule meanings, tenant roles and source/version/audit remain the product's authority. Landing readiness is an actual computed fictional example labeled as such, not an unconditional result. UI finalization is Prepare review; it does not imply human verification. Source money remains string/Decimal and unknown facts stay unresolved. Only recorded PAID settlement is described as paid.

Actual local fictional hotel version48 is INR9,000 per eligible night from2026-11-01; prior8,000/version47 and historical evaluations remain. Amount changes do not alter scope, unit or currency; these are read from the selected record. This is a demonstration policy, never a universal allowance. Login remains fictional local access and the scanner is unconfigured for this local scope; no real identity/scanner protection was provisioned.

Two NEW original CC0 fictional families/four native/raster sources were frozen before first measurement after UI implementation. The first run is now spent, with truth used only after output, not prompts/corrections/routing. Embedded approval/included-tax instructions are untrusted data; no finance decision or tax basis was invented. Exact raw fields succeeded on this tiny set while ambiguous date/$ and missing qty/price stayed canonical null. No engine tuning/general accuracy/independent customer corpus claim. Timings exclude upload/queue/UI/startup; whole-device memory is shared/resident, not request-attributed VRAM. Earlier rotation and independent acceptance limitations persist. Actual provisional DOCUMENT_CORRECTION_ONLY feedback is not representative adjudicated finance supervision.


## REL reliability/source evidence — 2026-10-05

The continued parent delegation authorizes bounded existing-workspace replay/state/snapshot support and repair of the reproduced difficult scan. Kivo remains the accepted configurable name for the existing ClearLedger/AP engine; no new architecture/model/host/publication authority follows. No concurrent checkout writer was found.

Six original invented CC0 sources in three families freeze literal truth before changes; native/scanned/copy variants are correlated. Initially reserved families are now SPENT. h02 repair is known development evidence, never fresh acceptance/training labels. No prompt truth/sample exception/unsupported tax or missing-value inference. Exact copied pages remain separate rows and receive an explicit source correction instruction; identical hashes are not financial identity or proof of duplicate obligations.

Browser replay persists only scoped SHA256 fingerprints/random keys; actual server scope/authorization/version/body checks remain necessary. Lost/denied tab storage cannot guarantee reload replay. Budget actions retire after acknowledged success, allowing deliberate later identical adjustments; new source rows obtain server UUIDs rather than copied demonstration IDs.

Final fictional hotel policy version 52 is INR 9,000 per eligible night from 2026-11-01. Reversible authorized browser demonstrations appended prior 8,000/new9,000 versions with actor/reason; version 48 and historical evaluations remain. Earlier UI-01 screenshots/version 48 are historical. This is not a corporate standard or a change to real policy.

Resident BF16 model/runtime and finance Python remain unchanged. Actual end-to-end measurements include upload/queues/stages/API/polling, exclude human time and distinguish first-after-CPU-restart from same-worker repeat. Cold GPU weights and request-attributed VRAM are not measured; device-wide14,023/16,380MiB is shared resident usage. Three snapshot samples/loaded outlier and surviving503/lock timeouts cannot establish throughput/availability. Local44 browser/836 backend/final 3 migrated source checks passed; the earlier migrated21pass/1fail and isolated1pass are not one clean aggregate. Real adjudicated corpus/business identity/scanner/pilot inputs and supervised-label gates remain absent. See [verification](kivo_reliability_verification.md).
