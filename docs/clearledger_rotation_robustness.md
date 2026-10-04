# CL-10 — bounded rotation and partial-row robustness

The current pinned engine now retains measured headers/tables on upright, quarter-turn and supported small-skew scans while preserving original evidence and missing-field holds. No finance engine, UI, model, runtime package, host setting or deployment was replaced. This closes the bounded extraction responsibility; further UI work is deferred by the latest instruction.

## Scope and source controls

Before implementation, `scripts/benchmark/clearledger_rotation.py --freeze` froze three original invented CC0 base PDFs and ten correlated PNG variants at CL-09 `0c690800b82d8597debb19876c3b2e25c79ef722`. The manifest pins source hashes, dimensions, literal truth, absent facts and split. One development family has upright/+6°/90° variants. Seven reserved variants from **two NEW synthetic families** cover upright/90°/180°/270°/+4°/−5°, including two absent quantity/price pairs. Reserved CPU baseline outputs stayed sealed through tuning and were opened only after one final reserved run. All are now spent. Expected rotations/truth never enter OCR/VLM prompts or upload metadata.

Original pack/ZIP/spec, older fictional/public originals, frozen truth/results, finance histories and isolated Python environments are preserved. No more source/model acquisition, fine-tuning, external inference, driver/Docker/security/credential change, paid service or publication. The portfolio checkout is untouched. All full raw artifacts remain ignored under `runtime/clearledger`; limited original-fictional evidence is [tracked here](../data/clearledger_rotation/measurements-2026-10-04.json).

## Implemented behavior

- Actual OCR quadrilaterals establish four rigid layout candidates and small global deskew. A unique sufficient printed-header/table/physical-axis candidate selects orientation. Ties, missing polygons, inconsistent/excessive skew and weak ownership abstain.
- One bounded actual CPU reread of a private in-memory aligned derivative recovers glyphs absent from the first read. Record the actual PNG hash/dimensions/transform/Pillow version. No original/preview bytes are rewritten; actual detector regions project back to original coordinates. Optional layout refinement requires measured second-read geometry, without a third image read.
- Existing maximum three numeric-cell crop attempts share the original 15-second page and 30-second document deadlines. Inverse-projected crop context is never presented as a field box. Source EXIF transforms remain independent.
- Corresponding measured read conflicts stay AMBIGUOUS/canonical null and require human source confirmation. Source conflict cannot be settled by another model vote. Actual raw alternatives stay in the scoped private sidecar.
- Unique independently printed table panels separate header baselines from item baselines. Actual description/amount anchors retain a partial row with missing quantity AND price, preserve subsequent/equal rows, and generate precise source questions. No inferred arithmetic, UOM, tax basis, zero, currency, policy or PASS.

Versions: native adapter 8, labeled layout v8/printed layout v6, CPU measured alignment v1/numeric-cell retry v2. Existing TypeLLM routing, normalization v4, strict extraction-v1, financial Decimal/currency/authorization/version/capacity controls remain. [ADR-0019](adr/0019-source-preserving-ocr-orientation.md) records the decision.

## Actual measurements

These are individual observed timings, not statistically established speed claims. Pipeline measurements include preprocessing and production CPU child startup on the first read, exclude upload/DB/queue/UI/confirmation, and use resident GPU weights. CPU-only baselines are distinguished from configured-provider measurements. Selected literal/state checks count all wrong/missing/ambiguous fields. Successful execution of the harness does not mean correct extraction or finance clearance.

| Spent development variant | Unchanged configured provider: headers / rows / seconds / VLM calls | Final configured provider: headers / rows / seconds / calls |
|---|---|---|
| d01 upright side panel | 4/7; 0/12; 27.665 s; 3 | 7/7; 12/12; 1.986 s; 0 |
| d02 +6° scan | 6/7; 0/12; 61.396 s; 4 | 7/7; 12/12; 3.830 s; 0 |
| d03 90° scan | 6/7; 4/12; 45.909 s; 3 | 7/7; 12/12; 3.312 s; 0 |

Initial d03 guessed UOM “Qty”; its wrong source/table/header candidates remain in the baseline record. Final development has 21/21 header and 36/36 row checks, all 18 absent header fields explicit MISSING/canonical null, no unsupported row values, and NEEDS_INPUT/no finance result.

