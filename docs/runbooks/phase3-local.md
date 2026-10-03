# Phase-3 local finance runbook

This extends the [CPU setup](phase1-local.md) and [document pipeline](phase2-local.md).
All policies, masters, payment proofs and authority identities are fictional.
Use the owned PostgreSQL cluster and project-local tools; no GPU is required.

Commands executed from the repository root:

```bash
.venv/bin/alembic -c apps/api/alembic.ini upgrade head
.venv/bin/python scripts/dev/setup_finance_identities.py
export PATH="$PWD/runtime/tools/node-v24.21.0-linux-x64/bin:$PATH"
npm --prefix apps/web run generate:api
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
.venv/bin/python scripts/dev/run.py
```

The identity setup activates the validated `rules-p3-v1` profile and additive
catalog, then configures private synthetic reviewer, Manager, Department Head,
Director, CFO and own-claim reader identities. It prints labels, never credentials.
The loopback supervisor explicitly enables the development identity picker.
Its default is disabled outside that supervisor. Selection uses server-configured
labels and an httpOnly SameSite Strict cookie; clients cannot invent actor/roles.
This is a local synthetic demonstration, not SSO or production authentication.

Open [AP Review Desk](http://127.0.0.1:3000). Existing seeded evaluations remain
their original immutable 20-control reports. New scope evaluations use 28 controls.
New transactions commonly HOLD until the required actual approval chain exists.

## References

Reference imports accepts an array of `{kind,payload}` JSON records. Stage, inspect
validation findings, validate, then explicitly activate with a reason. Required
fields are checked before activation; broken scope/links, float money, currency,
effective-period/overlap/band gaps and raw bank details are rejected. Updates use
the existing record UUID and a greater version. New evaluations pin exact versions;
old versions and snapshots remain immutable. An imported budget's nested ledger
gets server-owned child source versions and links.

Supported catalogs include vendors/payment-account equality tokens, employees,
PO/lines, GRN/lines, contracts/lines, service acceptances, UOM conversions,
expense/approval policies, delegations, independently verified preapprovals and
company payments, budgets/ledger, FX facts and the finance profile.
The additive synthetic catalog supplies 20 vendors, 30 employees, 50 PO/GRN lines,
3 cost centers and explicit fictional USD/INR FX. Its 200 structured scale inputs
are intentionally unverified; they are not 200 eligible invoices.

## Matching, budgets and actions

Case detail shows ordered, accepted, returned/reversed, previously allocated and
remaining quantities, proposed quantity, shortfall and price tolerance. PO gets
explicit priority; an authorized contract route still requires independent service
acceptance when configured. Missing UOM conversion or critical terms cannot PASS.

Budget capacity shows allocation, adjustment, consumed, open PO commitment,
reservation, available and covered commitment. Rules report incremental exposure.
A covered PO invoice transfers exposure at consumption rather than deducting it
twice. The authenticated ledger API transitions all resources belonging to one
evaluation together. RESERVED can be consumed or released; CONSUMED requires an
explicit reversal. Cancellation releases only unconsumed capacity and cancels its
queued work; it never silently releases settlement.

Enter a reason, request current approvals, then use the configured synthetic
Manager/Head identities for their ordered steps. The API checks server role,
effective master authority, currency/ceiling, scope, manager relationship,
delegation and separation of duties. Self/forged/out-of-order attempts are rejected;
eligible rejected approval actions are audited. Material corrections or changed
policy/exception requirements require fresh authority. Approval does not waive a
failed finance control.

Duplicate comparison displays both facts, individual signals, lifecycle and
actual uploaded pages when available. Similarity is a measurement, not probability.
Fuzzy/pHash alone routes REVIEW. Distinct/confirmed/shared dispositions need the
authorized role, current versions, reason and real evidence. Shared disposition
also requires an actual common receipt and authorized capacity shares.

Authorize a receipt share with actual document and canonical item UUIDs and decimal
amount/quantity. This establishes attribution; it does not create free capacity.
Cumulative shares still cannot exceed the eligible receipt. Ordinary reference
receipts in demo JSON are explicitly adjudicated synthetic facts; previews exist
only for actual uploads. Own-claim readers receive masked cross-employee evidence.

Waivers require the configured explicit role, allowed rule, current transaction,
evidence, reason and bounded expiry. Original failed findings remain visible.
Mandatory safety controls cannot be cleared by generic admin authority.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
.venv/bin/python -m pip check
.venv/bin/alembic -c apps/api/alembic.ini current
.venv/bin/alembic -c apps/api/alembic.ini check
node --test apps/web/checks/development-identity.mjs
npm --prefix apps/web run test:e2e
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/benchmark/finance_phase3.py
sha256sum -c docs/source_inputs.sha256
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c data/extraction_spike/fixtures.sha256
sha256sum -c data/documents_phase2/fixtures.sha256
cmp docs/AP_Exception_Assistant_Codex_Spec.md AP_Exception_Assistant_6_Person_Team_Pack/AP_Exception_Assistant_Codex_Spec.md
```

Integration and benchmark commands create/drop only their own UUID-named schemas
in `ap_phase1_test`; they never reset meaningful development data. The benchmark
really persists 10,000 generated histories and 200 structured inputs, measures
indexed candidate retrieval, pure matching/rules and transactional finalization,
then removes only its disposable schema. Reports/screenshots remain ignored.
Browser tests create retained synthetic records through the actual API/worker.

## Bounds

INR ordinary expense/invoice finance is the configured supported mode. USD and FX
reference facts do not authorize invented conversions; unsupported currency is
incomplete. Credit notes and uncertain document segmentation retain their earlier
safe boundaries. Catalog/history candidate/expense aggregate limits produce
explicit failures, not empty successful searches. Scope-wide admission locking
favors correctness over throughput. Local measured timings are not production SLAs.
Native/OCR extraction supports the previously tested layouts and manual verification;
live VLM remains **DEFERRED — BLOCKED EXTERNAL PREREQUISITE**. Malware scanning is
NOT_CONFIGURED in development. Production SSO, ERP connectors, real finance policy,
backup/restore, operations and ML require later authorized work. Phase 4 has not begun.
