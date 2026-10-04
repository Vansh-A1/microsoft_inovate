# ClearLedger fictional extraction challenge

Twelve original, locally generated sources: six tuning families and six reserved
holdout families. All names, facts and line prices are invented. These are not
customer documents, corporate policies, adjudicated risk labels or evidence of
production accuracy. No external inference or document download is involved.

The original fixture content is dedicated to the public domain under CC0 1.0.
ReportLab/PyMuPDF/Pillow render the sources; their implementation code is not
copied into the fixtures. `manifest.json` pins every source SHA-256 and keeps
post-extraction truth separate from the production input. The generator never
passes that truth to an adapter, provider or finance rule.

Freeze: `.venv/bin/python scripts/benchmark/clearledger_challenge.py --freeze`.
An existing manifest is preserved. Baseline holdout results are sealed while
tuning. Do not amend a frozen source to improve a result; create a new benchmark
version and disclose it. Runtime results remain ignored. No source is a private
uploaded invoice.

Families cover native side columns, labels above values, wrapped rows, a ruled
scan, sparse ambiguous scan, corrupt PDF, reserved landscape columns, reordered
three-page continuation, scanned cards, wrapped Times scan, conflicting invoice
identities and ambiguous numeric date/currency. The reserved families were not
used for tuning. They share vocabulary and invented facts with tuning sources;
this is a layout holdout, not a broad independent business-distribution holdout.
