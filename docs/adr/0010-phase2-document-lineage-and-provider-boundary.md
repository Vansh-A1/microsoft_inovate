# ADR-0010: document lineage and a bounded provider control plane

Status: accepted under the 2026-10-03 direct Phase-2 approval.

The Phase-1 finance queue requires transaction and snapshot foreign keys. Before
extraction those facts do not exist. Add scoped document jobs/outbox alongside
that queue rather than weakening its constraints. A stage lease pins document
revision, generation and pipeline version; guarded finalization appends facts,
advances the next stage and writes audit atomically. Failed attempts preserve
the last completed stage. Original keys are server generated; SHA-256 is computed
while streaming. Upload and finalize are separate, idempotent effects.

Immutable original metadata, pages, extraction runs/observations and normalized
drafts have scope-qualified FKs, forced PostgreSQL RLS and mutation rejection.
PDF text coordinates are transformed with PyMuPDF's actual rotation matrix.
Image OCR boxes use the inverse EXIF transform; unknown boxes remain null.
Resource-bounded child processes parse actual bytes. Unconfigured malware
scanning is explicitly NOT_CONFIGURED; requiring scanning blocks that state.
Preview PNGs are derived objects and originals are never rewritten.

Native text uses a conservative labeled-header/explicit-table parser. Unknown
layouts retain uncertainty. Optional project-local Tesseract is replaceable and
measured against real synthetic images. TypeLLM uses its pinned 0.5.1 generate
contract with flat state/string questions and application-managed rows against a
separate SGLang service. The client requires approved preprovisioned tokenizer
assets; it never downloads them. Runtime integration is externally deferred.
Mocked responses test the boundary, and the actual pinned wheel's schema compiler
accepted 42 flat header questions. Neither is a real-model extraction benchmark.
No hidden reasoning is stored. Routing sidecars are versioned separately from
the unchanged strict extraction-v1 result.

Document-derived screening requires explicit human source verification during
Phase 2. This is factual verification, not approval authority. Verified facts
are immutable scoped reference records bound to physical document revisions
and canonical versions. Finance controls, approvals and capacity effects remain
authoritative. This permits a useful CPU vertical slice without claiming
production extraction quality or clearing ambiguity using a fabricated score.

Consequences: additional queue/tables and bounded layout support; parser and OCR
failures require visible user input or a provider. Quarantine has no screening
decision. More advanced models, table layouts, segmentation and auto-pass quality
require later measured work, not a fixture fallback. No Phase-3 matching logic is
introduced.

The Phase-1 pure engine and its versions remain unchanged. A separately versioned
pure document-source extension changes DOC-001 reconciliation only on physical
source contexts, maps actual evidence and cannot override other mandatory checks.
Mapped cell evidence adds provenance without changing screening. Automatic approval
review rejected an earlier proposal to change global ruleset/per-rule versions
because it risked altering established Phase-1 behavior. The accepted narrower
integration preserves that behavior and confines new semantics to document sources.
