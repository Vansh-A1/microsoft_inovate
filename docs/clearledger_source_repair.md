# ClearLedger source repair — CL-09, 2026-10-04

**The bounded repair is implemented and verified locally.** Selected development
checks improve from **25/31 to 31/31 headers** and **72/86 to 86/86 row fields**.
Every measured document remains NEEDS_INPUT with no finance transaction/decision.
This is evidence of source repair on inspected fictional layouts, not invoice-level
accuracy, independently adjudicated business acceptance or production readiness.

Phase-6/final hardening responsibility: repair European monetary normalization,
provider-null contamination of multi-page headers and dense measured table
ownership; preserve the finance engine, immutable source/history and approved
BF16 runtime. Expected files were the existing layout/native/provider/worker/
normalizer, scoped tests and benchmark/decision/progress evidence. Financial Decimal,
UNKNOWN, source confirmation, tenant/entity authorization and mandatory controls
remain requirements. Verification covers meaningful source/geometry boundaries,
actual migrated CPU/document/finance behavior, resident real-model probes, both
UI roles and source/secret/preservation checks. No migration, financial engine,
policy master, production UI, dependency, model, host or publication change.

The project overview/specification, exit reviews, registers, local Codex context
and applicable checkout skills/instructions were inspected. A final thread check
shows this is the only active task in this checkout; the separate portfolio task
uses another directory. Its files were untouched.

## Implemented behavior

- New **document-normalizer-v4** drafts recognize supported explicit ISO currency
  and unique euro/rupee symbols. Printed monetary tokens can establish a derived
  source currency with the real monetary locator and derivation diagnostic.
  Dollar/yen/pound alone or conflicting units stay ambiguous; country/address/
  merchant currency and FX cannot pick a currency.
- Decimal-comma money is selected from PRESENT independently measured monetary
  cells with unambiguous printed separators. Traces retain raw text, contributing
  observation IDs and format/version. Strong mixed conventions, invalid grouping
  and isolated three-digit separators without supporting format evidence stay
  unresolved. Date locale and dimensionless quantity/rate syntax are separate.
  v2/v3 drafts and historical evaluations are retained.
- **printed-layout-v5 / native adapter 7** handles qualified stacked labels,
  narrowly bounded native-font extent overlap and distant left-column text. An
  inline value stays with its printed row. Dense SKU/barcode tables can use
  centered/wide text headings only when actual neighboring regions do not overlap
  and all financial/unit cells satisfy independent heading anchors. Missing shifted
  cells, crossing financial geometry and competing observations abstain. Every
  retained box is a measured detector/font region; crop extents are not field boxes.
- **extraction-routing-v6** reuses independently read document headers across
  pages and previous actual reads. With measured coverage it asks only unresolved
  core fields and first-page supplementary addresses. Known printed conflicts and
  ambiguous source currency remain human questions, not additional model votes.
  Unmeasured incomplete visual pages keep the broader contract. Actual requested
  fields/calls/seconds are retained; routing never creates a finance decision.
- Model PRESENT/AMBIGUOUS with raw null becomes **ILLEGIBLE/raw null**, tagged
  PROVIDER_VALUE_UNREAD. It cannot fabricate literal null or override a measured
  PRESENT source. Genuine non-null conflicts/illegibility remain unresolved.
  Unsupported model-only summary tax/discount/shipping/other charges retain raw
  AMBIGUOUS evidence and canonical null unless an independent summary label
  corroborates scope. An item amount, tax arithmetic or guessed zero is not proof.

[ADR-0018](adr/0018-source-context-normalization-and-header-reuse.md) records these
actual decisions. There are no invoice identity exceptions, truth-fed model prompts,
fine-tuning, fabricated accounting facts or changed approval/budget/ledger rules.

## Frozen source evidence and actual final measurements

[CL-08 baseline](clearledger_independent_validation.md), its original sources,
truth and scores remain unchanged. The four cases became spent development inputs
when their failures were inspected. [Final limited results](../data/clearledger_public/development-final-results-cl09-2026-10-04.json)
pin all eight production file hashes and the original truth hash. Full documents,
IDs, pixels and API outputs remain ignored. The pre-inline-fix successful probe is
separately retained in `development-results-cl09-2026-10-04.json`; it does not
replace the final gate or conceal the intervening CPU regression.

