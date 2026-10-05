# REL-05 local panel readiness verification

2026-10-05, Phase-6 support under the explicit continued panel-readiness delegation. Starting local main `d1ac0eb`, with `7c2edb2` extraction/reliability changes retained. [Plan](kivo_panel_readiness_plan.md) recorded before implementation. Inspected actual checkout/processes, project/source authority, required registers, historical exits/evidence and available skills; no competing writer found. No finance-engine rebuild, rule/database/migration change, dependency/model/driver change, identity/credential setup, host/security change, public/LAN/phone access, cloud spend, push, portfolio work or subagent.

## Target and submission inventory

User-provided Day1 is **Wednesday7October2026**, top25 advance8October; exact reporting/submission time remains pending. Target **6October evening IST**, before7October morning. Baseline5October14:25UTC/19:55IST left22–24hours to that target. The5–7hour scoped work estimate covered local rehearsal/recovery/handoff, not another application build. Dates are supplied context, not verified official event rules.

Working specification §25 requires complete vendor clearance with prerequisites; paid duplicate; partial receipt/prior capacity; clean/violating employee expenses; recompressed/shared receipt distinction; retained correction and current-version approvals. Original team work plan §9–10 adds code/contracts, fixtures/tests, evidence/dependencies/assumptions, short working module demos and combined acceptance. Existing8computed scenarios/28controls retain the local finance evidence. Historical exit reviews preserve external deferrals.

Application, setup/migrations, API/rule/policy catalogs, synthetic sources, release/security/recovery artifacts, measured evidence, handoff/runbooks and `output/pdf/Kivo-quick-start.pdf` exist. No official deck/video requirement, submission portal, upload deadline, scoring rubric or presentation duration was found in the supplied pack/repository. No pitch deck or narrated demo video is present. Parent confirmation/prioritization is needed if those are expected. The new [3–5minute operator walkthrough](runbooks/kivo-panel-demo.md) is a suggested sequence, not an event requirement.

## Reproduced findings and fixes

| Finding | Bounded change/evidence |
|---|---|
| Full restart stopped inference | Explicit `start-cpu`, `stop-cpu`, `restart-cpu` reuse owned PID/UID/argv/start-time validation, database role/migration preflight and current configuration. No identity seeding/inference control. Existing full lifecycle preserved. Affected17checks pass. Actual first CPU restart1.69s preserved8current/retained scenarios and all inference supervisor/child identities; build recovery1.68s also preserved inference. |
| Multiple Hotel entries had indistinguishable labels | Existing business `policy_code` distinguishes policies without database UUIDs. Fixtures select established `DEMO-EXP-HOTEL` by identity, not first Hotel. Isolated rehearsal/operator policies have distinct fictional location/code/version. |
| Submission date required JSON | Business form exposes explicit **Submission date**, including source review. Operator context is separate from extracted invoice date; no default invented or date rule weakened. Original frozen template26September preceded the new2October invoice. Reviewer supplies actual submission date; final rehearsal verifies date PASS while missing approvals still hold. |
| Legacy finance UI tests assumed open controls | Existing disclosure helpers preserve original business assertions/actions. Controls stay collapsed by default. |

New opt-in rehearsal covers first-time Welcome/Finance entry; actual unfamiliar upload/progress; ambiguous original date/page-two human correction and retained observations; explicit business submission date; honest HOLD/approval failure; role denials/history reload; isolated fictional INR8000→9000 policy/version/future date/reason/audit; current Ready/Hold/Review reports; read503 display/reload. Browser read503 is an explicitly injected response, not a real database failure. Actual timeout/rollback/replay is separately verified by REL-04 migrated tests. No finance result/model result/approval is injected.

`panel_prepare.py` uses existing authorized local reference APIs/identity to prepare one isolated fictional policy, with a private replay journal. Repeat preserves its version and never resets a changed allowance. It does not seed credentials, run inference or alter established records.

## Frozen sources and actual model

[Manifest](../data/kivo_panel/manifest.json), five original CC0 fictional PDFs and [sanitized evidence](../data/kivo_panel/results.json): one development/presentation source, four initially reserved native/scanned variants in two newly drawn layouts. Truth/source hashes frozen before first intake; truth used only in post-output scoring. Correlated variants are now **spent**. No production extraction tuning followed output; extraction code unchanged in REL-05.

| Source | Path | Seconds | Headers | Row/page values | Required nulls | Outcome |
|---|---|---:|---:|---:|---:|---|
| h01 | Native | 3.150 | 7/7 | 6/6 | 10/10 | NEEDS_INPUT |
| h02 | CPU OCR | 6.591 | 7/7 | 6/6 | 10/10 | NEEDS_INPUT |
| h03 | Native/two pages | 3.101 | 7/7 | 8/8 | 6/6 | NEEDS_INPUT |
| h04 | CPU OCR/two pages | 8.195 | 7/7 | 8/8 | 6/6 | NEEDS_INPUT |

