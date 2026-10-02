from copy import deepcopy
import hashlib

import pytest

from fixture_support import (
    FixtureError, ROOT, collect, decimal_text, load_fixture_set, validate_fixture_set,
)


def test_checked_in_reference_graph(baseline):
    assert len(baseline.references) == 12
    assert sum(map(len, baseline.references.values())) == 38
    index, parents = {}, {}
    for name, records in baseline.references.items():
        collect(records, name, index, parents)
    assert len(index) == 49  # 38 roots + PO/GRN lines + 3 allocations + 6 ledger rows.
    employees = {e["id"]: e for e in baseline.references["employees"]}
    claimant, peer, manager, head = baseline.references["employees"]
    assert claimant["manager_id"] == peer["manager_id"] == manager["id"]
    assert manager["manager_id"] == head["id"]
    assert head["manager_id"] is None
    assert all(e["manager_id"] is None or e["manager_id"] in employees for e in employees.values())


def test_reference_finance_operands(baseline):
    po = baseline.references["purchase_orders"][0]
    line = po["lines"][0]
    grn = baseline.references["goods_receipts"][0]["lines"][0]
    ordered = decimal_text(line["ordered_quantity"])
    accepted = decimal_text(grn["accepted_quantity"]) - decimal_text(grn["returned_quantity"]) - decimal_text(grn["reversed_quantity"])
    assert (ordered, accepted) == (100, 80)
    assert ordered * decimal_text(line["unit_price"]) * (1 + decimal_text(line["tax_rate"])) == decimal_text(po["approved_ceiling_amount"])
    history = baseline.references["historical_transactions"]
    allocations = [a for h in history for a in h.get("allocations", [])]
    active = sum(decimal_text(a["quantity"]) for a in allocations if a["lifecycle"] in {"CONSUMED", "RESERVED"})
    excluded = {a["lifecycle"]: decimal_text(a["quantity"]) for a in allocations if a["lifecycle"] not in {"CONSUMED", "RESERVED"}}
    assert active == 30
    assert excluded == {"RELEASED": 5, "REVERSED": 7}
    assert min(ordered - active, accepted - active) == 50
    assert [h["settlement_status"] for h in history] == ["PAID", "NOT_PAYABLE", "NOT_PAYABLE", "PAID", "PENDING"]
    assert history[-1]["capacity_state"] == "RESERVED"


def test_budget_ledger_and_history_agree(baseline):
    vendor, expense = baseline.references["budgets"]
    for budget, expected in [(vendor, "82000.00"), (expense, "48800.00")]:
        ledger = budget["ledger"]
        available = sum(decimal_text(e["amount"]) if e["entry_type"] == "ALLOCATION" else -decimal_text(e["amount"]) for e in ledger)
        assert available == decimal_text(expected)
    paid_invoice = baseline.references["historical_transactions"][0]
    assert vendor["ledger"][1]["owner_id"] == paid_invoice["id"]
    assert vendor["ledger"][1]["amount"] == paid_invoice["total_amount"]
    assert decimal_text(vendor["ledger"][1]["amount"]) + decimal_text(vendor["ledger"][2]["amount"]) == decimal_text(baseline.references["purchase_orders"][0]["approved_ceiling_amount"])
    paid_meal, pending_meal = baseline.references["historical_transactions"][-2:]
    assert expense["ledger"][1]["owner_id"] == paid_meal["id"]
    assert expense["ledger"][2]["owner_id"] == pending_meal["id"]
    assert expense["ledger"][1]["amount"] == paid_meal["claimed_amount"]
    assert expense["ledger"][2]["amount"] == pending_meal["claimed_amount"]


def test_demo_policy_configuration(baseline):
    policies = baseline.references["expense_policies"]
    assert [(p["category"], p["allowance_amount"], p["unit"]) for p in policies] == [
        ("HOTEL", "8000.00", "ELIGIBLE_NIGHT"), ("MEAL", "1500.00", "EMPLOYEE_LOCAL_DAY"),
        ("TAXI", "3000.00", "EMPLOYEE_LOCAL_DAY"),
    ]
    bands = baseline.references["approval_policies"][0]["bands"]
    assert [(b["lower_bound_amount"], b["lower_inclusive"], b["upper_bound_amount"], b["required_roles"]) for b in bands] == [
        ("0.00", False, "10000.00", ["MANAGER"]),
        ("10000.00", True, "100000.00", ["MANAGER", "DEPARTMENT_HEAD"]),
        ("100000.00", True, "500000.00", ["MANAGER", "DIRECTOR"]),
        ("500000.00", True, None, ["MANAGER", "CFO"]),
    ]
    assert all(b["upper_inclusive"] is False for b in bands)


