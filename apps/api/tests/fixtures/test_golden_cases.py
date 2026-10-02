from datetime import date
from decimal import Decimal

import pytest

from fixture_support import FixtureError, decimal_text, validate_fixture_set


def test_golden_case_catalog_is_data_only(baseline):
    assert len(baseline.cases) == 10
    assert [c["expected_decision"] for c in baseline.cases.values()].count("PASS") == 4
    assert {t for c in baseline.cases.values() for t in c["intended_test_ids"]} == {
        "T01", "T03", "T08", "T13", "T14", "T15", "T16", "T19", "T20", "T24", "T26",
    }
    assert all(c["preparation_status"] == "Fixture prepared; rule not yet implemented." for c in baseline.cases.values())


@pytest.mark.parametrize("path", ["vendor/clean.json", "vendor/paid_duplicate.json", "vendor/partial_grn.json", "vendor/approval_pending.json"])
def test_vendor_arithmetic_and_source_facts(baseline, path):
    case = baseline.cases[path]
    tx, facts = case["transaction"], case["expected_facts"]
    source = next(d for d in baseline.references["documents"] if d["id"] == tx["source_document_id"])["facts"]
    po_line = baseline.references["purchase_orders"][0]["lines"][0]
    grn = baseline.references["goods_receipts"][0]["lines"][0]
    allocations = [a for h in baseline.references["historical_transactions"] for a in h.get("allocations", [])]
    prior = sum(decimal_text(a["quantity"]) for a in allocations if a["lifecycle"] in {"CONSUMED", "RESERVED"})
    ordered = decimal_text(po_line["ordered_quantity"])
    received = decimal_text(grn["accepted_quantity"]) - decimal_text(grn["returned_quantity"]) - decimal_text(grn["reversed_quantity"])
    capacity = min(ordered - prior, received - prior)
    quantity = decimal_text(tx["lines"][0]["quantity"])
    assert decimal_text(facts["ordered_quantity"]) == ordered
    assert decimal_text(facts["accepted_quantity"]) == received
    assert decimal_text(facts["prior_active_quantity"]) == prior
    assert decimal_text(facts["ordered_remaining_quantity"]) == ordered - prior
    assert decimal_text(facts["received_remaining_quantity"]) == received - prior
    assert decimal_text(facts["eligible_new_quantity"]) == capacity
    assert decimal_text(facts["new_billed_quantity"]) == quantity
    assert decimal_text(facts["shortfall_quantity"]) == max(Decimal("0"), quantity - capacity)
    net = quantity * decimal_text(tx["lines"][0]["unit_price"])
    tax = net * decimal_text(tx["lines"][0]["tax_rate"])
    assert net == decimal_text(tx["subtotal_amount"]) == decimal_text(facts["invoice_net_amount"])
    assert tax == decimal_text(tx["tax_amount"]) == decimal_text(facts["invoice_tax_amount"])
    assert net + tax == decimal_text(tx["total_amount"]) == decimal_text(facts["invoice_total_amount"])
    assert source["invoice_number"] == tx["invoice_number"]
    assert source["invoice_date"] == tx["invoice_date"]
    assert source["total_amount"] == tx["total_amount"]
    assert source["quantity"] == tx["lines"][0]["quantity"]
    assert decimal_text(facts["incremental_budget_need_amount"]) == decimal_text(tx["total_amount"]) - decimal_text(facts["existing_commitment_coverage_amount"]) == 0
    assert decimal_text(facts["available_budget_amount"]) == 82000


def test_paid_duplicate_has_distinct_identity_and_equal_obligation(baseline):
    case = baseline.cases["vendor/paid_duplicate.json"]
    prior = baseline.references["historical_transactions"][0]
    current = case["transaction"]
    assert current["id"] != prior["id"]
    assert current["source_document_id"] != prior["source_document_id"]
    assert prior["lifecycle"] == prior["settlement_status"] == "PAID"
    assert all(current[k] == prior[k] for k in ("vendor_id", "invoice_number", "invoice_date", "total_amount", "currency"))
    assert prior["id"] in {ev["record_id"] for ev in case["expected_evidence"]}