Total28/28checked headers,28/28row/page values,32/32required abstentions, zero VLM calls and no finance decision. Missing bank/PO/tax basis/extras/quantity/price and ambiguous date/currency remain unresolved. Printed malicious payment note remains data. Small invented literal checks do not establish broad accounting completeness/customer accuracy or throughput.

**Why every reserved source needs input:** these scores compare only the seven printed headers and selected table cells. In h01/h02, `05/06/2026` is ambiguous and `$` does not establish ISO currency. Currency ambiguity therefore also blocks normalization of correctly read amounts. The second row genuinely omits quantity/unit price. In h03/h04, ISO date/INR and printed row values are read, but document discount/shipping/other charges and tax basis are absent. All four omit explicit per-line discount, tax rate/tax, net/gross interpretation and UOM; a generic Amount column and document Tax0.00 cannot establish that missing tax treatment. The source segmentation state remains UNCONFIRMED, with no inferred bundle clearance. These are source/normalization sufficiency gaps **before finance screening**. The benchmark did not confirm/commit the drafts, select independent business references or request approvals; PO/vendor/budget/approval controls were not run and are not the reason for the observed NEEDS_INPUT. Missing bank/PO observations separately remain missing; later reference matching must use authorized company records.

A successfully read literal is not a complete normalized invoice, and a complete normalized/source-confirmed invoice is not **Ready for processing**. That label requires the current finance evaluation to pass mandatory controls and eligibility. The separate development d01 source demonstrates the distinction: a page-two date correction and explicit submission context resolve date validation, then the actual finance engine returns HOLD for approval and duplicate-review requirements. No source inference is used to manufacture finance clearance.

Presentation d01 first intake3.138s/native: ambiguous `10/02/2026` retained, page2 supports2October correction. First rehearsal honestly held, including the old submission-date conflict; explicit form now permits the business confirmation. Repeated sources can create real duplicate candidates; HOLD is the presentation boundary, not a failure to force clearance.

Separate existing **spent** rotation r02: actual resident `ENTERPRISE_VLM`/Qwen/TypeLLM adapter2,14.799s,7/7headers,12/12row/page values,6/6required abstentions, NEEDS_INPUT/no finance decision. Metadata retains pinned model/runtime provenance. CPU worker freshly restarted; GPU already resident.31read-only approximately0.5s samples: owned inference tree12948MiB baseline/13766MiB maximum; no other compute process reported by that query. Resident/allocator footprint, **not** attributable incremental request peak. Cold GPU load not repeated. Earlier spent r02=13.032s stays separate; REL-05 makes no speed-improvement claim. REL-03 difficult spent scan49.941–53.097→8.631/8.456s and3→0VLM calls remains development evidence, not new independent accuracy.

## Executed verification

Existing finance `.venv`, private Node24.21.0/Playwright. One browser/migrated runner at a time. Detached final runner/private exit record survives intermittent tool transport loss; absence/ownership checked before starting another runner. Logs in ignored `runtime/kivo-panel`; no credentials/customer sources exported.

| Command/check | Result |
|---|---|
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/test_demo_lifecycle.py -q --tb=short` |17passed/0.05s/exit0 |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests --ignore=apps/api/tests/integration -q --tb=short` |840passed/5.33s/exit0, existing warning |
| `npm --prefix apps/web run build` (pinned Node PATH) |Both builds exit0; final includes submission date |
| `.venv/bin/python scripts/benchmark/kivo_panel.py --freeze` then `--label panel-first-reserved --split reserved` |Freeze before intake;4measurements complete/exit0; counts/limits above |
| `.venv/bin/python scripts/benchmark/clearledger_public.py --label panel-vlm-existing-r02 --corpus clearledger_rotation --case r02` |Actual current resident Qwen/TypeLLM/exit0,14.799s |
| `.venv/bin/python scripts/demo.py restart-cpu`, before/after model identities and judge checks |Exit0;8scenarios/current eligibility/retained source and original correction HOLD preserved |
| `.venv/bin/python scripts/release/panel_prepare.py` twice |Both exit0, same isolated version1/INR8000; repeat no activation/reset |
| Browser `panel-readiness.spec.ts` |First2pass/1fail/16.8s/exit1: cross-role catalog comparison error. Corrected same-role comparison3pass/14.8s/exit0. New submission-date assertions included in final aggregate. |
| Unscoped `npm --prefix apps/web run test:e2e` |Transport interrupted; no final exit/count.18reported outcomes:10pass/3fail/5opt-in skips.2stale undisclosed selectors and1first-Hotel identity selection corrected. Not a passing aggregate. Logs retained; runner absence checked. |
| Final scoped browser aggregate |55passed/400.314s/exit0; zero failures/skips/retries/flaky cases. Detached runner wall400.754s. |
| Final clean migrated aggregate |25passed/455.79s/exit0,1existing deprecation warning; detached wall457.402s. No overlap with browser. |
| Typecheck/syntax/source/secret/preservation/final visuals |Scoped tsc exit0;4Python modules compile. Source442texts/no forbidden artifacts/credential patterns; cached Gitleaks zero/one redacted detection probe/exit0.134backend/inference/source-pack/spec/ADR/exit files byte-preserved vsd1ac0eb;5new source hashes verified. Actual final new-HOLD laptop/policy phone/paid-HOLD phone inspected. Final judge8current/retained scenarios and health READY/AVAILABLE exit0; final post-document source442texts/zero findings and cached Gitleaks zero/one redacted detection probe, exit0; whitespace clean. |

