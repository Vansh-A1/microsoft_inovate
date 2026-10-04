# ClearLedger public evaluation and local demo acceptance — CL-08, 2026-10-04

**The bounded local judge demo passes. General invoice automation does not pass
independent acceptance.** Four lawful externally authored fictional invoices expose
real source-association, header reconciliation, normalization and latency gaps.
None was submitted as a canonical finance transaction. All remain NEEDS_INPUT;
no extraction result was relabeled PASS. The engine, source confirmation, mandatory
controls, approved runtime/host and historical benchmark snapshots are unchanged.

Scope: Phase-6/final evaluation and handoff continuation. Files: new public-source
provenance/pixel truth/limited metrics, an actual local durable evaluation harness,
three comparator integrity checks and documentation. No application architecture,
production extraction/finance code, migration, dependency, UI/name, host security,
model or publication change. Earlier CL-04/05/06/07 data and outcomes remain intact.

## Independent source provenance and method

The [attributed four-source manifest](../data/clearledger_public/README.md) pins
SalorWorks' CC BY 4.0 fictional fixture pack and Dylan Merigaud's MIT generated
samples to exact public revisions. Their license notices and explicit fictional
provenance were checked before anonymous source downloads. No signup/token,
restricted data, real customer/private invoice or external inference was used.
GitHub's anonymous API returned 403 rate limiting; public anonymous revision lookup
and pinned raw files worked without credential changes. No repository programs,
expected JSON, external models or dependencies were run/downloaded. Required
credit/notices accompany the limited derived facts; original samples stay ignored.

All relevant original pixels were inspected, including both pages of p04, then
source truths/comparison policy were frozen on 0319cf4 before model output. Four
sources contain 19 items. Source/type erratum: p01's frozen description incorrectly
says native; its PDF is raster-only (zero native characters), so its measured
route includes OCR. The manifest/expected values are preserved; this correction
does not modify a score. p03/p04 native counts are 370 and 519/259 characters.

The actual loopback web proxy/API uploads feed existing PREPROCESS→EXTRACT→NORMALIZE
→VALIDATE→FINALIZE durable workers. A server-configured fictional finance identity
is used; no supplied UUID/role bypasses authorization. No fixture answers enter
the provider. Before/after extraction/normalizer hashes prove no pipeline change
or tuning against these sources. Original hashes and frozen truth hash accompany
the run. The measurement ends after final document state, not after a finance
decision. It does not auto-correct, activate policies, approve or execute payments.

Raw literal checks require appropriate observation state and correct row/page.
Money comparisons strip only the source's printed currency token and whitespace,
preserving decimal/group punctuation. p01 English name/description segments are
explicitly limited; Arabic fidelity is not scored. All wrong/ambiguous/unread rows
stay in the denominator. Normalized draft values, absence and required abstentions
are assessed separately; a safe null is not a successful literal read.

## Actual results

| External source | End-to-end s | Upload s | Header reads | Row reads | VLM calls |
|---|---:|---:|---:|---:|---:|
| p01 dense bilingual raster PDF | 90.736 | 0.143 | 7/8 | 7/21 | 5 |
| p02 rotated uneven-contrast PNG | 55.190 | 0.125 | 7/7 | 5/5 | 3 |
| p03 European decimal/stacked native PDF | 31.523 | 0.119 | 8/8 | 12/12 | 1 |
| p04 twelve items over two native pages | 58.822 | 0.117 | 3/8 | 48/48 | 2 |

Total **25/31 checked header literals, 72/86 checked row fields**, with all 19
source rows in the denominator. These are limited field checks on four synthetic
sources, not invoice-level or representative production accuracy. The 86 row checks
include p01's printed discounts/taxes/UOM and p02's UOM, alongside core description/
quantity/price/amount fields. The difficult source failures are not excluded.

