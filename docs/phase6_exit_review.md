# Phase-6 local delivery exit review

Status: **PHASE 6 COMPLETE LOCALLY — CLOUD PROVISIONING DEFERRED EXTERNAL INPUT.** All supported local gates passed. The approved scope is P6-01–P6-04 continuously with an explicit external-input fallback. No Azure/GPU provisioning, classifier/SHAP or payment execution occurred. This is a synthetic local development release, not production readiness or an actual enterprise pilot.

## Task disposition

| Task | Local deliverable | External gate |
|---|---|---|
| P6-01 | Single private CPU Bicep architecture, Entra/server memberships, managed-identity Blob adapter, scoped Key Vault/registry identities, typed business administration and safe telemetry. | Actual subscription/region/spend/identity/residency/network/egress, hosted authentication/Blob and monitoring verification. |
| P6-02 | Pinned-action test/build/scan/image-checksum CI and protected manual release; explicit migrations; reviewed commit/parameter hash and immutable image requirements. Both Bicep templates compile. | Hosted CI/container build/registry publication, staging smoke and image rollback. Local Docker authorization remains blocked. |
| P6-03 | Actual authorization/tenant/RLS/upload/audit/retry/concurrency tests, dependency/secret scans, local CPU/history/workflow benchmarks and a real disposable database/object restore. | Provisioned-cloud restore/network/monitoring/load and real VLM measurements. |
| P6-04 | Finance upload/result/correction/evidence/report workflow, separate Admin forms/versioning, validated synthetic demonstrations, laptop/mobile views and complete runbooks/coverage matrix. | Institutional data/pilot acceptance; representative classifier labels. |

## Acceptance AC01–AC20

Statuses apply to verified supported local behavior; external/data gates are not silently waived for a production pilot.

| Criterion | Disposition | Evidence / limitation |
|---|---|---|
| AC01 | SATISFIED | Both branches persist through document/structured intake, evaluation, evidence/report and review; actual backend/browser flows. |
| AC02 | SATISFIED | 28 deterministic controls, explicit applicability/unknowns, matching/duplicate/policy/budget/authority. |
| AC03 | SATISFIED | Rule/version/snapshot and actual source, record/cell/page evidence; missing source/box is explicit. |
| AC04 | SATISFIED | Applicable controls, approvals and capacity gate PASS; no payments. Material/stale changes invalidate current eligibility. |
| AC05 | SATISFIED | Version/ownership guarded queue, typed correction/resolution and deterministic next actions. |
| AC06 | SATISFIED | Retry/business/fuzzy/pHash candidates, authorized DISTINCT/duplicate/shared dispositions and cumulative allocation. |
| AC07 | SATISFIED | Originals, observations, normalization, canonical versions, corrections and retained/superseded evaluations. |
| AC08 | SATISFIED | PASS/REVIEW/HOLD screening; business descriptions and separate human decline/state. |
| AC09 | SATISFIED | 39 complete, T30 partial, T31/T34 data-deferred; approved anomaly alternative never permits unsafe PASS. Not 42/42 complete. |
| AC10 | SATISFIED | Local tenant/entity RLS, scope/role/evidence/actor/approval/conflict tests. Real hosted identity/network still external. |
| AC11 | SATISFIED | Eight-way budget/GRN/duplicate/shared-receipt finalization, retry allocation checks, prior cancellation/compensation and stale-worker tests. |
| AC12 | SATISFIED | Audit-failure rollback and pinned deterministic replay; retained manifests/audit verified in restore. |
| AC13 | SATISFIED | Critical uncertainty, missing reference/provider/model/storage and required outages stay incomplete/REVIEW/HOLD, never zero-risk success. |
| AC14 | SATISFIED | Synthetic finance sources and ignored private originals/artifacts; scoped access, source/secret scans and content-free telemetry. Live private Blob smoke remains external. |
| AC15 | SATISFIED | Recorded TypeLLM compatibility/contract tests and conservative schema/state/money boundary; factual VLM quality/runtime is not claimed. |
| AC16 | SATISFIED | Visibly rules/statistical-anomaly-only with model card, synthetic limitations and supervised gate; no held-out classifier claim. |
| AC17 | DEFERRED_DATA | No justified supported tree classifier/raw margin; SHAP/additivity not fabricated. |
| AC18 | SATISFIED | Validated setup/migrations/demo/test commands, recovery/failure/deployment runbooks and limitations. |
| AC19 | SATISFIED | Actual machine/data/sample/timing tables separate targets; unmeasured 10-way/1k/cloud/VLM scopes explicitly remain. No enterprise SLA claim. |
| AC20 | DEFERRED_EXTERNAL | No deployed pilot. Real authorization/private network, cloud restore/monitoring/image rollback are mandatory future gates. |