| Source | Header checks before → after | Row fields before → after | VLM calls before → after | End-to-end seconds before → after |
|---|---:|---:|---:|---:|
| p01 dense bilingual raster PDF | 7/8 → 8/8 | 7/21 → 21/21 | 5 → 1 | 90.736 → 17.286 |
| p02 rotated uneven scan | 7/7 → 7/7 | 5/5 → 5/5 | 3 → 3 | 55.190 → 39.226 |
| p03 European native PDF | 8/8 → 8/8 | 12/12 → 12/12 | 1 → 1 | 31.523 → 13.524 |
| p04 two-page native PDF, twelve items | 3/8 → 8/8 | 48/48 → 48/48 | 2 → 1 | 58.822 → 14.087 |

All 19 rows/five pages remain in the denominator. Monetary literal comparison
strips only independently printed unit tokens/whitespace; punctuation, source page
and observation state remain checked. p01's English substrings are explicitly
limited; Arabic glyph fidelity is unscored. The frozen p01 native classification
erratum remains: its PDF is raster-only, with zero native characters.

All **23/23 absent canonical candidates remain null**, now **23/23 explicit
MISSING/raw null**, and **five required canonical abstentions** pass. p01 tax is
source-read AED 11.85 instead of the previous wrong 4.80; three independently
measured OCR rows replace repeated VLM vectors. p03 printed `1.198,93 €` normalizes
to decimal string `1198.93`/EUR. p04 retains issue/due dates and second-page totals
with measured page ownership; dollar currency and monetary canonical candidates
remain null. Missing tax basis/accounting facts and source confirmation still
prevent finance submission.

Actual call causes: p01 10.817 s header, zero model inventory/row generation;
p03 10.671 s header and three native rows reused; p04 10.630 s header, eight/four
rows reused, zero second-page header calls. The reduced header contract replaces
~28–29 s baseline header generations. p02 still costs **11.425 s header + 4.953 s
inventory + 16.905 s row generation**. Improving layout reuse removed calls where
source evidence exists; rotation remains a real unresolved bottleneck.

These are single before/after observations on the same bytes with different code,
not randomized repeated paired timing distributions. The model remains resident;
first app/CPU-client initialization can be cold, later requests are warm. Durations
include loopback upload/proxy/queue/processing/final 0.5 s polling, exclude browser/
human/approval time, and were collected after the integration load ended. No cold
weight load or universal warm-speed/per-request VRAM claim follows. Earlier actual
r07 cold/warm worker observations (6.469/6.883 s, warm slower) remain in CL-07 and
are not relabeled CL-09 evidence.

## Additional reserved source facts and hard failure

[Two additional lawful fictional probes](../data/clearledger_public_reserved/README.md)
were pixel-checked and truth frozen on 515f391 before tuning/execution and before
the latest no-more-acquisition instruction. Pinned CC BY 4.0/MIT notices/attribution
are retained. No author expected JSON/generators/services were used. They share
authors/template families; u01 shares the p03/p04 native family. They are not
genuinely held-out layout families, unknown-training-overlap evidence, business
adjudication or the requested 40–60 real/anonymized source corpus. No further data/
model/runtime acquisition or training followed.

Initial reserved execution passed **15/15 header, 21/21 row, 12/12 absent canonical
null, 11/12 explicit MISSING and four required abstention checks**, at 13.568/15.610 s.
After the separately discovered inline-total fix, [final spent regression](../data/clearledger_public_reserved/final-results-2026-10-04.json)
retains those checks at **14.721/16.088 s**, one actual model call each. u01 preserves
both identical compute items at separate source positions and does not infer USD
from dollar. u02 keeps explicit invoice USD despite merchant AED, total 172.00 and
shipping 12.00; absent tax remains ILLEGIBLE/raw null/canonical null, not invented
zero (the twelfth absence is not scored as explicit MISSING). Initial inherited
metadata incorrectly said four sources; the two-case manifest/scores are unchanged
and the final harness metadata states the actual count. Both probes are now spent.

The existing **q06 two-blank-cell case still fails 0/10 readable row checks**, with
7/7 headers and three retained inventory slots. Its real first row remains in
candidate-disagreement drill-down, not recovered as a verified main row. Both
absent quantity/price remain canonical null; three absent headers remain MISSING;
no unsupported row observation/canonical candidate is PRESENT. Final real-model
execution took **30.485 s**, three calls, **6.899 s inventory + 22.782 s rows**, and
stopped actual repeated unassociated candidates. It remains NEEDS_INPUT/no finance
result. Its incidental sampled **whole-device peak 15974 MiB** includes resident
weights/allocator/other processes; it is not request allocation or a VRAM improvement.
The historical holdout label is retained, but this inspected case is explicitly spent.

