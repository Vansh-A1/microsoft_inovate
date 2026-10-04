# Governed enterprise pilot deployment

Status: **DEFERRED_EXTERNAL — no Azure resource, registry image or hosted pilot has been created.** Local Bicep compilation, signed-token contracts and mocked Blob tests are deployment preparation, not a pilot smoke test.

## Inputs and promotion gates

An authorized operator must supply subscription, region, resource permissions, monthly spend ceiling, identities/application registrations, tenant/entity memberships, residency decision, approved address ranges/private access/egress and GPU disposition. This CPU release never authorizes inference provisioning. Also required: an approved private runner, real authorization smoke, cloud database/object restore, monitoring and application-image rollback evidence. There is no automatic cloud deployment from a pull request.

Foundation provisioning/staging requires its own authorized change and reviewed secure parameters. Protected pilot promotion is a later gate: `deployment_gate.py` rejects absent/incomplete approvals. It requires boolean verification flags and binds the approved full commit and the reviewed release-parameter SHA-256, and the dispatcher checks the active subscription/resource group/region. Do not mark checks true because templates compile. Do not put approval files, subscriptions, passwords or full deployment outputs in Git.

## Artifact order

1. Review/compile `infra/azure/foundation.bicep` and `release.bicep`. Region, CIDRs, PostgreSQL SKU/HA/storage, database backup days, Blob recovery days and log retention are mandatory operator inputs. No spend/retention policy is inferred.
2. On approved infrastructure, create the private foundation, DNS/private connectivity, registry and secrets. Apply enterprise egress/firewall policy, private DNS resolution, TLS and endpoint restrictions. Templates establish private resources/internal ingress; they do not supply an organization-specific outbound firewall policy or prove network reachability. Validate no accidental public database/Blob or unrestricted inference endpoint.
3. Configure separate Entra application registrations for web sign-in and API access scope. The API accepts only approved issuer/audience/tenant/client and enabled server memberships. Container Apps EasyAuth obtains the API access token; the same-origin BFF forwards it. Verify the configured scope returns an access token for the API rather than an ID token or web audience. Require actual hosted verification before pilot use.
4. Use the release validation workflow to test/build CPU API/worker and web images. It resolves base tags to recorded digests, uses locked language dependencies, saves image artifacts/checksums and pins action commits. Local Docker build is blocked; no image digest exists yet. Inspect OS packages/SBOM and vulnerability results on that approved build host. Push approved image artifacts into the private registry and record registry digests bound to the tested commit.
5. Supply only managed-identity Key Vault secret references and server-owned configuration. Web identity accesses its named authentication secret; API/worker access only their named configuration/database secrets and the document container. No account keys or developer credential fallback. Review worker scope membership separately. Use the non-superuser/non-bypass application role. PostgreSQL connections require `sslmode=verify-full`; provider/document service endpoints must use approved private HTTPS. Do not log configuration or token values.
6. Run reviewed Alembic migrations with separate controlled migration credentials before promotion; application startup/workers never migrate. Review expand/contract compatibility first. A failed migration stops deployment and preserves the prior application/schema; never reset/downgrade retained business data as a release shortcut.
7. Protected `enterprise-pilot` workflow uses Azure OIDC on `ap-private-pilot`, reviewed commit/parameters and immutable registry digests. It runs explicit migration unless image rollback, then what-if and release deployment. Set private runner `AP_CONFIG_FILE`/`AP_DATABASE_URL` for migration, approved Azure CLI/Bicep/venv and network access beforehand. Private outputs remain in `runtime/release` with restricted permissions. Current-host alternate publication/provisioning is not authorized.
8. Run post-deployment authorization, private storage, RLS, queue/worker, real document/manual verification, report/audit, outage, restore and rollback smoke. Validate unauthenticated/public responses are minimal; cross-tenant/entity/evidence, ordinary finance health/config access, self-approval, revoked policy privilege and forged actors are denied. Record results before institutional data or auto-eligibility use.

## Enterprise configuration contract

Set `AP_ENVIRONMENT=enterprise`; supply approved `AP_CONFIG_FILE` or Key Vault-backed `AP_CONFIG_JSON` and the database secret. Configuration needs:

- `enterprise_identity`: tenant ID, API audience, allowed client IDs and enabled server-owned object-ID memberships with application scope/actor/roles.
- `worker_scopes`: explicit server-owned tenant/entity/actor entries restricted to the worker permissions required by the existing stage services.
- `storage_mode=AZURE_BLOB`, HTTPS public-Azure account endpoint, private container and managed-identity client ID. Sovereign-cloud/custom Blob endpoints require another reviewed adapter; they are currently rejected.
- Typed document limits and CPU `ocr_executable=/usr/bin/tesseract` for the API image. OCR is CONFIGURED until actually tested; real image package/version execution is deferred.
- Optional private TypeLLM endpoint/model only when separately provisioned/approved; otherwise facts requiring visual inference remain incomplete. A configured endpoint is CONFIGURED_UNVERIFIED, not healthy. No fixture answer fills a live outage.
- `malware_required` according to approved intake safety policy. Current adapter is NOT_CONFIGURED; required scanning quarantines rather than pretends CLEAN. Real-data pilot acceptance must address the scanner gap explicitly.

Web needs enterprise mode, HTTPS `AP_API_ORIGIN`, exact HTTPS `AP_WEB_ORIGIN` and the verified EasyAuth API-token integration. Development/demo identities remain disabled even if a demo flag is accidentally set. No client-provided scope or role is accepted.

`release.bicep` defaults `useApprovedInferenceGateway=false`. Enable it only for
a separately approved, reachable private HTTPS gateway and licensed model.
API/worker then receive `AP_TYPELLM_GATEWAY_TOKEN` via the named Key Vault secret
`ap-typellm-gateway-token` and their managed identity; the frontend receives no
gateway credential. Populate that secret through the approved secret-management
process and explicitly verify access/health. This parameter does not create GPU
compute or confer commercial permission for the local Qwen research checkpoint.
The native hackathon runtime remains documented independently in
[local inference](local-inference.md) and the [demo runbook](hackathon-demo.md).

## Rollback and release integrity

Revert to a previously approved compatible application image digest through a reviewed release parameter file and protected workflow with rollback enabled; migrations are skipped. Keep historical evaluations/ledger/audit/evidence. A previous image must understand the current expanded schema; review compatibility rather than assume it. Never destructively roll back financial tables. After image rollback repeat permissions, processing, rules/report, audit and capacity smoke.

Model rollback is separate: a governor appends a deployment selecting a compatible historical approved statistical model, or explicitly selects RULES_ONLY. Changed code can make an old artifact incompatible. Rebuild/shadow/approve a compatible artifact through governance; never rewrite old scores. Policy/reference rollback is another explicit new version with authorized reason/effective dates.

Cloud database point-in-time restore and Blob version recovery are mandatory [recovery gates](recovery.md). No hosted rollout/rollback/restore test is claimed in this local delivery.
