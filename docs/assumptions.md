# Assumptions and external inputs

This register separates proposed development defaults, currently missing inputs, and observed environment facts. None establishes a live company's finance policy or a production capability. Basis: [specification](AP_Exception_Assistant_Codex_Spec.md), repository reconnaissance, and the user's bounded P0-01–P0-04A approvals on 2026-10-02.

## Business defaults and missing inputs

| Item | Current basis/status | Required before live use |
|---|---|---|
| Data | P0-03 adds 38 fictional root references and ten independently adjudicated golden alternatives. Source documents are JSON facts only, with no real documents or extraction claims. | Authorized representative documents/data and permitted uses. |
| Company/entity scope | All fixture finance activity uses one fictional entity/cost center. A second entity and second tenant's entity are sentinel scopes for malformed-link tests. This does not implement access control. | Actual entities, visibility, and policy owners. |
| Currency/tax | P0-03 is explicitly INR-only; its 18% tax, hotel/meals/taxi limits and half-open approval bands are labeled demo arithmetic/configuration. No FX was needed or invented. | Approved currencies, jurisdiction/tax/rounding/FX policies. |
| Finance policy | No real company policy or approved authority matrix is supplied. | Signed-off control, approval, waiver, and separation-of-duties rules. |
| Payment execution | Outside the initial scope; none exists. | Separate explicit design and authorization for any future integration. |

## Technical defaults and unverified work

| Item | Current basis/status |
|---|---|
| Architecture | The specification proposes Next.js/TypeScript, FastAPI/Pydantic, PostgreSQL, shared Python finance logic, local storage/jobs initially, and Azure later. These components have not been scaffolded. |
| Extraction | P0-04A implements provider-independent contracts and deterministic fixture response replay. It observes no actual document pixels and does not normalize or decide financial eligibility. |
| Extraction spike data | Ten structured synthetic cases declare raw/candidate/state/row ground truth separately from replay responses. Poor text, rotation, obstruction and repeated headers are annotations/metadata, not generated or processed visual artifacts. Page references are synthetic declarations; all bbox/artifact slots are null. |
| Spike metrics | Fixture agreement is expected by construction, not an independently measured extractor's accuracy. Absent candidates, abstention denominators, locators and adapter timings produce null metrics where unavailable. Locators measure availability only, not factual correctness. |
| TypeLLM/VLM | Compatibility, null handling, line strategy, evidence granularity, latency, license, and hardware needs are not verified. No provider was selected. |
| Deterministic controls | P0-02 implements immutable standard-library state, exact-decimal Money/currency, and evidence contracts. Finance rules, screening, and finalization remain unimplemented. |
| Fixture conventions | P0-03 uses fixed UUIDs, version 1, half-open reference dates, fixed UTC evaluation time, exact decimal strings including night quantities, and independent case snapshots. Test-only validation and operand assertions are not production transaction schemas or evaluators. |
| ML | No adjudicated training dataset or trained model is supplied or created. Synthetic tests will not establish real-world generalization. |
| Operational readiness | No latency, extraction-quality, availability, backup, or restore target has been measured. Targets in the specification are proposals. |

## Environment observations

Observed in the checked shell/Python environment on 2026-10-02. These are not project lockfile selections or compatibility approvals; an executable missing from PATH may exist elsewhere.

| Tool/package | Observation |
|---|---|
| Python | 3.13.11 (`/opt/conda/bin/python3`). |
| Git | 2.43.0; an existing author/committer identity is configured. |
| GitHub publication | Anonymous remote read succeeds, but the initial HTTPS push returned exit 128: `fatal: could not read Username for 'https://github.com': terminal prompts disabled`. Authentication is unavailable to this noninteractive Git operation; no credentials/configuration were changed. |
| pytest | Installed, version 9.1.1 in the checked Python environment; P0-01 found no tests, and P0-02 introduces domain unit tests configured by root `pytest.ini`. |
| FastAPI / Pydantic | Installed environment distributions: 0.137.1 / 2.12.4. No project dependency manifest or compatibility test exists; neither is used by the P0-02 domain modules. |
| Node / npm | Not available on the checked PATH. |
| SQLAlchemy / Alembic | Not installed in the checked Python environment. |
| Docker | CLI 29.1.3 available; daemon availability was not tested. |
| Docker Compose | `docker compose version` returned exit 1, unknown command. |
| PostgreSQL tools | `psql` not available on the checked PATH; no project database exists. |
| uv / GitHub CLI | Not available on the checked PATH. |

No dependencies were installed or selected in P0-01–P0-04A. Production domain/extraction modules and fixture support use the standard library and existing contracts; pytest uses the preexisting environment. Source syntax targets Python 3.10, but execution is verified only on Python 3.13.11. No package metadata or broader compatibility claim is introduced. Subsequent runtime setup must be a separately approved task. The [compatibility checklist](extraction_compatibility.md) is document-only; P0-04B has not started and all provider/runtime topics are NOT CHECKED.

## External dependencies

- Azure subscription, deployment destination, region, access, and budget have not been supplied. No resources were provisioned.
- Authorized ERP/vendor/employee/PO/GRN/master sources and freshness requirements are not available.
- Production identity/role mapping, retention, legal-hold, provider data terms, and real-data permissions remain external inputs.
- The user selected [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate) and authorized initial baseline publication to `main`; remote publication status belongs in [progress](progress.md).

Record future decisions or changed observations with evidence. Do not replace an unresolved input with a permissive value or represent a planned adapter as implemented.