| Newly reserved variant, now spent | CPU baseline headers / rows / seconds | Final CPU headers / rows / seconds |
|---|---|---|
| r01 upright landscape | 6/7; 12/12; 2.174 | 6/7; 12/12; 2.218 |
| r02 landscape 90° | 0/7; 0/12; 2.196 | 6/7; 12/12; 4.033 |
| r03 landscape 180° | 0/7; 0/12; 1.778 | 6/7; 11/12; 3.391 |
| r04 landscape 270° | 0/7; 0/12; 1.749 | 6/7; 11/12; 3.413 |
| r05 landscape +4° | 1/7; 0/12; 1.940 | 7/7; 12/12; 4.057 |
| r06 portrait −5°, two blank cells | 0/7; 0/10; 2.165 | 7/7; 10/10; 5.092 |
| r07 portrait 90°, two blank cells | 0/7; 0/10; 1.988 | 6/7; 10/10; 3.724 |

Reserved total **7/49→44/49 headers, 12/80→78/80 rows**; all 21 rows retained. Four supplier reads remain missing. r03/r04 have measured 9-versus-6 quantity conflicts: final raw 6 remains AMBIGUOUS/canonical null. r07 tax has 00-versus-0.00 conflict: AMBIGUOUS/null. No cherry-picking or tuning on these reserved failures followed. All 42 absent header checks are MISSING/null; all four missing quantity/price abstentions pass; no unsupported PRESENT or canonical row values; every case NEEDS_INPUT/no finance result. Safe abstention is separate from literal accuracy.

A separate actual first-process d03 read is **3.432 s**, same-process repeat **3.054 s**; isolated CPU model initialization **0.261713 s**, actual summed OCR stages **2.792328 / 2.748458 s**. This is one worker cold/repeat pair under shared-host activity, not cold GPU weight load or latency distribution. Incidental whole-device peaks **13,679–13,697 MiB** include resident GPU weights/other processes; CPU OCR allocates no GPU. No per-request VRAM improvement is claimed.

Spent q06: final **7/7 headers, 10/10 visible row facts**, all three rows including the two absent cells, both canonical null, no unsupported values, **0.229 s / zero VLM calls / NEEDS_INPUT**. CL-09 had 0/10 rows, 30.485 s/three calls. Native text, independently printed columns/amount and human questions supply partial capture; no inferred quantity/price or forced metric.

## Verification and honest failure history

Final pure suites: **209 passed / 4.51 s / exit 0** extraction/worker/grounding/intake, including 26 new orientation cases; **125 passed / 0.86 s / exit 0** retained finance/security/governance. The focused geometry batch passes **102 / 2.10 s** before the larger run. Ruff fatal checks, compilation, finance `pip check` and TypeScript check return exit 0. No new full all-application test claim.

Intermediate failures remain recorded: initial test collection exposed established DB import order; initial grouping tests needed a realistic preceding-row crossing fixture; actual development runs exposed a shadowed serializer import and a physical-axis aspect check that incorrectly used normalized rectangular coordinates. Subsequent ambiguity test fixtures initially supplied native spans for an image-only input and therefore correctly produced a separate provider disagreement. The fixtures were corrected to the actual native-empty image path; uncertainty/finance assertions were retained. Virtual-only and partial development measurements remain private and are not hidden by final scores.

Actual database/API/browser/security/preservation results are recorded below after completion. No outstanding measurement is represented as a pass.

## Final boundary correction and live verification

The first live public comparison exposed a real regression: a deskewed detector box for a synthetic top banner projected **4.462 pixels above the original canvas**. Strict `mapped_spans` correctly rejected it, but rejecting the whole optional read caused real Tesseract fallback and incorrect ambiguous vendor/tax candidates. The first batch p02 remains **5/7 headers, 5/5 rows, 28.499 s/two calls**; a pre-reload repeat remains 28.500 s. Both failed observations are preserved. This was a source-canvas validation repair, not tuning on reserved truth.

The child now **excludes and records the actual out-of-canvas detector region** instead of clipping/inventing a field box or rejecting all valid regions. Strict parent geometry rejection remains. Actual derivative hash/transform and excluded raw region/reason remain private/scoped; it supplies no canonical fact. A fresh real CPU regression verifies unchanged preview bytes, one excluded banner, all retained boxes in the original canvas, measured tax and table. Five final affected actual OCR/DB/crop/scope/partial-row cases pass **5 / 5 deselected / 55.86 s / exit 0**. The earlier full actual migrated pipeline/finance batch passes **26 / 399.84 s / exit 0**; these are separate runs, not one fabricated total. Final pure extraction suite repeats **209 / 4.50 s / exit 0**. Finance/security **125 / 0.86 s / exit 0** remains unaffected.

A **spent replay**, after the boundary correction, retains exactly **44/49 headers, 78/80 row facts, 21 rows, 42 missing/null header facts, four missing-cell abstentions** and the same explicit reserved failures. Recorded seconds r01–r07: **2.207, 3.443, 3.500, 3.636, 4.027, 4.568, 3.735**. These are not another held-out run. Incidental whole-device maximum **14,155 MiB** during overlapping actual checks is not request VRAM. First reserved measurements/code hashes remain separate.

