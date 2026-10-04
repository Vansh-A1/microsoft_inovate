# ADR-0016 — Owned hackathon lifecycle and isolated computed scenarios

Accepted 2026-10-04 within the user's continuous final-integration approval.

The finance application and real current-driver inference stack already work.
The hackathon needs repeatable start/stop and inspectable scenarios without
changing finance policy, requiring Docker or resetting existing data.

Use `scripts/demo.py` to supervise the existing API/worker/web runner and the
independent pinned inference launcher. Verify process UID, command and start time
before signaling application processes. Readiness checks actual database schema,
HTTP readiness, the owned worker and authenticated model provenance. CPU readiness
and visual-provider availability remain separate. Stop retains the shared local
PostgreSQL cluster, originals and model caches. Explicit inference cleanup is
guarded and is not a consequence of start/stop.

Generate a deterministic, separately scoped synthetic reference catalog and
narrow development identities. Build scenarios through real upload, extraction,
source verification, finance, approval, duplicate disposition and correction APIs.
Private idempotent checkpoints retain computed evaluation IDs. The development
walkthrough reads scoped DB evaluations, rather than trusting a seed's decision
text. Prepared templates bind to that same scope. Enterprise mode disables these
routes and identity selection.

The ruled-table synthetic image deliberately requires visual relationships;
the conservative OCR parser cannot map it completely. This establishes a genuine
VLM demonstration without disabling the native/OCR fast path. Source corrections
and independent approvals remain explicit. No source generator provides expected
answers to the model. These examples prove supported behavior, not general invoice
accuracy or commercial license suitability.
