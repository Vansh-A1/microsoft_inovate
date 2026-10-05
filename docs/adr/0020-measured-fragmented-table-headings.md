# ADR-0020 — measured fragmented table headings

2026-10-05. Accepted within delegated REL-03 bounded extraction repair; preserves ADR-0015 runtime and ADR-0019 source geometry.

The newly spent fictional h02 scan had seven independently read headers and actual OCR row text, but its mild skew split Description from Qty/Unit price/Amount. Detector rectangles reported zero baseline rotation. The strict generic grouping rejected the heading, causing three full-page VLM requests and equal, unassigned row candidates. The measured baseline took49.941s and repeated measurement53.097s; all six checked row values remained unconfirmed. This is a development failure, not fresh validation.

Keep generic label/value and item grouping unchanged. Only two adjacent groups made entirely of recognized column labels may associate as one heading. Require one complete description/quantity/unit-price/amount schema, unique labels, nonoverlapping ordered columns, at least40% common overlap of the smallest actual heading height, and a linear centre baseline with residual at most25% of that height. Competing labels, unrelated text, separate rows, crossing columns and nonlinear geometry abstain. No source box or image is expanded/transformed by this helper.

Apply the same heading association to table parsing, independent printed-column detection and bounded numeric-cell retries. New runs identify printed-layout-v7/native adapter9. Reuse existing measured partial-row routing: unread quantity/price slots remain MISSING/raw null/canonical null, actual source regions stay unchanged, and human confirmation remains required. No arithmetic supplies a value, tax basis, currency/date locale, confidence or finance decision.

No schema/migration, model/runtime/package/host changes, prompt truth, sample exceptions or page/row deduplication. Historical outputs retain their versions. The spent difficult scan may verify repair of this known failure; it cannot establish independent accuracy. Actual runtime measurements and remaining limitations belong in the reliability report.
