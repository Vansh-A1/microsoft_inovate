# Assumptions and external inputs

This register separates proposed development defaults, currently missing inputs, and observed environment facts. None establishes a live company's finance policy or a production capability. Basis: [specification](AP_Exception_Assistant_Codex_Spec.md), repository reconnaissance, and the user's P0-01 approval on 2026-10-02.

## Business defaults and missing inputs

| Item | Current basis/status | Required before live use |
|---|---|---|
| Data | Synthetic-only development is the approved default. No synthetic application fixtures or real confidential documents have been added in P0-01. | Authorized representative documents/data and permitted uses. |
| Company/entity scope | Proposed synthetic single entity, with tenant/entity isolation required once implemented. No organization-specific scope was supplied. | Actual entities, visibility, and policy owners. |
| Currency/tax | INR is the proposed demo primary currency; tax, FX, limits, and approval bands in the spec are development examples. | Approved currencies, jurisdiction/tax/rounding/FX policies. |
| Finance policy | No real company policy or approved authority matrix is supplied. | Signed-off control, approval, waiver, and separation-of-duties rules. |
| Payment execution | Outside the initial scope; none exists. | Separate explicit design and authorization for any future integration. |

## Technical defaults and unverified work

| Item | Current basis/status |
|---|---|
| Architecture | The specification proposes Next.js/TypeScript, FastAPI/Pydantic, PostgreSQL, shared Python finance logic, local storage/jobs initially, and Azure later. These components have not been scaffolded. |
| Extraction | Fixture extraction is the safe planned default until a provider/runtime is verified. No extraction adapter exists yet. |
| TypeLLM/VLM | Compatibility, null handling, line strategy, evidence granularity, latency, license, and hardware needs are not verified. No provider was selected. |
| Deterministic controls | Rules-first screening and exact Decimal calculations are required; domain contracts and rules remain unimplemented. |
| ML | No adjudicated training dataset or trained model is supplied or created. Synthetic tests will not establish real-world generalization. |
| Operational readiness | No latency, extraction-quality, availability, backup, or restore target has been measured. Targets in the specification are proposals. |

## Environment observations

Observed in the checked shell/Python environment on 2026-10-02. These are not project lockfile selections or compatibility approvals; an executable missing from PATH may exist elsewhere.

| Tool/package | Observation |
|---|---|
| Python | 3.13.11 (`/opt/conda/bin/python3`). |
| Git | 2.43.0; an existing author/committer identity is configured. |
| GitHub publication | Anonymous remote read succeeds, but the initial HTTPS push returned exit 128: `fatal: could not read Username for 'https://github.com': terminal prompts disabled`. Authentication is unavailable to this noninteractive Git operation; no credentials/configuration were changed. |
| pytest | Installed, version 9.1.1 in the checked Python environment; workspace collection found no tests. |
| FastAPI / Pydantic | Installed environment distributions: 0.137.1 / 2.12.4. No project dependency manifest or compatibility test exists. |
| Node / npm | Not available on the checked PATH. |
| SQLAlchemy / Alembic | Not installed in the checked Python environment. |
| Docker | CLI 29.1.3 available; daemon availability was not tested. |
| Docker Compose | `docker compose version` returned exit 1, unknown command. |
| PostgreSQL tools | `psql` not available on the checked PATH; no project database exists. |
| uv / GitHub CLI | Not available on the checked PATH. |

No dependencies are installed or selected in P0-01. Subsequent runtime setup must be a separately approved task.

## External dependencies

- Azure subscription, deployment destination, region, access, and budget have not been supplied. No resources were provisioned.
- Authorized ERP/vendor/employee/PO/GRN/master sources and freshness requirements are not available.
- Production identity/role mapping, retention, legal-hold, provider data terms, and real-data permissions remain external inputs.
- The user selected [Vansh-A1/microsoft_inovate](https://github.com/Vansh-A1/microsoft_inovate) and authorized initial baseline publication to `main`; remote publication status belongs in [progress](progress.md).

Record future decisions or changed observations with evidence. Do not replace an unresolved input with a permissive value or represent a planned adapter as implemented.
