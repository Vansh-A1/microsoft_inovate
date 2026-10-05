# REL-04 — verified database contention boundary

2026-10-05, Phase-6 support, explicit continued delegated reliability request. Starting clean local main `7c2edb2`; [bounded responsibility](kivo_concurrency_plan.md) recorded before changes. Inspected the original traceback, transactions/scope locks, worker lease/failure/retry, isolated test fixture and relevant prior evidence. No concurrent checkout writer or other integration runner found. Existing application and resident model stayed running; portfolio untouched.

**The clean applicable aggregate passed: 25 tests, 411.94 seconds, exit0.** These are the previous 22 checks plus three actual timeout/rollback/recovery checks. No production defect was reproduced that justifies changing the conservative finance lock. Production code, database/host/security settings, lock/statement/lease/attempt limits, financial checks and API/UI/model serving remain unchanged. This checkpoint adds test-only instrumentation, meaningful recovery checks and evidence; no new product feature or publication.

## Diagnosis

The original broader run was 21 pass/1fail/791.29s while a browser batch ran concurrently. The failed GRN call raised PostgreSQL SQLSTATE 55P03 at `finance.finalize`'s first `pg_advisory_xact_lock`, before reading/modifying its job or publishing evaluation/ledger/report/audit effects. Eight committed leases were submitted together to the domain finalizer. The test calls `finalize` directly and propagates timeout exceptions; it does not pass them through the normal worker failure/retry orchestration. Its finance assertions were not reached after that exception; no overbooking or duplicate financial effect was shown.

The scope key serializes tenant/entity duplicate and capacity admission with atomic finalization. Transaction-local `lock_timeout` remains 5000ms and `statement_timeout` 10000ms (the latter is per statement, not an entire request deadline). A caller waiting behind a holder/queue for 5s receives55P03, even if later release would permit it. This is the admission wait boundary; it is not an eight-invoice or universal throughput guarantee. Narrowing/removing the lock or extending timeout without evidence would weaken or obscure this conservative design.

Test schemas use `ap_phase1_test`; live application uses a different database. An actual harmless random advisory-key probe acquired the same key in both databases simultaneously and observed distinct lock database OIDs. No business records changed. Thus the two original runners could not collide through that advisory key. Schemas within the same database still share the namespace; this verification used one integration runner. Shared host/I/O pressure is a plausible reason the earlier queue exceeded 5s, but the original holder/wait trace was not collected, so exact attribution is unproved. No artificial host load, service shutdown or settings change was used to conceal it.

## Measured eight-way workload

Each scenario creates/approves eight fictional finance cases, commits actual leases and releases eight threads together. Budget 80 against 100 and GRN 30 against 50 must each yield one PASS/seven HOLD. Repeated obligations must yield at most one PASS. Shared receipt 200 against 1000 requires explicit duplicate dispositions, then five PASS/three HOLD. Existing Decimal capacity, state, ownership and same-lease allocation-replay assertions are unchanged. Receipt has an initial admission round and a second after explicit source/business disposition.

The optional test-only probe times actual advisory-query waits and complete transaction/commit intervals with monotonic clocks. It logs no SQL, parameters, source values, actor IDs or credentials. Each measured transaction had one advisory wait. COMMITTED here means database effects committed; it does not mean a financePASS.

| Case / round | Initial isolated max wait ms | Final aggregate median wait ms | Final max wait ms | Final max transaction ms |
|---|---:|---:|---:|---:|
| Budget | 874.983 | 441.914 | 983.021 | 1141.381 |
| GRN | 874.425 | 484.510 | 937.265 | 1155.000 |
| Duplicate | 954.651 | 462.790 | 948.760 | 1111.993 |
| Receipt, initial | 1046.504 | 475.722 | 950.964 | 1114.557 |
| Receipt, after disposition | 1084.579 | 588.082 | 1058.782 | 1224.072 |

Forty transactions per run (five eight-caller groups), zero rollbacks in these normal bursts, unchanged capacity assertions. These are two bounded observations on a shared machine using small fresh fictional catalogs. They do not reproduce the retained live 1744-version/867k-membership footprint, sustained arrival rates or the original simultaneous browser/migration load. No global latency/throughput or production availability inference. Final large immutable snapshot check separately measured 174.104/155.575/195.882ms in its fresh schema; no stress distribution claim.

## Actual timeout and recovery

Controlled blockers held only the finance scope in disposable migrated test schemas. Actual application locks/settings/errors were used; no fabricated delay/exception or timeout increase.

