# Kivo reliability and measured extraction repair

2026-10-05, REL-01–REL-03, Phase-6 support under the continued delegated hardening approval. Existing ClearLedger/AP finance engine and accepted Kivo presentation are preserved. This is a functioning local repair with measured evidence; it is not a production pilot or a new phase completion.

Read the working specification, progress/assumptions/dictionary/coverage, implementation/exit reviews, relevant local thread memory and replay/source/runtime ADRs before implementation. Verified checkout `/data/vansh/microsoft_inovate`, starting clean main `4883e1b`. No second recent checkout writer was found; final process/index inspection found no concurrent Codex checkout process or index lock. The separate portfolio checkout was untouched. No checkout `.agents` folder exists. Existing UI-01 design skills/results are retained without another redesign. The [bounded responsibility](kivo_reliability_plan.md) was recorded first.

## Implemented behavior

An unchanged source confirmation, policy draft/activation or budget adjustment now reuses an actor/tenant/entity/endpoint/input-bound idempotency key after an interrupted reply. The browser coalesces identical in-flight calls and stores only SHA256 fingerprints/random UUID keys in tab storage. Server authentication, authorization, version checks and exact-body replay remain authoritative. No automatic POST retry is introduced. Budget keys retire only after acknowledged success, permitting a deliberate subsequent adjustment; source/policy keys retain logical-action replay. Restricted/cleared storage loses replay across reload, although page-memory replay remains.

Late canonical-template, policy validation and history replies cannot replace a newly selected scope or changed values. Source/case/budget components reset on record navigation. Budget fields clear after success and cannot change while submitting. A new multi-line source draft omits development-template row IDs so the existing server assigns distinct UUIDs; revisions of an existing case preserve its historical row IDs. Actual source-confirmation errors remain visible and actionable. The policy success notice survives the refreshed version instead of disappearing during its reset effect.

Upload limits come from actual intake capabilities. An oversize batch is rejected before creating upload sessions. Exact repeated rendered page hashes produce a correction instruction; original pages and their distinct rows remain available. There is no silent row/page/invoice deduplication, no financial identity from hashes and no automatic duplicate resolution.

An actual source commit returned DATABASE_UNAVAILABLE/503 at about 10.5 seconds during snapshot writes/worker lock waits. The measured scope then contained 1,744 reference versions, 918 snapshots and 867,059 memberships (375,193,600 table bytes). Immutable membership now uses bounded 500-row SQLAlchemy inserts. Selection, sorting, manifest digest, UUIDs, snapshot reuse, FK/unique/RLS constraints and atomic rollback are unchanged; no migration/index/dependency/finance-engine change. In a fresh migrated schema, three 1,700/1,699/1,698-member transactions measured:

| Run | Transaction milliseconds | Median milliseconds |
|---|---|---:|
| Before | 194.264, 334.246, 277.610 | 277.610 |
| Candidate | 190.074, 174.841, 188.233 | 188.233 |
| Final stressed run | 186.406, 1282.996, 176.593 | 186.406 |

The candidate median is about 32% lower, based on three shared-local observations. The 1.283-second outlier and loaded-host lock timeouts remain limits; batching does not establish sustained throughput or eliminate overload failures.

## Actual extraction before and after

Six new invented CC0 sources/three families were frozen before measurement. Two reserved families/four native/scanned variants were opened after the reliability changes. That opening spent the split. Literal truth is used only by the scorer after output, never prompts, defaults, corrections or sample-specific routing. [Frozen sources/truth](../data/kivo_reliability/manifest.json) and [sanitized measurements with hashes](../data/kivo_reliability/results.json) are trackable; full runtime outputs are ignored.

| Source | Before end-to-end seconds | After UI/replay seconds, before geometry repair | Header matches | Row matches |
|---|---:|---:|---:|---:|
| h01 native offset panels | 4.990 | 3.984 | 7/7 | 6/6 |
| h02 difficult blurred/slightly skewed scan | 49.941 | 53.097 | 7/7 | 0/6 |
| h03 native two-page continuation | 5.190 | 3.079 | 7/7 | 8/8 |
| h04 raster two-page continuation | 9.506 | 8.779 | 7/7 | 8/8 |

Both aggregate observations were 28/28 header and 22/28 row checks. These runs showed no extraction improvement from UI/replay changes. All required canonical abstentions passed and every source was NEEDS_INPUT with no finance decision. Development d01 changed 3.364→18.568 seconds and copied d02 3.087→14.493 seconds under simultaneous heavy test load. They are not speed improvements; d02 still has four retained source rows for two printed rows plus an explicit copied-page notice and LINE_UNRESOLVED findings. Incomplete financial fields prevent complete arithmetic validation.

