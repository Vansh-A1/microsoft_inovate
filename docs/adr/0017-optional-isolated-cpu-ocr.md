# ADR-0017 — Optional isolated CPU OCR and source-grounded accounting

Status: accepted for the authorized local ClearLedger experiment, 2026-10-04.

## Context

The frozen twelve-source challenge exposed label association, wrapped-row and
scan recognition failures in the existing native/Tesseract path. The current
Qwen/TypeLLM model sometimes repeated rows or supplied unprinted accounting
semantics. A larger model, finance dependency changes and GPU/host changes are
outside this task. Historical observations and the finance engine must survive.

## Decisions

Keep Tesseract as the repository default. Add explicit server configuration
`RAPIDOCR_CPU_EXPERIMENTAL` with an absolute isolated interpreter. Use RapidOCR
3.9.2 and CPU ONNX Runtime 1.23.2 with bundled, SHA-256-verified detector,
recognizer and classifier models. Verify actual CPU execution providers at
startup. Record package/model/provider provenance per page; configuration alone
does not establish health or extraction quality. Finance Python and ADR-0015
inference environments are unchanged.

The finance process launches the optional resident child through private stdio,
with stripped environment, scoped derived-image paths, bounded responses and
deadlines including partial responses. No shell or network listener is used.
Explicit bundled model paths and blocked supported HTTP download functions avoid
runtime downloads. These are application controls, not an OS network sandbox.
An actually configured Tesseract engine may fall back within the remaining time
budget. Neither failure nor provider null becomes an empty successful extraction.
The owned child can restart after exit without touching system services.

General measured geometry may associate a label-only row with a nearby aligned
value row, and join a bounded description continuation before a complete next
row. Competing columns, identities or incomplete tables abstain. Neither fixture
identities nor expected values enter routing, prompts or parsers. Reserve six
synthetic layouts until tuning ends; preserve observed holdout failures.

Purpose limits TypeLLM questions, and independently observed table headings
limit requested columns when complete. Preserve strict extraction-v1; request
telemetry belongs in the versioned sidecar. Model-only line discount/net/tax/gross
facts need independently observed corresponding row columns before normalization.
Otherwise retain raw observations as AMBIGUOUS with no canonical accounting value.
Totals or arithmetic cannot prove tax treatment. Source confirmation, approvals
and all existing mandatory finance controls remain required.

## Consequences

Three challenge scans avoid VLM and improve core fact recovery. One reserved
wrapped-table scan still produces no usable rows, and a landscape layout retains
an incomplete model row. CPU OCR is experimental, not universal invoice accuracy
or a production provider approval. The local demo opts in reversibly; deployable
defaults remain Tesseract. Larger lawful adjudicated corpora, commercial model
attribution, approved stronger provider, identity and malware-scanner acceptance
remain separate inputs. The project's advertised model-license document was
unavailable during verification, so packaged/commercial release attribution is
not claimed complete. See the measured [validation report](../clearledger_validation.md).

Visual QA exposed source-derived forms inheriting unprinted row accounting values
from a development template. The API already blocked unresolved source commits,
but the form was misleading. Blank unsupported financial fields and eligible
night defaults, preserving explicit business-reference choices. Native v4 retains
unread row fields as MISSING observations with no raw value/box for the existing
audited correction controls. Finance rules and historical records stay unchanged.

## CL-06 implementation refinement — 2026-10-04

Actual spent h04 detections miss a printed quantity glyph, while the same pinned
CPU model reads it from a bounded measured row crop. Use at most three local
in-memory row-context retries with exact inverse detector coordinates, four-million
scaled-pixel cap and the original page budget. Crops are routing extents, never
field boxes or confidence. Complete independent tables survive header-only VLM
fallback; incomplete/uncertain pages remain subject to review. No RapidTable,
PPStructure, new model or dependency is justified by this specific failure.
See [CL-06 evidence and remaining failures](../clearledger_table_correctness.md).
