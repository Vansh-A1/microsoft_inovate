# Phase-6 measured local performance
Environment: Intel(R) Core(TM) Ultra 7 265; 20 logical CPUs; 65,278,588 KiB reported RAM (~62.3 GiB); Ubuntu 24.04/glibc 2.39, Linux 6.11 x86_64; Python 3.13.11, PostgreSQL 16.15, Node 24.21.0, CPU Tesseract 5.3.4. Measurements used warm loopback/development processes and synthetic data on a shared host while release checks also ran. No VLM, cloud throughput or production SLA is measured.

Executed benchmark commands (each exit 0):

```bash
.venv/bin/python scripts/benchmark/finance_phase3.py
.venv/bin/python scripts/benchmark/workflow_phase4.py
.venv/bin/python scripts/benchmark/intelligence_phase5.py
.venv/bin/python scripts/benchmark/release_phase6.py
.venv/bin/python scripts/benchmark/documents_phase2.py --output runtime/release/documents-phase6.json
```

## Target versus tested scope

| Proposed specification target | Tested scope / limitation |
|---|---|
| List/detail p95 <500 ms with 10k transactions | HTTP measured on retained demo (362 transactions at restore snapshot), not 10k API rows; separate 10k history measurements below. |
| Enqueue/finalize p95 <2 s, excluding documents | Actual enqueue/claim/context/finalization samples below; small sample and shared host. |
| Rules/matching p95 <5 s at 10k history and 10 concurrent evaluations | 10k-history measurements and separate eight-way correctness tests; combined ten-way target is not established. |
| Typical 1–3 page document <90 s end to end | Actual CPU preprocessing/extraction measured on 14 fixtures; browser covers durable end to end but is not a provider SLA. Real VLM unmeasured. |
| Structured 1k-row batch <60 s | Not measured at 1k rows. 200 structured scale inputs and actual small import/browser batches are covered; no batch-target claim. |

## Measured operations

All values below are **MEASURED**, not target numbers. Service benchmarks reuse owned migrated disposable schemas and remove only those schemas. Raw reports remain ignored under runtime/generated. The benchmark percentile helper uses sorted index floor((n−1)×0.95); the HTTP probe uses index 18 for 20 samples. Small samples are not statistically robust tail estimates.

### Loopback HTTP (20 samples per route)

| Operation | Samples | Median ms | Measured p95 ms | Maximum ms |
|---|---:|---:|---:|---:|
| list_25 | 20 | 68.065 | 119.491 | 133.359 |
| case_detail | 20 | 5.349 | 9.119 | 9.843 |
| review_queue_25 | 20 | 21.716 | 29.313 | 31.073 |
| audit_timeline | 20 | 7.347 | 9.05 | 10.093 |
| report | 20 | 22.797 | 28.914 | 29.413 |
| admin_catalog | 20 | 33.64 | 93.217 | 101.648 |

### Finance: 10k generated history, 200 structured records

| Operation | Samples | Median ms | Measured p95 ms | Maximum ms |
|---|---:|---:|---:|---:|
| duplicate_candidate_lookup | 25 | 4.105 | 7.322 | 10.533 |
| pure_rules_including_po_grn | 10 | 2.981 | 4.044 | 6.313 |
| transactional_finalization_including_budget | 10 | 194.855 | 407.887 | 469.787 |
| enqueue_claim_context_finalization | 10 | 569.673 | 779.218 | 837.507 |

### Workflow: 100 computed synthetic cases

| Operation | Samples | Median ms | Measured p95 ms | Maximum ms |
|---|---:|---:|---:|---:|
| review_queue_25 | 10 | 23.73 | 26.806 | 27.611 |
| case_detail | 10 | 4.061 | 4.474 | 6.347 |
| audit_timeline_50 | 10 | 3.672 | 4.458 | 4.709 |
| dashboard | 10 | 6.234 | 7.742 | 11.859 |
| assignment_action | 10 | 72.108 | 88.568 | 105.58 |
| report_export_generation | 10 | 86.663 | 102.906 | 128.28 |
| reconciliation_batch | 3 | 749.706 | 749.706 | 779.314 |
| correction_and_reevaluation | 1 | 577.237 | 577.237 | 577.237 |
| cancellation | 1 | 63.974 | 63.974 | 63.974 |

### PIT/anomaly: 10k canonical submitted history

| Operation | Samples | Median ms | Measured p95 ms | Maximum ms |
|---|---:|---:|---:|---:|
| pit_history_query_10000 | 5 | 345.7 | 355.998 | 491.039 |
| feature_build_10000 | 5 | 141.853 | 141.873 | 233.289 |
| statistical_score | 20 | 0.001 | 0.006 | 0.024 |

## Actual native/OCR corpus

Command: `.venv/bin/python scripts/benchmark/documents_phase2.py --output runtime/release/documents-phase6.json` (exit 0). Fourteen synthetic PDFs/PNG/JPEG: seven READY, five NEEDS_INPUT, two permanent parsing failures. READY means extraction draft sufficiency, not screening PASS; human verification and finance controls remain necessary. Times include bounded CPU parsing/render/extraction/normalization, not upload/queue/reviewer time.

| Source | Processing result | Measured seconds |
|---|---|---:|
| ambiguous_date.pdf | NEEDS_INPUT | 0.189326 |
| conflicting_total.pdf | NEEDS_INPUT | 0.182261 |
| corrupt.pdf | PROCESSING_FAILURE | 0.091285 |
| missing_total.pdf | NEEDS_INPUT | 0.182747 |
| password_protected.pdf | PROCESSING_FAILURE | 0.094983 |
| receipt_native.pdf | READY | 0.179148 |
| receipt_photo.jpg | READY | 0.390864 |
| receipt_scan.pdf | READY | 0.362699 |
| receipt_scan.png | READY | 0.361766 |
| receipt_unreadable.png | NEEDS_INPUT | 0.220176 |
| uncertain_bundle.pdf | NEEDS_INPUT | 0.23653 |
| untrusted_instructions.pdf | READY | 0.186971 |
| vendor_multipage.pdf | READY | 0.23738 |
| vendor_native.pdf | READY | 0.207229 |

## Concurrent integrity and recovery

Four actual PostgreSQL tests synchronize eight finalizers. Budget capacity 100 admits one 80 claim and holds seven; GRN capacity 50 admits one 30-unit invoice and holds seven; unresolved repeated obligations allow at most one PASS (the observed batch remains REVIEW); after explicit shared-source dispositions a 1,000 receipt admits five 200 claims and holds three. Finalizer retries preserve allocation count. Existing tests cover stale approvals, cancellation/release compensation and audit failure rollback. No throughput inference is drawn from these correctness tests.

The latest local restore verified 62 tables/61 forced-RLS business tables, 5,047 audit events, 392 report manifests and 263 object hashes in **167.846 seconds**, with the source unchanged. This was a logical synthetic restore under concurrent local validation, not a disaster RTO/RPO. Earlier isolated drill was 67.826 seconds; workload and snapshot size differ. Cloud recovery remains unmeasured.

Actual query plans are retained in the ignored benchmark reports; scoped operational indexes already exist. No speculative database indexes or new migration were added. Correction/cancellation each have one measured sample. API/export/assignment tails and multi-tenant production contention require an authorized pilot workload. No unmeasured target is labeled achieved.
