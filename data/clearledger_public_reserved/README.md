# CL-09 reserved public source probe

Two additional independently authored **fictional** sources, frozen on 515f391
before production tuning. Original pixels were manually checked; author expected
JSON/generators/services were not fetched or used. Five item rows on two pages.
These are reserved from tuning/model execution until the CL-09 implementation is
fixed, not independently adjudicated real-company data or unknown-training-overlap
evidence. No later source acquisition or training is authorized.

- **u01**, Dylan Merigaud, AI Invoice Parser, `eval/samples/duplicate-lines.pdf`,
  revision `5b54f4b5969452cc282b27f0327fbc886f9f6358`, MIT, copyright 2026 Dylan Merigaud.
  [Pinned source](https://github.com/DylanMerigaud/ai-invoice-parser/blob/5b54f4b5969452cc282b27f0327fbc886f9f6358/eval/samples/duplicate-lines.pdf).
  Four separately printed items, including equal items at distinct positions;
  dollar currency cannot establish USD. Reuse notice:
  [merigaud-LICENSE.txt](../clearledger_public/merigaud-LICENSE.txt).
- **u02**, SalorWorks, Synthetic Shopify Invoice Test Pack,
  `fixtures/08-usd-for-aed/invoice.pdf`, revision
  `bb2e531cfa504e6f7200243620121c523f9f7622`, CC BY 4.0, copyright 2026 Salorworks.
  [Pinned source](https://github.com/SalorWorks/shopify-invoice-test-pack/blob/bb2e531cfa504e6f7200243620121c523f9f7622/fixtures/08-usd-for-aed/invoice.pdf).
  Explicit invoice USD differs from merchant-store AED; tax is absent.
  [salor-LICENSE.txt](../clearledger_public/salor-LICENSE.txt) and this attribution
  accompany limited derived evaluation facts. Original bytes are unchanged.

Pinned license/README checks are inherited from the CL-08 manifest; source download
receipts/hashes and manual truth are in the frozen `manifest.json`. Original PDFs,
rendered source pages and full outputs remain in ignored runtime. Monetary literal
checks remove only printed currency tokens/whitespace and preserve punctuation;
all rows/page associations and required canonical abstentions remain scored.

```bash
.venv/bin/python scripts/benchmark/clearledger_public.py --corpus clearledger_public_reserved --label a-new-label
```

The local harness cannot overwrite an existing label and never injects truth,
corrects finance facts, sends sources externally or executes source instructions.
Exit zero means measurements completed, not finance PASS. After this measurement
these cases are spent regression evidence, not fresh unseen acceptance samples.
They share authors/template families with development sources; in particular u01
uses the same native template family as p03/p04. They check new source facts and
equal-row/currency safety, not genuinely held-out vendor/layout-family accuracy.

Initial fixed-code execution is retained in `results-2026-10-04.json`. Its inherited
limitation text incorrectly says four sources; the manifest and actual cases
contain two. `final-results-2026-10-04.json` records final-code regression execution
after the separately discovered inline-total fix, with corrected source-count
metadata. No original truth or initial score was rewritten. Both executions are
now spent; neither supports a new-layout-family acceptance claim.
