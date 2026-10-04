# ClearLedger CL-06 reserved fictional layouts

Eight original fictional sources dedicated to the public domain under CC0 1.0.
No customer data, downloaded invoices or real business policy is included.
`manifest.json` was frozen on db1095f before CL-06 extraction changes. Source
hashes are checked on every run; truth enters only post-extraction scoring.

The previous h01/h04 failures are spent development/regression layouts. These
new variants vary values, typography, geometry, three-page reordered tables,
wrapped scans, ambiguous dates/currencies, an unfamiliar header, a genuinely
unprinted quantity and conflicting document identities. They share fictional
vocabulary and are not a representative customer distribution or a 40–60 source
acceptance corpus. The r07 intentionally incomplete table is excluded from row
literal scoring; its required canonical quantity abstention is checked separately.
`expected_rows: 0` in raw run output means zero scored rows for r07, not a claim
that its source has no table. The source visibly has three candidate rows.

Freeze: `.venv/bin/python scripts/benchmark/clearledger_reserved.py --freeze`.
Existing sources/results must not be amended to improve a score. Baseline output
was sealed during tuning; after execution opened it for comparison. New runs
require fresh labels and do not recreate the old-code baseline. Inspectable
synthetic metrics are in `results-2026-10-04.json`; raw outputs remain ignored.