## T01–T42

Final disposition remains **39 complete, one partial (T30), two data-deferred (T31/T34)**. T30 verifies low actual statistical risk cannot clear mandatory HOLD; its classifier portion remains unsupported. Statistical PASS→REVIEW is tested but is not a classifier-specific T31 result. No static SHAP numbers close T34. T29/T33/T39 preserve unknown/degraded/unsupported-document behavior. Detailed evidence remains in [coverage](test_coverage.md); historical phase reviews are unmodified.

## Verification record

All commands below actually ran. Each successful application/check command returned exit 0; the intentionally absent deployment approval returned exit 1. Separate suites are not summed into a fabricated single run.

| Command/check | Actual result |
|---|---|
| `.venv/bin/pytest -q apps/api/tests` | **777 passed**, zero failed/skipped; one upstream Starlette/httpx deprecation; 2550.42 s. Collected before the final two release cases were added. |
| `.venv/bin/pytest -q apps/api/tests/test_release_boundaries.py apps/api/tests/integration/test_release_phase6.py` on final code | **21 passed** (12 pure, nine PostgreSQL), zero failed/skipped; same warning; 152.39 s. Includes both added cases and all affected enterprise guards. |
| `.venv/bin/pytest --collect-only -q apps/api/tests` | **779 collected**, 0.56 s. All current cases are covered by the full/final focused runs; collection alone is not a passing test. |
| `PLAYWRIGHT_BROWSERS_PATH="$PWD/runtime/playwright" npm --prefix apps/web run test:e2e` with project Node PATH | **36 passed**, 2.7 min, one worker/no retries, real API/worker. Includes retained finance/intelligence/workflow and four new release flows plus responsive loaded views. |
| `npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build` with project Node PATH | Strict TypeScript and normal production build pass. Separately `AP_BUILD_STANDALONE=1` build and actual enterprise-mode Node server `/health` returned 200/alive; no hosted authentication or container image claim. |
| `.venv/bin/alembic -c apps/api/alembic.ini check` | No new upgrade operations. Integration tests migrate fresh owned PostgreSQL schemas through all eight revisions; existing head is `0008_intelligence_audit`, 61 forced-RLS business tables. No Phase-6 migration. |
| `.venv/bin/python scripts/release/contracts.py`; generated client inspection | Public OpenAPI exact match; generated TypeScript retained. |
| `runtime/release-tools/bin/ruff check apps/api/app --select E9,F63,F7,F82`; `runtime/release-tools/bin/mypy apps/api/app/domain --ignore-missing-imports`; compileall | All pass; mypy five domain files. Fatal-error lint is not a claim of full formatting/style enforcement. |
| `.venv/bin/pip check`; `runtime/release-tools/bin/pip-audit -r apps/api/requirements.lock --no-deps --disable-pip`; `npm --prefix apps/web audit --audit-level=moderate` | Dependency integrity passes; no known Python vulnerabilities; npm zero in every severity category. pip-audit recommends full requirement hashes, a nonfatal reproducibility warning. No container/OS scan was executed. |
| `.venv/bin/python scripts/release/source_security.py`; `.venv/bin/python scripts/release/secret_scan.py` | 296 source text files pass bounded patterns/path checks; Gitleaks 8.30.1 zero findings plus one successfully detected/redacted synthetic probe. Final documentation additions are rescanned before commit. |
| `sha256sum -c` for original, synthetic, extraction and document manifests; spec `cmp` | All **9 / 23 / 11 / 15** checks pass; working specification byte-identical. Historical Phase-0–5 reviews and deterministic rule/domain modules are unchanged. |
| Bicep `build` for `foundation.bicep` and `release.bicep` | 0.47.16 compiles both without warnings. No cloud resource was provisioned. |
| `runtime/release-tools/bin/python scripts/release/check_artifacts.py` | Missing/invalid approval and target/hash mismatches rejected before mutation; reviewed action pins, both YAML workflows and 11 shell blocks validated. No GitHub workflow execution claim. |
| `.venv/bin/python scripts/release/deployment_gate.py runtime/release/absent-approval.json` | Expected exit 1, DEFERRED_EXTERNAL; no provisioning. |
| `.venv/bin/python scripts/release/restore_drill.py` | Real disposable local database/object restore verified; details below. |
| `.venv/bin/python scripts/release/persistence.py record` then owned supervisor restart and `verify` | Actual document-linked transaction/version/evaluation/report digest unchanged; verified again after final normal build/start. |
| Finance/workflow/intelligence/document/release benchmark scripts | All exit 0; exact measured scope/sample tables in [performance](performance_phase6.md), no VLM/classifier/production measurements. |

