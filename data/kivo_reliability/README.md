# Original fictional reliability sources

Six invented invoice PDFs in three layout families, created with existing ReportLab/PyMuPDF/Pillow tools. Their original contents are dedicated to the public domain under CC0 1.0. They contain no customer, employee, bank or third-party invoice data. Embedded instructions are intentionally untrusted document text.

`manifest.json` froze source hashes and literal truth at checkout `4883e1b` before these measurements and repairs. `delivery_matrix` is development; `offset_panels` and `folio_continuation` were initially reserved. Native/scanned/copy variants are correlated within each family. The reserved split is now **spent**; the h02 repair uses known development evidence. Neither six independent layouts nor real-world accuracy is claimed.

`results.json` contains sanitized measured scores, timings, source/code/measurement hashes, routing and mandatory abstentions. It contains no private document IDs, credentials or full source outputs. Truth/results are scorer evidence only; never model prompts, routing exceptions, business defaults, canonical corrections or supervised labels. Exact copied pages remain separate source rows and are explicitly flagged for human review.

The existing harness `scripts/benchmark/kivo_reliability.py --freeze` preserves an existing freeze; `--label <unused-label> --split <development|reserved> [--case h02]` performs actual local upload/durable processing without a finance commit. It refuses to overwrite a measurement, validates source hashes and records extraction code hashes. Runtime measurements and source outputs stay ignored. Exit 0 means measurement completed, not that extraction was correct.

See [verification](../../docs/kivo_reliability_verification.md) for failures, measured changes, exact checks and remaining limits.