## Verification and retained failures

| Executed check | Result |
|---|---|
| Final focused extraction/source/schema/scoping suite | **183 passed / 4.41 s / exit 0** |
| Finance/security/governance/duplicate/rules/scanner/worker unit regression | **125 passed / 0.88 s / exit 0** |
| Actual CPU OCR + migrated durable pipeline + both source-to-finance branches | **24 passed / 363.03 s / exit 0** |
| Four final actual-model development documents | **exit 0**, selected checks above; all NEEDS_INPUT |
| Two initial reserved and two final spent regression documents | **exit 0**, selected checks above; all NEEDS_INPUT |
| Final actual-model q06 hard case | **exit 0** measurements completed; **0/10 rows**, not accuracy PASS |
| Initial combined browser run | **16 passed / one selector failure / one conditional outage skip / 132.647966 s / exit 1** |
| Affected selector-only rerun | **one passed / 2.7 s / exit 0** |
| Final actual-source browser checks on current final-code documents | **two passed / 4.438873 s / exit 0**, one worker/no retries/skips/flakiness |
| TypeScript typecheck / Python compilation / whitespace | **exit 0** |
| Read-only current judge | **eight computed scenarios / 28 controls each / exit 0**; original correction HOLD and current eligibility/citations retained |

The first focused run had **126 pass/two failures/3.56 s/exit 1** (a new test stub's
missing model attribute and unnecessary model question for a measured printed
conflict). Both were fixed; 128/142/145/182 and final 183 focused passing runs are
retained. The first model repair iteration still failed p01 rows **1/21** at
61.060 s/five calls; that failure drove generic measured metadata-cell ownership,
not source-name special cases. Full intermediate measurements remain ignored
under unique labels; none overwrites baseline truth/results.

An initial actual CPU integration run failed t04. Targeted diagnosis was **one
failed/13.95 s/exit 1**: expected printed total `236.00`, actual raw total incorrectly
`Tax basis: EXCLUSIVE`, canonical null. The new stacked parser had treated distant
same-row numeric text as unrelated, then claimed the next row. Rejecting right-side
text for stacked ownership preserves inline values. A meaningful regression test
was added; the original actual CPU assertion was unchanged. Final 24-case actual
integration passes, including tenant denial, unresolved-source commit guard,
legitimate equal items, child restart/fallback, immutable corrections/reports,
approval HOLD before authorized actions, attachments and embedded-instruction
resistance. Isolated test schemas migrate from fresh setup and are torn down under
test ownership; the demo/history/database were preserved. No full backend or all
old GPU suite rerun is claimed.

The browser failure was a new test selector for Source page, not incorrect page
ownership. It was changed to the existing accessible combobox role. Fifteen other
existing browser cases passed in that combined run, including Finance/Admin denial,
Auto intake, invoice/employee computed HOLD, missing quantity, correction/revision/
report history, quarantine/loading/error/mobile and future fictional hotel allowance
version **46**, reason/effective date/audit with old report preservation. The final
two source tests read actual durable documents without supplying truth/corrections:
measured p01 tax/rows, euro raw/canonical values, blocked confirmation, page-two
boxes and unresolved dollar. Laptop/390 px phone and Admin screens were visually
inspected. No clean combined 17-case rerun is fabricated. The outage fixture skip
is not a new provider-outage drill; CL-07 retains its actual earlier outage evidence.

Source/secret/preservation gate: **392-text-file bounded source scan / exit 0**;
**cached Gitleaks 8.30.1 zero findings and one redacted detection probe / exit 0**;
finance and isolated CPU `pip check` both exit 0. Original nine checksums/spec, 26
prior fictional source hashes, 40 tracked historical corpus/evidence files and six
public originals passed; new results pin the unchanged production hashes throughout
each run. Originals, private source/model/settings/weights/runtime outputs remain
ignored. Final health is READY, required VLM AVAILABLE; GPU readback is RTX 2000 Ada,
driver 550.120, total 16380 MiB, and finance Python remains 3.13.11.

## Reproduce and hand off