| Boundary | Final measured failure ms | Verified outcome |
|---|---:|---|
| API source transaction creation | 5013.660 | Retryable503 DATABASE_UNAVAILABLE; no case/version/idempotency-key/evaluation/report/allocation/audit effect. After release, exact same body/key creates one case; replay returns it without new effects. |
| Already committed current-generation finalization lease | 5009.696 | Actual 55P03, all prior counts/digests/audit hashes and RUNNING lease/owner/attempt unchanged. Same still-valid lease after release produces one PASS, evaluation/report and 20 GRN units; replay adds nothing. |
| Worker finalization and bounded recovery | 5008.498 | Failure classified DATABASE_UNAVAILABLE/RETRYABLE, one failure audit, eligible=false. Real 2–3s scheduler backoff, actual subsequent claim/finalization completes on attempt 2 with one evaluation/report/allocation set, unchanged canonical source version and retained prior audit. Final measured wait-plus-reclaim 2816.866ms. Idle repeat adds nothing. |

The worker test feeds the real already committed lease at the claim/finalization boundary to deterministically acquire the blocker. Only that stage handoff is instrumented; PostgreSQL timeout, rollback, failure classification/audit, scheduler delay and later claim use real code/time/SQL. No clock advance, lease extension or fake successful response. Existing actual claim-timeout test also verifies a blocked claim remains QUEUED/attempt 0 and later runs once. Failure-disposition contention lasting another 5s and 60s lease-expiry recovery were inspected in code but not forced in this checkpoint; those prolonged-load paths remain a limitation, not an asserted new test result. Existing attempts/leases still bound recovery and cannot clear missing finance controls.

## Exact executed checks

Commands from the repository, existing finance `.venv`, no package/runtime changes. Logs/measurements stay in ignored `runtime/kivo-concurrency`; [sanitized evidence](../data/kivo_reliability/capacity-results.json) contains scores/timings/hashes and no private IDs/source output. One pytest runner at a time, no overlapping browser/migration batch initiated. Selected native document checks already use provider-free CPU settings; no inference requests were initiated.

```sh
AP_CAPACITY_MEASUREMENT_LABEL=isolated-before PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_release_phase6.py -k eight_concurrent -q --tb=short
# 4 passed, 5 deselected, 77.22s, exit0

AP_CAPACITY_MEASUREMENT_LABEL=affected PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_kivo_capacity_recovery.py apps/api/tests/integration/test_clearledger_worker_recovery.py -q --tb=short
# 3 passed, 56.30s, exit0 (two new boundary checks plus existing claim recovery)

AP_CAPACITY_MEASUREMENT_LABEL=worker-affected PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_kivo_capacity_recovery.py -k preclaimed_worker -q --tb=short
# 1 passed, 2 deselected, 21.42s, exit0

AP_CAPACITY_MEASUREMENT_LABEL=clean-aggregate AP_SNAPSHOT_MEASUREMENT_LABEL=concurrency-final PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests/integration/test_release_phase6.py apps/api/tests/integration/test_document_finance.py apps/api/tests/integration/test_clearledger_worker_recovery.py apps/api/tests/integration/test_references_phase3.py apps/api/tests/integration/test_snapshot_batch.py apps/api/tests/integration/test_kivo_capacity_recovery.py -q --tb=short
# 25 passed, 411.94s, exit0
```

All runs retain the existing Starlette/httpx deprecation warning; dependencies were not changed. The new aggregate supersedes the prior absence of a clean combined applicable run, while the historical 21 pass/1fail and isolated GRN rerun remain preserved. Previous836 backend/44 browser results remain historical; no UI/product code change required another browser build/run here. Final source/secret/whitespace/health checks and local commit are recorded in progress. No host/security/GPU/Docker/model/credential/network change, meaningful database reset, public/LAN/cloud deployment or push.

The verified local boundary is safe rejection/rollback/replay and bounded recovery under the stated workload. Loaded-host 503/5s waits can still occur. Larger catalog/history, sustained real arrival rates and prolonged failure-bookkeeping contention require separate representative acceptance; no unmeasured concurrency guarantee or new infrastructure action follows. Stop at this concurrency checkpoint.


Final closure checks: `python -m py_compile` on the three changed/new integration modules exit0; bounded source scan434 text files/no forbidden paths or configured credential patterns; cached Gitleaks8.30.1 zero source findings/one redacted detection probe, exit0. Eight read-only judge scenarios/current eligibility/28 controls/original correction HOLD and READY/AVAILABLE health pass. Byte comparison against7c2edb2 preserves141 production/frontend/original-pack/spec files. Optional `.venv/bin/ruff check --select F821,F822,F823 ...` could not run (executable absent, exit127); no lint-pass claim or dependency installation. Actual25-test execution and syntax checks passed.