Actual loopback upload/proxy/durable worker/final-result observations, at 0.5 s polling:

| Source | Checked headers / rows | Seconds / actual VLM calls | Outcome |
|---|---|---|---|
| d03 original 90° | 7/7; 12/12 | 6.915 / 0 | NEEDS_INPUT; original hash/boxes preserved |
| r02, now spent 90° | 7/7; 12/12 | 13.032 / 1 | Supplier read by actual pinned provider; all absent facts null |
| r06, now spent −5°/two blanks | 7/7; 10/10 | 7.440 / 0 | Both blank quantity/price null; precise source questions |
| p01 spent dense public | 8/8; 21/21 | 15.628 / 1 | Measured summary tax retained |
| p02 final spent public deskew | 7/7; 5/5 | **19.300 / 1** | RAPIDOCR_CPU, one excluded banner, no fabricated tax treatment |
| p03 spent euro public | 8/8; 12/12 | 14.020 / 1 | EUR/decimal-comma normalization preserved |
| p04 spent multi-page public | 8/8; 48/48 | 14.081 / 1 | Page-two totals/equal rows/dollar ambiguity retained |

The final p02 is a separate targeted run after the boundary correction; the other three public results are from the first batch on the unaffected paths. Do not present a fictitious single final-code four-source run. Selected current public facts remain **31/31 headers and 86/86 row checks** across these recorded runs, all 19 rows, required nulls, NEEDS_INPUT/no finance result. p02 improves from CL-09 **39.226 s/three calls** to 19.300 s/one call; no full Arabic/address/business completeness or latency distribution is claimed. Full raw files/code hashes remain ignored and limited measurement links are tracked.

Final actual source browser **three passed / 2.1 s / exit 0**, one worker/no retries/skips: original 90° field overlay, skewed partial row/null source questions, final p02 source tax/excluded region; laptop 1280×720 and phone 390×844 have no document-width overflow. Separate existing role-login check **one passed / 1.0 s / exit 0** verifies Finance/Admin authorization and mobile views, with no policy write. Screens were visually inspected. Small rotated source text/long technical review tables remain UI polish limits; no redesign was performed. Existing CL-09 future allowance version 46/audit/report evidence is preserved, not rerun or claimed changed.

Read-only judge verifies all eight current **computed** scenarios with 28 controls and eligibility; PASS/HOLD/REVIEW remain distinct from processing/source status. Final typecheck/compilation/fatal Ruff checks and finance dependency integrity pass. Cached Gitleaks 8.30.1: zero source findings plus one detected/redacted probe. Original nine pack/ZIP hashes, all 105 prior tracked data files, 28 historical spec/exit/ADR files and 13 new frozen originals pass byte/hash preservation. No push, public deploy, hosted identity/scanner configuration, new model/dependency/host changes or cloud spend. Local app/API/web/worker READY; pinned inference AVAILABLE.

## Reproduction commands actually executed

Run at repository root with the existing finance Python, and server-local configured OCR/provider settings. Sources/truth enter only scoring. Exit zero from a benchmark means completed measurement, not business PASS.

