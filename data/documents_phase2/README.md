# Actual synthetic document corpus

Created by `scripts/seed/document_fixtures.py` from fictional printed labels and
amounts. All files are synthetic; no real finance/customer data or payable bank
details. These are actual PDF/PNG/JPEG bytes, distinct from Phase-0 replay JSON.
`expected.json` is independent printed ground truth, never read by extraction.
`fixtures.sha256` pins bytes; originals in the established team pack and fixture
collections are unchanged.

Native invoice, two-page invoice with repeated headers, native receipt, scan PDF,
scan PNG, EXIF-rotated JPEG, unreadable low-resolution image, ambiguous date,
missing/conflicting total, uncertain two-invoice bundle, document instructions,
encrypted PDF and corrupt PDF exercise processing and explicit uncertainty.
The password fixture is a pinned encrypted rejection seed, preserved on
regeneration because MuPDF randomizes encrypted IDs. It is not a storage-encryption example. The synthetic table uses an explicit
pipe-delimited layout so native parsing can be verified within its bounded scope.

Rendered native/multi-page PDFs and the oriented photograph were visually checked
for clipping/legibility. Measurements concern this small synthetic corpus only;
they establish neither real-model accuracy nor production document quality.
