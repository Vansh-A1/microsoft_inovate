# CL-07 fictional row identity fixtures

Six original invented invoices, dedicated to the public domain under CC0 1.0.
No customer data, downloaded invoices or company policy is included. The manifest
and source SHA-256 hashes were frozen on 7cc473e before this milestone's tuning.
Baseline output stayed sealed until the implementation and focused checks ended.
Truth enters only scoring after extraction; inference has no fixture-ID exceptions.

Variants cover a blank quantity in scanned/native tables, legitimate identical
items at distinct positions, three equal items on separate pages, a blank price,
and two unread cells where row ownership cannot be established. All 67 readable
row literals are scored, including the ten unresolved q06 values. The latter is
0/10; required missing-quantity/price abstentions pass, without pretending that
successful abstention establishes correct row extraction.

These are reserved synthetic variants with shared fictional vocabulary, not an
independently sourced customer distribution or the requested 40–60 invoice
acceptance corpus. They become spent regression cases after inspection; do not
relabel later measurements unseen or modify sources/expectations for a better score.

Freeze: `.venv/bin/python scripts/benchmark/clearledger_rows.py --freeze`.
Run with a fresh label: `.venv/bin/python scripts/benchmark/clearledger_rows.py --label new-label`.
Existing run files cannot be overwritten. Baseline measurements must actually run
against the preceding code; do not recreate them using a newer implementation.
The public `results-2026-10-04.json` retains measured source/code provenance,
checks, call counts and generation stops. Raw run outputs remain ignored.

See [CL-07 diagnosis and limits](../../docs/clearledger_row_correctness.md) and
[acceptance inputs](../../docs/clearledger_acceptance_inputs.md).