All **23 checked absent header canonical candidates remain null** and all **five
required canonical abstentions pass**. Only 14/23 are explicit MISSING reads; the
other states/raw errors remain in the record. One p04 absent shipping field is
incorrectly PRESENT as "Delivery surcharge", but amount normalization rejects that
text; it remains null. The source has a delivery item, not a second header shipping
charge. These guards prevent unsupported acceptance, not extraction failure itself.

The GPU/CPU service was resident. These single observations include upload, proxy,
queue, preprocessing, extraction and final-state polling at 0.5 s, excluding human
review, browser rendering and approvals. No cold weight-loading or concurrent load
measurement was made. No old-code paired timing, per-request VRAM improvement or
universal warm-speed promise follows. Header generation alone costs about 28–29 s
per page; the rotating scan still needs three VLM calls. Existing actual provider
bounds remain 120 seconds, 32 calls and 200 rows; the observation bound is 300 s.

## What failed and what remains useful

1. **Wrong values can enter an unconfirmed normalized draft.** p01 document tax
   is incorrectly 4.80 instead of the visible 11.85, and later items repeat first-
   item descriptions/quantity/price with differing amounts. The exact-vector
   repetition guard therefore does not catch this pattern. Printed row discount/
   tax observations remain ambiguous, while some wrong core fields are PRESENT.
   NEEDS_INPUT, unresolved accounting and explicit source verification still block
   automatic finance clearance. This is the highest remaining extraction risk;
   review must not treat a normalized candidate as a verified printed fact.
2. **Multi-page header reconciliation loses readable facts.** p04 preserves all
   twelve native rows with actual page evidence, reusing eight/four independent
   items during header fallback. Provider null placeholders nevertheless contaminate
   the known issue date and second-page subtotal/tax/total. `$` correctly remains
   canonically unresolved; an address cannot establish USD. Future correction should
   distinguish absence/provider failure from genuine conflicting printed values,
   without permitting ambiguous facts to PASS.
3. **Literal read does not finish trusted normalization.** p03's euro glyph and
   European comma-formatted amounts are copied correctly, but current normalization
   leaves currency and monetary candidates null. Tax basis remains unprinted;
   a model's "tax-exclusive" guess is quarantined. A future versioned explicit
   locale/symbol rule needs source/business context; no FX, guessed zeros or inferred
   tax treatment belongs in canonical facts.
4. **Public complex layouts are still slow.** Native table reuse preserves all fifteen
   items without item-generation calls across p03/p04, but missing/uncertain headers
   still make expensive VLM reads. Layout/table/header grounding and request scope
   should be improved with the existing model before considering a larger model.
   This evaluation did not tune or install a replacement stack.

The absent-tax-basis source is an issuer/business-policy question, not permission
to invent an EXCLUSIVE value or zeros. Explicit source correction/approved versioned
policy is required where the existing mandatory accounting control needs it.

## Hard two-blank-cell development case

The previously inspected q06 is not a new independent sample. Its existing sidecar
retains one independently measured first row: Canvas file pouches, quantity 2,
price 31.00, amount 62.00, page 1 with actual boxes. The second source row has no
printed quantity or price; the third readable row is not recovered in the current
main candidate set. The VLM yields repeated unassigned candidates and stops after
inventory plus two row reads (**three calls / 28.927 pipeline s**, versus four calls/
39.109 s before). Main row literals remain 0/10, unconfirmed candidates ambiguous,
and absent quantity/price null. True independent first-row evidence is retained,
but full-row recovery/visibility is incomplete. Original snapshots are unchanged.

This case requires confirmed source row association and an authorized issuer source
for missing quantity/price; amount division is not evidence. No current production
code was relaxed or benchmark fact manufactured. A future bounded partial-row
improvement must prove ownership of readable cells/following rows and keep both
blank cells unknown, under the existing call/deadline limits.

## Local judge and minimum human-confirmation gate

The read-only computed walkthrough verifies eight scenarios with all 28 current
controls, current eligibility and exception citations. Clean source/approved demo
cases are PASS, paid duplicate/partial delivery/overflow are HOLD and allowance
exception REVIEW. Original correction HOLD remains retained. Expected outcomes
check persisted computations; no screen/engine result is hard-coded. Actual real
TypeLLM/model provenance and explicit source verification remain in the clean
visual walkthrough. Local API/web/worker/model health is READY.