Final browser command: `npm --prefix apps/web run test:e2e -- reliability.spec.ts reliability-source.spec.ts kivo.spec.ts final-acceptance.spec.ts rotation-source.spec.ts release.spec.ts workflow.spec.ts documents.spec.ts workspace.spec.ts panel-readiness.spec.ts finance.spec.ts`. Flags `AP_RUN_FINAL_ACCEPTANCE=1 AP_RUN_ROTATION_BROWSER=1 AP_RUN_RELIABILITY_BROWSER=1 AP_RUN_PANEL_REHEARSAL=1`, one worker/zero retries. Policy and financial assertions retained. Actual source-page2/new-case/Ready/Review/paid-Hold/policy-version/error screenshots inspected at laptop1366×900 and phone390×844; page overflow checked, keyboard/reduced motion covered. Final new-HOLD laptop, isolated-policy phone and paid-HOLD phone screenshots inspected after the passing aggregate.

## Limits

Applicable local panel gates passed; final documentation, staging and local commit complete the checkpoint. This is a local presentation checkpoint. No production readiness/legal compliance/customer accuracy/universal speed/capacity/supervised model claim. Real company policy/reference/identity, working malware scanner, authorized adjudicated independent invoices and pilot acceptance absent. Cold model startup/exclusive request VRAM/sustained large catalog load unverified. REL-04 prolonged-contended failure bookkeeping/lease expiry limits remain. Event reporting/deck/video/submission inputs require parent confirmation, independently of technical completion. No publication/infrastructure action implied.

## Parent-requested pause checkpoint

2026-10-05: Parent explicitly requested a safe-boundary checkpoint now. Edits paused; work uncommitted/preserved. Final browser55pass/400.314s/exit0 and backend840pass/5.33s/exit0. Detached migrated25-test runner PID1488095 remains active; do not abandon/duplicate it. Read `runtime/kivo-panel/migrated-final-exit.json` and log before next action. Short execution remains available; prior transport interruption affected the unscoped run, corrected detached final browser completed. Final docs/register counts/progress/health/judge/security/staged review/local commit remain. No push.

## Resumed local gate completion

The parent authorized resumption after the safe pause. Existing detached runner exit0 confirmed,25passed/455.79s; no test duplicated or interrupted. Final judge8current/retained scenarios/28controls and required-VLM health READY/AVAILABLE exit0. Full migrated command:

```bash
AP_CAPACITY_MEASUREMENT_LABEL=panel-final AP_SNAPSHOT_MEASUREMENT_LABEL=panel-final PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_release_phase6.py apps/api/tests/integration/test_document_finance.py apps/api/tests/integration/test_clearledger_worker_recovery.py apps/api/tests/integration/test_references_phase3.py apps/api/tests/integration/test_snapshot_batch.py apps/api/tests/integration/test_kivo_capacity_recovery.py -q --tb=short
```

Scoped typecheck: fromapps/web, existing private Node executes`node_modules/typescript/bin/tsc --noEmit`,exit0. The initial root-cwd npm-exec check printed TypeScript help; it was not counted as successful. Python compile checks on demo lifecycle, panel benchmark/preparation and lifecycle tests exit0. Parent's event-format/reporting/deck/video questions remain pending and do not block the local gate. No scope expansion or external publication.

Final post-document commands `scripts/release/source_security.py` and `scripts/release/secret_scan.py`:442texts/no forbidden runtime artifacts or configured credential patterns, zero Gitleaks source findings/one redacted synthetic positive probe, exit0. `git diff --check` exit0. Original pack/ZIP/working specification, backend/finance/inference/schema/rules/ADRs/historical exits134files byte-preserved againstd1ac0eb;5new source hashes verified. Only scoped CPU lifecycle, two business-form presentation changes, test fixtures/rehearsal, fictional corpus/preparation and handoff records are included. Local commit follows staged review; no publication.
