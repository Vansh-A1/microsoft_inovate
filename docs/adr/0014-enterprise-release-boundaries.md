# ADR-0014 — Enterprise release boundaries

Status: accepted for Phase-6 local implementation; actual pilot deployment gated.

Use Azure Bicep as the single infrastructure definition. CPU web/API/control workers share private PostgreSQL/object storage and durable jobs. The enterprise inference plane remains a separate approved service; no GPU dependency in CPU images. Internal networking, managed identities, Key Vault and private Blob are deployment requirements. Azure account, spend, region, network, identity and residency approvals are absent; definitions and contract checks do not prove deployment.

The existing reference staging/validation/activation service remains authoritative. The Admin Console adds allowlisted typed business changes with optimistic version checks and a POLICY_ADMIN capability restricted to policy kinds. It cannot edit canonical decisions or arbitrary code. Finance screens lead with a plain-language result and source; detailed checks retain original evidence. Existing blue/navy palette and keyboard/focus conventions remain.

Enterprise access tokens must be issuer/audience/signature/tenant validated, then resolve to server-owned scoped memberships. UI navigation follows actual permissions. Browser traffic uses same-origin requests; development identity selection is disabled in enterprise mode. Missing identity/storage configuration fails closed. Hosted identity, private-network, managed-identity and cloud recovery verification remain pilot gates, even when mocked contracts pass locally.

Delivery uses reviewed explicit migrations, immutable image digests and separate manually governed deployment. Rollback restores application images first; historical finance/audit data is never erased to recover a release. Local restore drills use owned disposable databases/storage, never reset the working demo.

Operational health is narrower than finance case access: dependency internals require an operational or auditor role, even when a finance reviewer can inspect business failures. Cached idempotency results never bypass current administration authorization. Managed-identity cloud storage is CONFIGURED_UNVERIFIED until cloud checks are run; local cache readiness does not prove the cloud service is available.

Primary implementation references: [Container Apps resource schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.app/containerapps), [authentication](https://learn.microsoft.com/en-us/azure/container-apps/authentication), [internal networking](https://learn.microsoft.com/en-us/azure/container-apps/vnet-custom), [Blob Python identity integration](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-python-get-started), [Entra token validation](https://learn.microsoft.com/en-us/entra/identity-platform/claims-validation). These guide contracts and deployment definitions; they are not evidence of a completed hosted deployment.