Actual browser tests cover role entry/denial, Auto intake, readable source evidence,
invoice and expense source confirmation into computed HOLD while approvals remain
unmet, correction/revision history, missing quantity left blank/no false box,
corrupt source quarantine, loading/error/mobile states, plain result/report/audit,
manual business reference mapping without development templates and future
fictional hotel allowance 8000→9000 with actor/reason/effective date/history and
old report unchanged. A source checkbox cannot supply a genuinely absent fact.
The public evaluation sources were never corrected or committed to finance.

**15 browser cases passed; one conditional retained-UI-outage case skipped;
116.310 s, exit 0, one worker/zero retries.** The skip is not a passing outage drill.
Actual provider outage/retry checks from CL-07 remain separately recorded; the
resident service was not interrupted during this evaluation. Source/laptop/phone
screens were inspected. Scoped comparator integrity: **three passed / 0.03 s**;
wrong pages/ambiguous rows, comma rewrites and invented zero tax cannot inflate
the literal/absence score. No new full-backend or full-browser suite is claimed.

Executed commands:

```bash
.venv/bin/python scripts/benchmark/clearledger_public.py --label cl08-independent
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_public_evaluation.py -q --tb=short
.venv/bin/python scripts/release/judge_verify.py
.venv/bin/python scripts/demo.py health
```

From apps/web using the existing Node 24.21.0 PATH:

```bash
AP_RUN_CPU_OCR_BROWSER=1 npm run test:e2e -- tests/documents.spec.ts tests/release.spec.ts tests/hackathon.spec.ts tests/clearledger.spec.ts tests/cpu-ocr.spec.ts --grep-invert 'actual CPU scan|spent wrapped scan|separate identical items|actual unassigned VLM rows'
```

All commands above exit 0. The benchmark exit means four measurements completed,
**not** four invoices passed accuracy or finance screening. Provider/core code and
all prior evidence remain pinned. New full outputs/originals stay ignored; public
source/truth/limited metrics/notices are reviewable in the attributed corpus.

Final `compileall`, `git diff --check`, bounded `scripts/release/source_security.py`
(382 text files) and cached `scripts/release/secret_scan.py` (Gitleaks 8.30.1,
zero source findings/one redacted detection probe) exit 0. Read-only preservation
checks match all nine original pack/input hashes, working specification, 26 prior
frozen sources/all tracked corpus snapshots, four public originals, frozen pixel
truth and eight unchanged measured production hashes. Public totals recompute to
25/31 and 72/86. No fresh full-backend/full-browser suite or penetration-test claim.
Latest actual screenshots show Finance HOLD/next steps, source preview/evidence,
blank unread quantity without a fabricated box and Admin version 44 on laptop/phone.

## Acceptance disposition and prioritized next responsibility

The **local fictional hackathon demonstration passes within its stated bounds**:
owned startup/health, current computed walkthrough, roles, visible next actions,
source confirmation and retained policy/correction/report history. Demonstrate a
known validated layout, a blocked missing-value case and an actual HOLD; disclose
the external failures instead of promising arbitrary invoice automation.

Production acceptance remains blocked by independently adjudicated lawful real/
anonymized invoice families (target 40–60), approved company policy/accounting
sources, actual organization identity and malware engine/definitions, commercial
model attribution/provider acceptance and authorized release inputs. This public
sample research provides a lawful small independent layout probe, not those inputs.
No confidential/restricted alternatives were fetched to inflate the corpus.

Next bounded technical responsibility: repair header-versus-item source association
and multi-page null handling using preserved failures as **spent** regressions,
then evaluate new reserved layouts. Approved locale normalization and partial
multi-blank rows follow with explicit provenance/unknown states. Keep existing
finance controls, resident model and no-training-label governance. No push/public
deployment, stronger provider, paid service, credential/security/driver change is
authorized by this report.
