# ADR-0003 — Trusted identity and internal record keys

- Date: 2026-10-03.
- Status: Accepted Phase-0 design; authentication/persistence enforcement is future implementation.
- Basis: specification sections 2.2, 5, 18 and P0-06; approved Phase-0 closure.

## Decision

Tenant, legal entity, actor and allowed roles come from validated server authentication and authorized entity membership. Enterprise identity targets Entra ID/OIDC; development uses an explicitly isolated synthetic identity adapter. Never trust a tenant, role, approver or claimant merely because an upload/form/document provides it. Workers receive scoped jobs and independently verify access to referenced versions; pooled database tenant context must be cleared between uses.

Use UUIDs for internal document, transaction, entity, master, job and evaluation identities. Display invoice/employee numbers, source hashes and fuzzy names are attributes/candidates. Identical bytes in separate independent submissions must not silently merge obligations; an idempotent retry is bound to the scoped request key and request digest. Document content cannot create approved vendor/employee identities or modify bank/master records. Claimant and submitter are resolved separately from authenticated claim context; curated reference resolution supplies trusted master IDs.

Versioned records and immutable source/evaluation links preserve lineage. A UUID is not an access grant. Future API checks and composite scoped database relationships/RLS must enforce boundaries in addition to the existing in-memory structural validators.

## Consequences and alternatives

Reject client-controlled identity and hash-as-primary-key designs. Development fixtures carry declared UUID scopes but do not prove authentication or authorization. No identity adapter, OIDC configuration, database constraint or endpoint is implemented in Phase 0. Phase 1 must test forged claims, cross-tenant/entity access and reused-connection scope; later approval flows test self-approval/delegation. See [phase exit review](../phase0_exit_review.md) for current evidence and limits.