@pytest.mark.parametrize("path", ["employee/clean_taxi.json", "employee/hotel_two_nights.json", "employee/hotel_unknown_nights.json", "employee/daily_meals.json", "employee/shared_within.json", "employee/shared_exceeded.json"])
def test_employee_receipt_policy_and_budget_context(baseline, path):
    case = baseline.cases[path]
    tx, facts = case["transaction"], case["expected_facts"]
    item = tx["items"][0]
    source = next(d for d in baseline.references["documents"] if d["id"] == item["source_document_id"])["facts"]
    policy = next(p for p in baseline.references["expense_policies"] if p["id"] == tx["expense_policy_id"])
    claimant = baseline.references["employees"][0]
    assert policy["effective_from"] <= tx["expense_date"] < policy["effective_to"]
    assert policy["category"] == tx["category"] == item["category"] == source["category"]
    assert policy["dimensions"] == {"grade": claimant["grade"], "country": tx["country"], "location": tx["location"]}
    assert tx["expense_date"] == item["expense_date"] == source["expense_date"]
    assert tx["local_timezone"] == item["local_timezone"] == source["local_timezone"]
    assert item["receipt_total_amount"] == source["receipt_total_amount"]
    assert item["eligible_nights"] == source["eligible_nights"]
    assert source["readable"] is True and source["receipt_type"] == policy["receipt_type"] == "ITEMIZED"
    assert facts["allowance_amount"] == policy["allowance_amount"]
    assert decimal_text(item["claimed_amount"]) - decimal_text(item["company_paid_amount"]) - decimal_text(item["applied_advance_amount"]) == decimal_text(facts["computed_reimbursement_amount"]) == decimal_text(tx["requested_amount"])
    assert decimal_text(facts["available_budget_amount"]) == 48800


def test_hotel_denominator_is_verified_or_explicitly_unknown(baseline):
    case = baseline.cases["employee/hotel_two_nights.json"]
    amount = decimal_text(case["transaction"]["requested_amount"])
    facts = case["expected_facts"]
    source_id = case["transaction"]["items"][0]["source_document_id"]
    source = next(d for d in baseline.references["documents"] if d["id"] == source_id)["facts"]
    nights = decimal_text(facts["eligible_nights"])
    assert nights == (date.fromisoformat(source["stay_to"]) - date.fromisoformat(source["stay_from"])).days == 2
    assert amount / nights == decimal_text(facts["amount_per_night"]) == 7500
    assert amount / nights < decimal_text(facts["allowance_amount"]) == 8000
    unknown = baseline.cases["employee/hotel_unknown_nights.json"]
    assert unknown["expected_facts"]["eligible_nights"] is None
    assert unknown["expected_facts"]["amount_per_night"] is None
    assert unknown["transaction"]["items"][0]["eligible_nights"] is None
    assert unknown["expected_facts"]["category_limit_status"] == "UNKNOWN"
    assert unknown["expected_decision"] == "REVIEW"


def test_three_meal_claim_operands_and_evidence(baseline):
    case = baseline.cases["employee/daily_meals.json"]
    tx, facts = case["transaction"], case["expected_facts"]
    history = [h for h in baseline.references["historical_transactions"] if h["id"] in tx["history_ids"]]
    assert len(history) == 2
    assert all(h["employee_id"] == tx["employee_id"] and h["category"] == tx["category"] and h["expense_date"] == tx["expense_date"] and h["local_timezone"] == tx["local_timezone"] for h in history)
    aggregate = sum(decimal_text(h["claimed_amount"]) for h in history) + decimal_text(tx["requested_amount"])
    assert aggregate == decimal_text(facts["daily_aggregate_amount"]) == 1800
    assert aggregate - decimal_text(facts["allowance_amount"]) == decimal_text(facts["excess_amount"]) == 300
    assert set(facts["claim_ids"]) == set(tx["history_ids"]) | {tx["id"]}
    assert set(facts["claim_ids"]) <= {ev["record_id"] for ev in case["expected_evidence"]}


@pytest.mark.parametrize("path,total,excess", [("employee/shared_within.json", 1200, 0), ("employee/shared_exceeded.json", 1400, 200)])
def test_shared_receipt_allocation_operands(baseline, path, total, excess):
    case = baseline.cases[path]
    allocations = case["transaction"]["receipt_allocations"]
    facts = case["expected_facts"]
    assert len({a["employee_id"] for a in allocations}) == 2
    assert len({a["source_document_id"] for a in allocations}) == 1
    assert [a["lifecycle"] for a in allocations] == ["CONSUMED", "PROPOSED"]
    assert sum(decimal_text(a["amount"]) for a in allocations) == decimal_text(facts["aggregate_allocated_amount"]) == total
    assert max(Decimal("0"), Decimal(total) - decimal_text(facts["eligible_receipt_amount"])) == decimal_text(facts["excess_amount"]) == excess
    assert {a["id"] for a in allocations} <= {ev["record_id"] for ev in case["expected_evidence"]}