Use the existing loopback ClearLedger app at `http://127.0.0.1:3000`. Both synthetic
role experiences stay available; real identity/scanner/business activation remains
an acceptance input, not supplied by a local demo. The app, API/worker and approved
resident model were healthy after the controlled app-only reload. No model stop,
host/driver/Docker/system/security/credential change, paid service, public deployment
or GitHub push was performed. Finance Python 3.13 and isolated serving/CPU runtimes
remain intact. TypeLLM 0.5.1 provenance is real; its client Transformers 5.3.0 is
separate from the preserved SGLang runtime Transformers 4.51.1. Qwen2.5-VL-3B revision
66285546d2b821cf421d4f5eb2576359d3770cd3 stays BF16 on the unchanged 550.120 driver.

```bash
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_clearledger_source_repair.py apps/api/tests/test_cpu_ocr.py apps/api/tests/test_extraction_documents.py apps/api/tests/test_clearledger_layout.py apps/api/tests/test_clearledger_grounding.py apps/api/tests/test_clearledger_row_identity.py apps/api/tests/test_vlm_integration_contract.py apps/api/tests/test_public_evaluation.py apps/api/tests/test_clearledger_worker.py apps/api/tests/test_documents_phase2.py -q --tb=short
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_rules_phase1.py apps/api/tests/test_finance_controls_unit.py apps/api/tests/test_duplicates_phase3.py apps/api/tests/test_risk_phase5.py apps/api/tests/test_release_boundaries.py apps/api/tests/test_clearledger_scanner.py apps/api/tests/test_clearledger_worker.py -q --tb=short
AP_RUN_CPU_OCR=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_cpu_ocr_live.py apps/api/tests/integration/test_document_pipeline.py apps/api/tests/integration/test_document_finance.py -q --tb=short
.venv/bin/python scripts/benchmark/clearledger_public.py --label a-new-development-label
.venv/bin/python scripts/benchmark/clearledger_public.py --corpus clearledger_public_reserved --label a-new-spent-regression-label
.venv/bin/python scripts/benchmark/clearledger_rows.py --label a-new-q06-label --case q06
.venv/bin/python scripts/release/judge_verify.py
.venv/bin/python scripts/release/source_security.py
.venv/bin/python scripts/release/secret_scan.py
.venv/bin/python -m pip check
runtime/ocr-rapid/.venv/bin/python -m pip check
.venv/bin/python scripts/demo.py health --require-vlm
git diff --check
```

Final executed labels were `cl09-final`, `cl09-reserved-final` and
`rows-cl09-final-q06`; exit zero means measurement finished, never invoice PASS.
Harnesses reject label overwrite, validate source/code/truth hashes and score only
after output. For browser/typecheck, cwd `apps/web`, prepend the existing project
Node 24.21.0 `runtime/tools/node-v24.21.0-linux-x64/bin` to PATH:

```bash
AP_RUN_SOURCE_REPAIR_BROWSER=1 AP_RUN_CPU_OCR_BROWSER=1 npm run test:e2e -- tests/source-repair.spec.ts tests/documents.spec.ts tests/release.spec.ts tests/hackathon.spec.ts tests/clearledger.spec.ts tests/cpu-ocr.spec.ts --grep-invert 'actual CPU scan|spent wrapped scan|separate identical items|actual unassigned VLM rows'
AP_RUN_SOURCE_REPAIR_BROWSER=1 npm run test:e2e -- tests/source-repair.spec.ts
npm run typecheck
```

First browser metrics/failure image and final metrics are preserved under ignored
`runtime/clearledger/browser-cl09-first.json`, `browser-cl09-final.json` and
`output/playwright/qa-cl09-first-selector-failure.png`. Final real-source laptop/
phone screenshots are `output/playwright/cl09-*-source-*.png`; current policy
screens retain version 46. Exact actual integration output is
`runtime/clearledger/integration-cl09-final.log`. These are local evidence, not
public confidential exports. Reviewed local commit only; publication is separate.

Remaining work is explicit: rotated/page/crop recognition on the current engine,
source-backed q06 association and absent-field clarification, Arabic/RTL fidelity,
less verbose reviewer field presentation, genuinely independent adjudicated vendor/
layout families (40–60 acceptance target) and approved business/source facts. Actual
organization identity, scanner definitions, provider/model attribution and pilot/
release inputs remain separate gates in [the acceptance checklist](clearledger_acceptance_inputs.md).
A stronger fallback is not configured/authorized; no new acquisition, fine-tuning,
paid service or inferred policy follows. The local fictional demo passes its bounded
gate; broader automation/production acceptance remains unmet.