Inspection of actual h02 OCR showed the six printed row values had been read, but axis-aligned heading rectangles split Description from Qty/Unit price/Amount. The old route made three real resident Qwen/TypeLLM calls: inventory about 5.97 seconds and two line calls totaling about 36.23 seconds. Equal, unassigned model candidates were correctly quarantined as AMBIGUOUS/canonical null, so their row score was 0/6.

[ADR-0020](adr/0020-measured-fragmented-table-headings.md) accepts a generic measured heading association: only two adjacent groups consisting entirely of unique recognized column labels may establish one complete heading, with ordered nonoverlapping columns, common measured vertical overlap and a bounded linear baseline. Generic label/value/item grouping is unchanged. Duplicate labels, unrelated words, separate rows, crossing columns and nonlinear geometry abstain. No field box/image changes or supplied row values occur. Metadata is printed-layout-v7/native adapter9; historical runs retain prior versions.

| Spent h02 repair observation | End-to-end seconds | Headers | Rows | Actual VLM calls |
|---|---:|---:|---:|---:|
| Before repair comparison | 53.097 | 7/7 | 0/6 | 3 |
| First after CPU-worker restart | 8.631 | 7/7 | 6/6 | 0 |
| Same-worker repeat | 8.456 | 7/7 | 6/6 | 0 |

Both repairs retain two distinct measured rows and unchanged original SHA256. All ten required abstentions remain: bank account, PO, tax basis, discount, shipping, other charges, row-two quantity/price, ambiguous date and currency. Blank cells are MISSING/raw null/canonical null; the visible exact questions identify line two and page one. No quantity/price is calculated, `$` becomes no guessed currency, `04/05/2026` becomes no guessed date and printed zero tax supplies no tax treatment. Source confirmation actually returns 422 CANONICAL_SOURCE_UNRESOLVED; no finance case or approval is manufactured.

End-to-end timing includes actual loopback upload, durable scheduling/stages/API and 0.25-second polling, excluding browser/human time. Each entry is one observation on a shared host, not a latency distribution. First-after-restart and same-worker repeat are distinguished; they are **not cold GPU weights measurements**. OCR reports measured initialization 0.271 seconds before and 0.263 seconds after, with actual OCR read times 2.129/2.181/2.014 seconds respectively. Resident inference was kept available. Device-wide observed GPU use was 14,023/16,380 MiB, not request-attributed VRAM. No cold serving startup, VRAM delta or universal speed claim follows. This known-failure repair is development evidence, not another held-out accuracy result; no claim combines old h01/h03/h04 runs into a new final-geometry corpus run.

The pinned model/runtime remained Qwen2.5-VL-3B-Instruct revision `66285546d2b821cf421d4f5eb2576359d3770cd3`, BF16, RTX 2000 Ada/driver 550.120. Finance Python 3.13.11 and isolated Python 3.12 serving/client/CPU environments were preserved. No model download/replacement, package upgrade, GPU/host/system/Docker/credential/firewall change, external inference, paid service, push or public/LAN/cloud deployment.

## Executed verification

Commands run from the repository unless stated. Node commands used the existing private Node24.21.0 PATH and `PLAYWRIGHT_BROWSERS_PATH=runtime/playwright`. Opt-in browser flags were AP_RUN_FINAL_ACCEPTANCE=1, AP_RUN_ROTATION_BROWSER=1 and AP_RUN_RELIABILITY_BROWSER=1; one worker, zero retries.

| Exact command | Result |
|---|---|
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests --ignore=apps/api/tests/integration -q --tb=short` | Final 836 passed, 5.50s, exit0; existing Starlette/httpx deprecation warning |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_release_phase6.py apps/api/tests/integration/test_document_finance.py apps/api/tests/integration/test_clearledger_worker_recovery.py -q --tb=short` | Before batch support: 17 passed, 311.58s, exit0 |
| Same migrated files plus `test_references_phase3.py test_snapshot_batch.py` | After batch support: 21 passed, 1 failed, 791.29s, exit1; GRN eight-finalization lock timeout under overlapping browser/migration load |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_release_phase6.py -k 'eight_concurrent and GRN' -q --tb=short` | Unchanged exact failed capacity check: 1 passed, 8 deselected, 22.12s, exit0 after overlap ended |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_document_pipeline.py apps/api/tests/integration/test_document_finance.py -k 'real_pdf_stages or generic_revision_cannot or uncertainty_source_confirmation' -q --tb=short` | Final after source fix: 3 passed, 14 deselected, 96.00s, exit0 |
| `AP_SNAPSHOT_MEASUREMENT_LABEL=before` / `after` with `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_snapshot_batch.py -q --tb=short` | Fresh migrated test: 1 passed/14.86s then 1 passed/14.35s, both exit0; exact membership/replay/UUID/RLS/FK/rollback/empty assertions |
| `npm --prefix apps/web run test:e2e -- reliability.spec.ts reliability-source.spec.ts kivo.spec.ts final-acceptance.spec.ts rotation-source.spec.ts release.spec.ts workflow.spec.ts documents.spec.ts workspace.spec.ts` | Final 44 passed, 278.442s, exit0; no skips/retries/flaky cases |
| `npm --prefix apps/web run test:e2e -- tests/reliability-source.spec.ts tests/reliability.spec.ts tests/final-acceptance.spec.ts --grep 'actual repaired scan\|new multi-line\|retained future'` | Final focused source/row-ID/policy checks: 3 passed,12.5s,exit0 |
| `npm --prefix apps/web run build`; `npm --prefix apps/web run typecheck` | Final production build and separate final TypeScript check exit0 |
| `.venv/bin/python scripts/release/judge_verify.py` | Eight existing computed scenarios/current eligibility/28 controls/citations and original correction HOLD pass, exit0 |
| `.venv/bin/python scripts/release/source_security.py`; cached `.venv/bin/python scripts/release/secret_scan.py` | No forbidden runtime paths/configured credential patterns; Gitleaks 8.30.1 zero source findings/one redacted synthetic detection, exit0 |
| `scripts/demo-health.sh` | App/API/web/worker READY, approved resident model AVAILABLE, exit0 |