def test_approval_actions_and_truthful_absence(baseline):
    for case in baseline.cases.values():
        tx = case["transaction"]
        assert all(a["state"] == "APPROVED" for a in tx["approvals"])
        assert [a["sequence"] for a in tx["approvals"]] == list(range(1, len(tx["approvals"]) + 1))
        missing = [r for r in tx["required_approval_roles"] if r not in {a["role"] for a in tx["approvals"]}]
        assert missing == case["expected_facts"]["missing_approval_roles"]
    case = baseline.cases["vendor/approval_pending.json"]
    evidence = case["expected_evidence"]
    assert [e["record_id"] for e in evidence if e["kind"] == "APPROVAL"] == [case["transaction"]["approvals"][0]["id"]]
    assert evidence[0]["kind"] == "TRANSACTION"
    assert evidence[0]["snapshot_id"] == case["reference_snapshot"]["id"]
    assert "No DEPARTMENT_HEAD" in evidence[0]["observed_value"]


@pytest.mark.parametrize("field,value", [
    ("branch", "UNKNOWN_BRANCH"), ("expected_decision", "APPROVED"),
    ("intended_test_ids", ["T43"]), ("intended_test_ids", ["T01", "T01"]),
    ("expected_rule_concepts", ["FAKE-999"]), ("synthetic", False),
    ("rationale", ""), ("preparation_status", "RULE PASSED"),
    ("reference_ids", ["50000000-0000-4000-8000-999999999999"]),
])
def test_invalid_golden_metadata_is_rejected(fixtures, field, value):
    fixtures.cases["vendor/clean.json"][field] = value
    with pytest.raises(FixtureError):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("field", ["expected_facts", "expected_evidence", "reference_snapshot", "rationale"])
def test_required_golden_fields(fixtures, field):
    del fixtures.cases["vendor/clean.json"][field]
    with pytest.raises(FixtureError, match="missing required"):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("field,value", [
    ("record_version", 2), ("field_path", "facts.does_not_exist"),
    ("kind", "APPROVAL"), ("record_id", "40000000-0000-4000-8000-999999999999"),
    ("legal_entity_id", "20000000-0000-4000-8000-000000000002"),
])
def test_invalid_evidence_relationships(fixtures, field, value):
    fixtures.cases["vendor/clean.json"]["expected_evidence"][1][field] = value
    with pytest.raises(FixtureError):
        validate_fixture_set(fixtures)


def test_snapshot_version_drift(fixtures):
    fixtures.cases["vendor/clean.json"]["reference_snapshot"]["records"][0]["record_version"] = 2
    with pytest.raises(FixtureError, match="snapshot version mismatch"):
        validate_fixture_set(fixtures)


def test_duplicate_case_id(fixtures):
    cases = list(fixtures.cases.values())
    cases[1]["case_id"] = cases[0]["case_id"]
    with pytest.raises(FixtureError, match="duplicate golden case ID"):
        validate_fixture_set(fixtures)


def test_duplicate_transaction_identity_across_cases(fixtures):
    fixtures.cases["vendor/paid_duplicate.json"]["transaction"]["id"] = fixtures.cases["vendor/clean.json"]["transaction"]["id"]
    with pytest.raises(FixtureError, match="duplicate stable ID"):
        validate_fixture_set(fixtures)


def test_missing_snapshot_dependency(fixtures):
    case = fixtures.cases["vendor/clean.json"]
    historical_source = fixtures.references["historical_transactions"][0]["source_document_id"]
    case["reference_ids"].remove(historical_source)
    case["reference_snapshot"]["records"] = [p for p in case["reference_snapshot"]["records"] if p["record_id"] != historical_source]
    with pytest.raises(FixtureError, match="lacks dependency root"):
        validate_fixture_set(fixtures)


@pytest.mark.parametrize("field,value", [("transaction_version", 2), ("actor_id", "51000000-0000-4000-8000-000000000001")])
def test_approval_binding_errors(fixtures, field, value):
    fixtures.cases["vendor/clean.json"]["transaction"]["approvals"][0][field] = value
    with pytest.raises(FixtureError):
        validate_fixture_set(fixtures)


def test_manifest_required_metadata(fixtures):
    del fixtures.manifest["cases"][0]["expected_decision"]
    with pytest.raises(FixtureError, match="missing required"):
        validate_fixture_set(fixtures)


def test_empty_invoice_lines_are_rejected(fixtures):
    fixtures.cases["vendor/clean.json"]["transaction"]["lines"] = []
    with pytest.raises(FixtureError, match="records required"):
        validate_fixture_set(fixtures)


def test_screening_state_cannot_replace_human_approval_state(fixtures):
    fixtures.cases["vendor/clean.json"]["transaction"]["approvals"][0]["state"] = "PASS"
    with pytest.raises(FixtureError, match="invalid human approval state"):
        validate_fixture_set(fixtures)


def test_receipt_share_lifecycle_is_explicit(fixtures):
    fixtures.cases["employee/shared_within.json"]["transaction"]["receipt_allocations"][0]["lifecycle"] = "PASS"
    with pytest.raises(FixtureError, match="receipt allocation lifecycle"):
        validate_fixture_set(fixtures)
