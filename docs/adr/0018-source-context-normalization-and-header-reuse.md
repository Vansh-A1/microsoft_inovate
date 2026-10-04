# ADR-0018 — source context, money normalization and header reuse

Status: accepted in the delegated CL-09 local repair, 2026-10-04.

Four externally authored public fictional sources exposed correct raw European
money being rejected, known multi-page totals contaminated by provider nulls and
dense measured cells rejected because their headings were centered differently.
Original sources, pixel truth and baseline outcomes remain immutable. These four
sources are development cases after inspection; they cannot prove fresh holdout
accuracy. No training, model/runtime change or new financial policy is authorized.

## Decisions

New drafts use document-normalizer-v4. Recognize explicit supported ISO currency
codes and the unique euro/rupee symbols; dollar, yen and pound symbols alone remain
ambiguous. Uniform explicit monetary tokens can establish a source-bound currency
observation when no separate Currency label exists; conflicting tokens cannot.
Keep the real monetary span locator and a derivation diagnostic, never invent a
Currency field box or infer a unit from an address or FX arithmetic.

Infer decimal-comma monetary notation only from PRESENT measured source cells with
unambiguous separators. Record the contributing observation IDs, format, raw
literal and rule version. Validate grouping and use Decimal strings. Strong mixed
point/comma conventions leave money unresolved. Isolated three-digit separators
remain ambiguous without format evidence; the explicit low-level point parser
and existing dimensionless syntax stay compatible. Currency does not establish
number/date locale. No inference fills missing tax treatment, zeros or quantities.
Older v2/v3 drafts, evaluations and reports retain their recorded versions.

Read bounded stacked labels with or without colons when independent aligned value
regions establish ownership. Only measured native font extents may have up to one
quarter of a span-height overlap; OCR/material overlap and nearby competing text
still abstain. A distant unrelated left column need not discard a qualified number
label. Text to the right can be an inline value: that row must not be claimed as
stacked or replaced by the following row. Bare invoice/PO titles cannot supply identities.

For complete printed tables with SKU/barcode metadata, permit centered/wide textual
headings when the actual cell regions are ordered and nonoverlapping and every
financial/unit cell satisfies its own heading anchor. Exact ordered cell counts
or complete separated cell groups are required. This refines the old blanket
midpoint-crossing rejection: actual neighboring/financial overlap, missing shifted
cells and ambiguous geometry still abstain. Only measured detector regions become
field boxes. Metadata and equal values are not universal record identities or
proof of duplication; valid separately printed equal rows are retained.

Reuse independent source headers across all pages and previously read document
headers. When at least three independently measured headers are available, request
only unresolved core fields and first-page supplementary address fields. A printed
conflict or ambiguous source currency is a human question, not another model vote.
Incomplete unmeasured visual pages keep the existing broader contract. Actual
request fields, calls and times are recorded in extraction-routing-v6; extraction-v1
is unchanged. This routing choice never produces a finance decision.

Provider null with PRESENT/AMBIGUOUS status becomes ILLEGIBLE with raw null and a
PROVIDER_VALUE_UNREAD diagnostic, not fabricated literal "null". It cannot contradict
an independently measured value. Genuine non-null conflicts/source illegibility
remain ambiguous, and unread provider output without an independent fact remains
unresolved. Model-only summary tax/discount/shipping/other-charge candidates without
an independently read summary label stay ambiguous, retaining raw evidence for
source correction. An item amount or guessed zero cannot establish header scope.

## Consequences

Human source confirmation, immutable corrections, mandatory finance controls,
versioned business activation and all budgets/approvals remain required. Successful
literal reads do not supply absent accounting/business facts or clear an invoice.
The existing driver/BF16 model, isolated runtimes and loopback serving remain intact.
Measured development improvements need reserved validation and disclose Arabic,
rotation, multi-blank rows, unsupported currency/locale and real-business gaps.
No fine-tuning, paid service, stronger model, hosted inference or publication follows.
