# ADR-0011 — Activated finance catalogs and append-only control lifecycles

Status: accepted under the direct continuous P3-01–P3-06 approval, 2026-10-03.

The original rules-p1-v7 engine remains available for retained Phase-1/2 inputs.
An explicitly validated and activated finance_profiles record selects rules-p3-v1
for new evaluations in that scope. This is server-owned reference configuration;
ordinary intake cannot select a permissive profile. Existing catalogs are retained
as a compatibility baseline. New approved catalogs select exactly one effective
expense/approval policy, preserving old immutable reference versions and snapshot
membership. Staging never makes a reference evaluable. Activation validates again
under the existing scoped finance lock to prevent a concurrent stale activation.

Reuse reference_records and reference_snapshots; add import/activation metadata,
append-only allocations/lifecycle events and budget events, comparison/resolution
facts, fingerprint/band facts, receipt shares and approval request/action/waiver
facts. ReferenceBatch is a current workflow projection. Every new table has scoped
foreign keys and forced PostgreSQL RLS; authoritative facts reject ORM and direct
SQL mutation. Allocation reservation and consumption are states of one allocation,
with explicit release/reversal events. The original minimal capacity table remains
for legacy evaluations; new catalogs use the full lifecycle and do not count both.

The conservative tenant/entity finance advisory lock remains the admission guard.
This favors correctness for the local demo over throughput. Resources are locked
in stable order inside that boundary. Workers retain bounded retries; failed audit
or any capacity persistence rolls back the entire decision. No payment is executed.

RapidFuzz 3.14.6 ratio supplies named similarity measurements only, never calibrated
probability or identity authority. A separately versioned OpenCV DCT pHash uses
64 bits and indexed disjoint bands for candidate retrieval. Only corroborated
active business matches or authorized version-bound dispositions confirm repeats.
Thresholds are labeled synthetic configuration requiring independent validation.

Technical basis: [RapidFuzz ratio](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html),
[PostgreSQL 16 serialization failure handling](https://www.postgresql.org/docs/16/mvcc-serialization-failure-handling.html).