Measurements used `.venv/bin/python scripts/benchmark/kivo_reliability.py --freeze`, then `--label baseline-development/final-development --split development`, `--label baseline-reserved/final-reserved --split reserved`, and `--label repaired-spent-scan-first/repaired-spent-scan-warm --split reserved --case h02` (each label a separate executed command). Each completed exit0; scores/failures above are separate from command completion. Timing files were never overwritten.

Intermediate failures remain in ignored logs: initial three browser failures included an ambiguous alert selector; the corrected actual lost-source-reply baseline failed with different keys/case IDs. Affected runs were 4pass/3fail then 5pass/2fail, exposing a mistaken copied-page arithmetic expectation, isolated import provenance error, literal Decimal precision assertion and real 503. After correcting assertions/setup and product behavior, the affected seven passed/49.7s. An overloaded broader browser run was 27pass/15fail/299.5s with actual 503/upload/commit waits and the disappearing activation notice. The next 42-test run was 41pass/1fail/268.1s: a prior failed reversible demonstration had left the fictional hotel at 8,000. Its actual successful policy flow restored 9,000. No reset or erased history occurred. The later focused source test first failed a hidden-JSON locator, then exposed the actual duplicated template row IDs; the final fix now yields the intended source-unresolved422 and successful distinct-row201. No capacity/control assertion or database lock timeout was loosened, and no failing run was relabeled clean. There is no combined clean 22-test migrated rerun claim.

Actual rebuilt browser QA covers Finance/Admin laptop and390px phone layouts, source boxes/questions, mobile overflow, keyboard focus/reduced motion, real upload/revision/history/report/audit, corrupt quarantine, visible loading/error/restored retry/empty state, lost committed replies, policy races/history, one budget event, role403/CSRF, ownership/actions/recovery and enterprise mapping without development templates. Inspected current ready-result laptop/phone, scoped policy laptop/phone and repaired-scan source overlay screenshots. Source fact tables can still be long; unknown currency makes related monetary canonical fields unresolved despite readable raw literals.

Final fictional hotel readback is **version 52, INR9,000 per eligible night from 2026-11-01**, with prior version 48 and8,000/history/actor/reason retained. This records authorized reversible local test activations, not a business policy or historical decision overwrite. Prior UI-01 version 48 screenshots/claims remain historical. Eight retained reports/decisions remain unchanged. Nine original pack/ZIP files and156 prior tracked data/spec/ADR/exit files were byte-compared with starting HEAD and preserved; all six new frozen hashes match.

## Remaining limits and next responsibility

Local repaired journeys are verified. Loaded-host DATABASE_UNAVAILABLE and 5s lock-timeout behavior remains a capacity limit, even with smaller snapshot write cost and passing isolated capacity rerun; no sustained-load or production availability claim. Fresh diverse authorized adjudicated vendor/layout families are still needed for independent acceptance (40–60 target), with cold/warm distributions and attributable VRAM on suitable authorized infrastructure. Reserved families here cannot be reused as fresh evidence. Difficult Arabic/perspective/mixed-page/currency/tax cases from earlier reviews remain explicit limitations.

Business-approved policies/references, real identity, required malware-scanner validation, deployment/residency/network/spend inputs and a pilot are unsupplied. Local role login is visibly fictional development access. Missing policies/source/mandatory controls still hold. Supervised adjudicated labels remain absent; rules/robust anomaly support is the honest result, no classifier/SHAP/model score fabricated. Original T01–T42 disposition and historical exits are unchanged. Next bounded responsibility: obtain those authorized independent/business inputs and validate actual loaded-host/source failure behavior. No publication or infrastructure action is implied by this closure.