```bash
.venv/bin/python scripts/benchmark/clearledger_rotation.py --freeze
.venv/bin/python scripts/benchmark/clearledger_rotation.py --label baseline --split tuning
.venv/bin/python scripts/benchmark/clearledger_rotation.py --label cpu-baseline --split tuning --cpu-only
.venv/bin/python scripts/benchmark/clearledger_rotation.py --label cpu-baseline --split holdout --cpu-only
.venv/bin/python scripts/benchmark/clearledger_rotation.py --label provider-final --split tuning
.venv/bin/python scripts/benchmark/clearledger_rotation.py --label cpu-final --split holdout --cpu-only
.venv/bin/python scripts/benchmark/clearledger_rotation.py --label cpu-verified-spent --split holdout --cpu-only
.venv/bin/python scripts/benchmark/clearledger_rows.py --label rotations-final-q06 --case q06
.venv/bin/python scripts/benchmark/clearledger_public.py --label cl10-d03 --corpus clearledger_rotation --case d03
.venv/bin/python scripts/benchmark/clearledger_public.py --label cl10-final
.venv/bin/python scripts/benchmark/clearledger_public.py --label cl10-r02 --corpus clearledger_rotation --case r02
.venv/bin/python scripts/benchmark/clearledger_public.py --label cl10-r06 --corpus clearledger_rotation --case r06
.venv/bin/python scripts/benchmark/clearledger_public.py --label cl10-p02-final --case p02
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_clearledger_orientation.py apps/api/tests/test_clearledger_source_repair.py apps/api/tests/test_cpu_ocr.py apps/api/tests/test_extraction_documents.py apps/api/tests/test_clearledger_layout.py apps/api/tests/test_clearledger_grounding.py apps/api/tests/test_clearledger_row_identity.py apps/api/tests/test_vlm_integration_contract.py apps/api/tests/test_public_evaluation.py apps/api/tests/test_clearledger_worker.py apps/api/tests/test_documents_phase2.py -q --tb=short
PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_rules_phase1.py apps/api/tests/test_finance_controls_unit.py apps/api/tests/test_duplicates_phase3.py apps/api/tests/test_risk_phase5.py apps/api/tests/test_release_boundaries.py apps/api/tests/test_clearledger_scanner.py apps/api/tests/test_clearledger_worker.py -q --tb=short
AP_RUN_CPU_OCR=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_cpu_ocr_live.py apps/api/tests/integration/test_document_pipeline.py apps/api/tests/integration/test_document_finance.py -q --tb=short
AP_RUN_CPU_OCR=1 PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_cpu_ocr_live.py -q --tb=short -k 'border_padding or rotated_scan or two_blank_cells or wrapped_scan or source_scope'
.venv/bin/python scripts/release/judge_verify.py
.venv/bin/python scripts/release/source_security.py
.venv/bin/python scripts/release/secret_scan.py
sha256sum -c docs/source_inputs.sha256
runtime/release-tools/bin/ruff check apps/api/app --select E9,F63,F7,F82
.venv/bin/python -m compileall -q apps/api/app scripts/benchmark/clearledger_rotation.py scripts/benchmark/clearledger_public.py
.venv/bin/pip check
```

For browser/typecheck, cwd `apps/web`, prepend `/data/vansh/microsoft_inovate/runtime/tools/node-v24.21.0-linux-x64/bin` to PATH and set PLAYWRIGHT_BROWSERS_PATH to the existing project `runtime/playwright`:

```bash
AP_RUN_ROTATION_BROWSER=1 npm run test:e2e -- tests/rotation-source.spec.ts --workers=1 --retries=0
npm run test:e2e -- tests/clearledger.spec.ts --grep 'local role entry' --workers=1 --retries=0
npm run typecheck
```

Full first/repeat CPU runs used the same existing `harness.run` in one process with fresh labels `rotation-cpu-first-process` and `rotation-cpu-same-process-repeat`; no inference restart. Original app reloads stopped only the owned app supervisor and preserved resident GPU serving/histories. Detailed actual integration logs: `runtime/clearledger/integration-cl10.log` and `integration-cl10-border-final.log`.

[Consolidated hackathon readiness](clearledger_hackathon_readiness.md) separates working local behavior, current failures, external input gates and UI work deferred by the latest instruction. This checkpoint makes no additional T01–T42, production or legal-compliance claim.

Final supplemental browser check loads retained Admin records (not just its loading screen), confirms catalog 200/finance access 403, and captures laptop/phone views without writes. Final combined source/Admin file: **four passed / 2.7 s / exit 0**, no retries/skips; separate role-login one/1.0 s remains. A test-only locator syntax typo initially returned exit 1 with no tests collected; it is not counted as a passing run and was corrected before this final execution. Final bounded source scan counts **402 text files**, cached secret scan zero findings/one redacted probe, finance and isolated CPU pip checks pass. Health command confirms READY/AVAILABLE; current readback is RTX 2000 Ada/550.120/16,380 MiB and finance Python 3.13.11.

Post-self-review source safety: disagreements are now retained even when the second measured OCR read has poorer structural coverage and the first read is kept. One new IPC regression demonstrates the conflicting 24.00-versus-94.00 cell stays in the source sidecar without adopting 94.00; the existing worker test verifies such sidecars produce AMBIGUOUS/canonical null. Final scoped suite **210 passed / 4.42 s / exit 0** (27 new geometry cases); earlier 209-case runs remain historical. No source/finance control is relaxed.

Final-code live p02 after the conservative conflict guard: **7/7 checked headers, 5/5 row facts, one actual VLM call, 20.359 s upload/durable result** (upload 1.232 s), original hash/provenance and NEEDS_INPUT/no finance decision/tax-basis null preserved. All nine production hashes match this actual measurement. Earlier 19.300 s boundary result remains separately recorded, not replaced or averaged into a speed claim. Core work stops; no further tuning, UI redesign or publication.

Final-code source/loaded-Admin browser repeat: **four passed / 2.8 s / exit 0**, one worker/no retries/skips; final p02 source record selected. Earlier 2.7 s run is retained as a separate observation.
