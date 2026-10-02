# P0-03 synthetic reference fixtures

Every record is fictional and marked `synthetic: true`. These fixtures describe **DEMO / SYNTHETIC POLICY**, never a real company's rules, tax obligations, approval authority, bank accounts, or payments. They prepare future tests; no finance rule or screening service exists.

## Layout and size

`reference/` contains JSON envelopes with `fixture_schema_version: p0-03-v1`, `source_system: SYNTHETIC_JSON`, and `records`. JSON is the checked-in source of truth; loading never generates IDs, dates, or randomness.

| File | Root records | Purpose |
|---|---:|---|
| [tenants.json](reference/tenants.json) | 2 | Main tenant and an isolation-test sentinel. |
| [legal_entities.json](reference/legal_entities.json) | 3 | Main entity, another entity in the same tenant, another tenant's entity. |
| [cost_centers.json](reference/cost_centers.json) | 1 | DEMO workshop department/cost-center relationship. |
| [vendors.json](reference/vendors.json) | 1 | Approved fictional supplier, curated alias, nonregistered fictional tax identifier and nonpayable account token. |
| [employees.json](reference/employees.json) | 4 | Two claimants, their Manager, and Department Head; acyclic manager links. |
| [purchase_orders.json](reference/purchase_orders.json) | 1 | Approved PO with one UUID line, gross ceiling, zero demo tolerance and budget link. |
| [goods_receipts.json](reference/goods_receipts.json) | 1 | One UUID GRN line; 85 accepted, 5 returned, 0 reversed. |
| [expense_policies.json](reference/expense_policies.json) | 3 | INR 8,000/hotel night, 1,500/meals per employee/local day, 3,000/taxi per employee/local day. |
| [approval_policies.json](reference/approval_policies.json) | 1 | Versioned half-open INR bands, ordered roles, no claimant/submitter self-approval. |
| [budgets.json](reference/budgets.json) | 2 | Gross-basis supplies/travel budgets with six UUID ledger rows. |
| [historical_transactions.json](reference/historical_transactions.json) | 5 | Paid/cancelled/reversed vendor invoices and paid/reserved-pending meals. |
| [documents.json](reference/documents.json) | 14 | Adjudicated JSON source facts for invoices/receipts; **no PDF/image bytes, extraction outputs, or authentic receipt evidence**. |

There are 38 root reference records and 49 UUID records including embedded PO/GRN lines, three historical allocations and six ledger entries. All finance activity is in the main entity; the other scopes provide negative-test targets only. The [golden dataset](../golden_cases/README.md) has ten independent alternatives, not a queue to submit together.

## Identifiers, values, and time

Fixed UUIDs have the form `family-0000-4000-8000-counter`; the twelve-digit counter is deterministic. Examples: tenant `10000000`, entity `20000000`, transaction `30000000`, source facts `40000000`, vendor `50000000`, employee `51000000`, PO `60000000`, budget `61000000`, expense/approval policy `62000000`/`63000000`, PO line `71000000`, GRN/line `76000000`/`76100000`. Golden case and snapshot families are `90000000` and `81000000`. Display numbers such as `DEMO-PO-001` and `DEMO-INV-PAID-001` are separate attributes and may repeat between distinct obligations under future matching semantics.

All authoritative money, rates, counts of eligible nights, and quantities are **plain decimal strings**. Currency is explicitly `INR`; no FX or rounding convention is inferred. Integers are metadata such as versions, sequence positions and submission-window days. No JSON float is accepted anywhere in this dataset. Explicit zero remains zero; unknown hotel nights and per-night amount remain `null`.

Every UUID record has positive integer `version: 1`. Child versions equal their containing record version. Reference validity uses `[effective_from, effective_to)` with ISO local dates, currently `[2026-01-01, 2027-01-01)`. Employment dates are separate; a null employment end means no supplied end. Business-local timezone is `Asia/Kolkata`; evaluation and approval timestamps are fixed UTC. The checks validate declared policy links and date/dimension consistency; they do not resolve policies for new transactions or establish import freshness. No import pipeline is represented.