Final release PostgreSQL coverage verifies future hotel allowance versions/old snapshots, policy/master permission boundaries, revoked authorization before idempotent responses, audit rollback, narrow finance/health access, safe telemetry, actual enabled enterprise submitter membership and eight-way budget/GRN/duplicate/shared-receipt admission. Disabling the on-behalf submitter membership produces EMP-001 FAIL/HOLD in a new evaluation while preserving its old report. Only the external storage contract is mocked in that test; PostgreSQL/RLS/admission/rules/audit are real.

Early release failures were repaired: future-activation notice refresh, new role filtering in the existing operations browser test, receipt stress authorization, and the new membership test's vendor/self-submitter precondition. Final membership coverage explicitly uses a distinct on-behalf submitter. Finance rules were not changed to satisfy the test. Mobile/laptop loading/error/empty states and loaded Finance/Admin screenshots were inspected at 1280, 1024 and 390 pixels.

The latest restore snapshot contains 62 tables, 61 forced-RLS business tables, 362 transactions, 392 reports/evaluations, 5,047 verified audit events and 263 verified private artifacts; 167.846 seconds under shared-host checks, source unchanged. Actual document transaction/version/evaluation/report digest survived API/worker/web restart. This is not cloud recovery or RTO/RPO. Benchmarks are [measured separately](performance_phase6.md); query plans/raw reports remain private/ignored.

## Scope and known limitations

Real native PDF and CPU OCR work; remote TypeLLM is contract-tested; VLM/SGLang live execution is externally blocked. The financial intelligence layer is statistical, separately governed and locally measured. Representative final independent labels are absent, so no classifier, probability/calibration or SHAP. New scopes default RULES_ONLY/null score. No online learning/retraining/promotion occurs from reviewer clicks.

No actual Azure deployment, container image build/registry publication, GitHub CI success, hosted SSO/Blob/egress/pilot restore/rollback or production throughput is claimed. Malware is NOT_CONFIGURED, advanced table/segmentation families need human review/validation, PDF report export remains deferred, and remote-wide object inventory is not implemented by the local cache reconciler. Cloud/provider/retention/incident policy and real-data authorization remain external inputs.

Original team pack/ZIP/specification and all fixture manifests are preserved; historical Phase-0–5 reviews are byte-unchanged. No deterministic rule/domain rewrite or new business migration was introduced. [Capability matrix](release_matrix.md), [security review](security_release_review.md), [architecture](architecture.md), [data flow](data_flow.md), [local handoff](runbooks/phase6-local.md), [enterprise gate](runbooks/enterprise-pilot.md), [recovery](runbooks/recovery.md) and [failure operations](runbooks/failure-operations.md) provide the final handoff.

## Git publication

The final local gate passed before publication. Release-artifact commit: `2999d9d`; verified application/Finance/Admin/enterprise boundaries: `a838450`; complete handoff commit: `74f9c52`. Exactly one `GIT_TERMINAL_PROMPT=0 git -c core.askPass= push origin main` attempted **`74f9c529d666440df8a39d51978cad6c15b1f2c7`** and failed **exit 128**, because the HTTPS username could not be read with prompts disabled. **LOCAL DELIVERY COMPLETE — GITHUB PUBLICATION BLOCKED BY AUTHENTICATION.** No credential change, retry, alternate transport or force-push occurred. Remote SHA/published files remain unverified. A final documentation-only commit records the outcome; [progress](progress.md) preserves the exact safe error. Local app: http://127.0.0.1:3000. No further phase starts automatically.