def test_repeated_loads_and_checked_in_digests(baseline):
    again = load_fixture_set()
    assert baseline.normalized() == again.normalized()
    assert baseline.digest() == again.digest()
    entries = [line.split("  ", 1) for line in (ROOT / "data/synthetic/fixtures.sha256").read_text().splitlines()]
    # The P0-03 manifest owns these documented directories, not later datasets.
    files = {p.relative_to(ROOT).as_posix() for p in (ROOT / "data/synthetic/reference").glob("*.json")}
    files |= {p.relative_to(ROOT).as_posix() for p in (ROOT / "data/golden_cases").rglob("*.json")}
    assert len(entries) == len(files) == 23
    assert {path for _, path in entries} == files
    for digest, path in entries:
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("name,field,value", [
    ("vendors", "id", "DEMO-VENDOR-NUMBER"),
    ("vendors", "id", "00000000-0000-0000-0000-000000000000"),
    ("vendors", "version", True),
    ("vendors", "effective_to", "2026-01-01"),
    ("vendors", "effective_from", "2026-02-30"),
    ("vendors", "legal_name", ""),
    ("vendors", "tax_identifier", "REAL-TAX-NUMBER"),
    ("vendors", "payment_account_token", "1234567890"),
    ("employees", "manager_id", "51000000-0000-4000-8000-999999999999"),
    ("employees", "manager_id", "51000000-0000-4000-8000-000000000001"),
    ("employees", "cost_center_id", "52000000-0000-4000-8000-999999999999"),
    ("employees", "department", "DEMO-WRONG-DEPARTMENT"),
    ("employees", "employment_to", "2024-01-01"),
    ("purchase_orders", "vendor_id", "50000000-0000-4000-8000-999999999999"),
    ("purchase_orders", "currency", "IN1"),
    ("purchase_orders", "currency", "USD"),
    ("purchase_orders", "approved_ceiling_amount", "1e5"),
    ("budgets", "currency", "inr"),
    ("budgets", "legal_entity_id", "20000000-0000-4000-8000-000000000002"),
])
def test_malformed_reference_records_are_rejected(fixtures, name, field, value):
    fixtures.references[name][0][field] = value
    with pytest.raises(FixtureError):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("name,field", [
    ("vendors", "status"), ("employees", "grade"), ("purchase_orders", "lines"),
    ("goods_receipts", "source_version"), ("expense_policies", "effective_to"),
    ("approval_policies", "bands"), ("budgets", "ledger"),
    ("historical_transactions", "settlement_status"), ("documents", "facts"),
])
def test_required_reference_fields(fixtures, name, field):
    del fixtures.references[name][0][field]
    with pytest.raises(FixtureError, match="missing required"):
        validate_fixture_set(fixtures)


def test_duplicate_uuid_is_rejected(fixtures):
    fixtures.references["vendors"].append(deepcopy(fixtures.references["vendors"][0]))
    with pytest.raises(FixtureError, match="duplicate stable ID"):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("tenant,entity", [
    ("10000000-0000-4000-8000-000000000001", "20000000-0000-4000-8000-000000000002"),
    ("10000000-0000-4000-8000-000000000002", "20000000-0000-4000-8000-000000000003"),
])
def test_resolving_vendor_in_wrong_scope_is_rejected(fixtures, tenant, entity):
    fixtures.references["vendors"][0].update(tenant_id=tenant, legal_entity_id=entity)
    with pytest.raises(FixtureError, match="tenant mismatch|entity mismatch"):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("name,field,value", [
    ("purchase_orders", "po_id", "60000000-0000-4000-8000-999999999999"),
    ("purchase_orders", "vendor_id", "20000000-0000-4000-8000-000000000001"),
    ("purchase_orders", "legal_entity_id", "20000000-0000-4000-8000-999999999999"),
    ("goods_receipts", "po_line_id", "71000000-0000-4000-8000-999999999999"),
    ("goods_receipts", "accepted_quantity", "86.0000"),
    ("goods_receipts", "returned_quantity", "90.0000"),
    ("goods_receipts", "uom", "BOX"),
])
def test_broken_po_and_grn_lines(fixtures, name, field, value):
    fixtures.references[name][0]["lines"][0][field] = value
    with pytest.raises(FixtureError):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("version,dates,message", [
    (1, ("2027-01-01", "2028-01-01"), "duplicate logical policy version"),
    (2, ("2026-06-01", "2027-01-01"), "overlapping policy periods"),
])
def test_policy_version_and_period_conflicts(fixtures, version, dates, message):
    extra = deepcopy(fixtures.references["expense_policies"][0])
    extra.update(id="62000000-0000-4000-8000-000000000099", version=version,
                 effective_from=dates[0], effective_to=dates[1])
    fixtures.references["expense_policies"].append(extra)
    with pytest.raises(FixtureError, match=message):
        validate_fixture_set(fixtures)


def test_approval_band_overlap_is_rejected(fixtures):
    fixtures.references["approval_policies"][0]["bands"][1]["lower_bound_amount"] = "9999.00"
    with pytest.raises(FixtureError, match="gap/overlap"):
        validate_fixture_set(fixtures)


def test_different_policy_codes_cannot_hide_applicable_overlap(fixtures):
    extra = deepcopy(fixtures.references["expense_policies"][0])
    extra.update(id="62000000-0000-4000-8000-000000000099", policy_code="DEMO-OTHER-HOTEL")
    fixtures.references["expense_policies"].append(extra)
    with pytest.raises(FixtureError, match="overlapping applicable policy periods"):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("name", ["expense_policies", "approval_policies"])
def test_selected_policy_period_must_cover_transaction_date(fixtures, name):
    fixtures.references[name][0]["effective_to"] = "2026-09-01"
    with pytest.raises(FixtureError, match="outside effective period"):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("value", ["PASS", "RESERVED"])
def test_paid_history_cannot_misstate_allocation_lifecycle(fixtures, value):
    fixtures.references["historical_transactions"][0]["allocations"][0]["lifecycle"] = value
    with pytest.raises(FixtureError, match="allocation lifecycle"):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("field,value", [
    ("entry_type", "UNKNOWN_ENTRY"),
    ("owner_id", "30000000-0000-4000-8000-000000000101"),
])
def test_budget_commitment_type_and_owner(fixtures, field, value):
    fixtures.references["budgets"][0]["ledger"][2][field] = value
    with pytest.raises(FixtureError, match="budget entry type|owner kind mismatch"):
        validate_fixture_set(fixtures)
