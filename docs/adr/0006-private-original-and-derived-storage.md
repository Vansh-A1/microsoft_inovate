# ADR-0006 — Private originals and versioned derived storage

- Date: 2026-10-03.
- Status: Accepted Phase-0 design; storage service not implemented.
- Basis: specification sections 3.3, 4, 13, 18, 19 and P0-06.

## Decision

Use a local filesystem storage adapter in development; target private Azure Blob/object storage for an authorized enterprise pilot. Internal keys are server-controlled and scoped; clients and document text cannot supply arbitrary filesystem paths or fetch URLs. Preserve original bytes, SHA-256, immutable object/document version and intake/availability state. Enforce safe path resolution, authorized reads, file/page/pixel/CPU/time limits and quarantine in future implementation.

Previews, native text, rendered pages and detected crops are separate derived artifacts. Record original parent/version, preprocessing version, dimensions/orientation, rendering settings and actual transforms. A crop region is not a detected field bbox. Map coordinates back to the original only when verified; otherwise locator/bbox remains absent. No coordinates or crops are created in Phase 0.

Private document access goes through server authorization with current tenant/entity/resource checks. No public document URLs. If later scoped short-lived object access is selected, authorize it first and retain an auditable access/expiry policy; a UUID or object key alone is not permission. GPU workers fetch only assigned versions over approved private paths.

Blob/file writes are staged, checksum-confirmed and finalized before marking AVAILABLE; reconcile orphan objects and missing metadata. Retention, legal hold and erasure are organization-approved inputs. Original/derived/model/report caches remain outside Git; preserve fixtures explicitly. No host/model/shared-cache deletion or cloud provisioning follows this decision.

## Consequences and alternatives

Reject destructive preprocessing and public/unvalidated URL storage. Local originals and private enterprise objects share an adapter boundary; no adapter or retention engine exists yet. Phase 1/2 must test path traversal, scope, interrupted writes, read authorization, original preservation, transform correctness and reconciled availability. [Deployment profiles](../inference_architecture.md#deployment-profiles) keep GPU storage away from finance laptops.