## Reproducible operands

PO: `100 × INR 1,000 × (1 + 0.18) = INR 118,000` gross ceiling. The 18% tax is a synthetic arithmetic example with no statutory claim. GRN net accepted is `85 − 5 − 0 = 80`. Prior consumed quantity is 30; cancelled 5 and reversed 7 allocations do not consume current capacity. Thus ordered remaining is 70, received remaining is 50, and eligible new quantity is 50. A proposal for 70 has a 20-unit shortfall. Proposals in golden cases do not change these reference balances.

Supplies budget: `200,000 − 35,400 consumed − 82,600 open PO commitment = 82,000 available`. The prior 30-unit invoice consumes INR 35,400; its consumption plus the remaining PO commitment equals the original ceiling. A covered invoice transfers existing commitment in a future engine; it has zero incremental need in the example. Travel budget: `50,000 − 600 paid − 600 pending reservation = 48,800 available`.

Approval configuration: `(0, 10,000)` Manager; `[10,000, 100,000)` Manager → Department Head; `[100,000, 500,000)` Manager → Director; `[500,000, infinity)` Manager → CFO. These are configuration records, not an implemented approval evaluator. Only the first two chains have actors/actions in selected golden cases.

## Validation and checksums

From the repository root, using the existing Python/pytest environment:

```bash
python3 -m pytest apps/api/tests/fixtures -q
python3 -m pytest -q
sha256sum -c data/synthetic/fixtures.sha256
sha256sum -c docs/source_inputs.sha256
```

[fixture_support.py](../../apps/api/tests/fixtures/fixture_support.py) is test-only standard-library support reusing the domain Money, state and evidence contracts. It rejects missing fields, malformed/duplicate UUIDs, unresolved or incorrectly typed/scoped links, manager cycles, cost-center mismatches, invalid currencies/decimal text, nested floats/constants and duplicate JSON keys, temporal/policy overlaps, invalid bands, stale pins and malformed golden metadata/evidence. Source facts declare their representation explicitly. Negative tests corrupt copies, not the checked-in dataset. Arithmetic tests derive expected operands directly from referenced data and do not screen transactions.

Repeated validated loads must have identical canonical content and SHA-256 digests. The byte-checksum [fixtures.sha256](fixtures.sha256) covers all 23 synthetic/golden JSON files, including the golden manifest; READMEs are outside this data digest. Intentional updates require review, fixture/schema/test updates and a refreshed digest. To regenerate it deliberately from the repository root:

```bash
python3 - <<'PY'
import hashlib
from pathlib import Path
root = Path.cwd()
paths = sorted((root / 'data/synthetic/reference').glob('*.json'))
paths += sorted((root / 'data/golden_cases').rglob('*.json'))
lines = [f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}\n'
         for p in sorted(paths)]
(root / 'data/synthetic/fixtures.sha256').write_text(''.join(lines), encoding='utf-8')
PY
```

Adding a fixture: preserve existing identities/versions as regression inputs; allocate unused deterministic UUIDs, label synthetic fields, supply exact decimals and scope, resolve every parent/policy/budget/source link, and document the intended case. Add required validation fields and meaningful mutation/operand tests if the shape changes. Update the golden manifest, snapshot dependency closure, coverage support and inventory counts deliberately. Review the diff before refreshing checksums; do not regenerate a digest to conceal accidental drift.

## Limits

This is a small P0-03 dataset, not the specification's later 200-transaction/10k-history or training benchmark. It has no real documents, authorization, database ledger, reservation service, import freshness, FX, contracts/service acceptances, UOM conversions, fuzzy/image matching, extraction, ML, or deployment. Fields are fixture conventions, not production API/database schemas. Source facts and demo roles do not prove genuine receipt validity or approval authority. T01–T42 behavior remains NOT IMPLEMENTED.
