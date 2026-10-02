"""P0-03 test-only fixture integrity checks; never evaluate screening decisions.

JSON is the source of truth. This helper checks its declared structure, links,
versions and evidence. Arithmetic expectations are independently checked in
tests, not applied to new transactions by an application service.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
from uuid import UUID

from app.domain.evidence import EvidenceKind, EvidenceReference
from app.domain.money import Money, normalize_currency
from app.domain.states import ReviewApprovalState, RuleStatus, ScreeningDecision


ROOT = Path(__file__).resolve().parents[4]
BRANCHES = {"VENDOR_INVOICE", "EMPLOYEE_EXPENSE"}
REFERENCE_NAMES = (
    "tenants", "legal_entities", "cost_centers", "vendors", "employees",
    "purchase_orders", "goods_receipts", "expense_policies", "approval_policies",
    "budgets", "historical_transactions", "documents",
)
COMMON = {"id", "version", "synthetic", "tenant_id", "legal_entity_id"}
REQUIRED = {
    "tenants": {"id", "version", "synthetic", "name"},
    "legal_entities": {"id", "version", "synthetic", "tenant_id", "code", "name", "base_currency", "timezone"},
    "cost_centers": {"code", "department"},
    "vendors": {"legal_name", "aliases", "tax_identifier", "status", "approved_categories", "payment_account_token", "payment_account_version"},
    "employees": {"employee_number", "name", "status", "employment_from", "employment_to", "department", "cost_center_id", "manager_id", "grade", "country", "roles"},
    "purchase_orders": {"display_number", "vendor_id", "currency", "status", "category", "approved_ceiling_amount", "budget_id", "approval_policy_id", "lines"},
    "po_lines": {"po_id", "vendor_id", "description", "ordered_quantity", "uom", "unit_price", "currency", "tax_basis", "tax_rate", "budget_id", "tolerance"},
    "goods_receipts": {"display_number", "po_id", "received_date", "source_system", "source_version", "lines"},
    "grn_lines": {"goods_receipt_id", "po_id", "po_line_id", "received_quantity", "accepted_quantity", "returned_quantity", "reversed_quantity", "uom"},
    "expense_policies": {"policy_code", "label", "category", "currency", "allowance_amount", "unit", "dimensions", "receipt_required", "receipt_type", "local_timezone", "submission_window_days"},
    "approval_policies": {"policy_code", "label", "currency", "branches", "department", "cost_center_id", "bands", "separation_of_duties"},
    "budgets": {"code", "fiscal_period", "department", "cost_center_id", "project", "category", "covered_categories", "currency", "basis", "ledger"},
    "budget_ledger": {"entry_type", "amount", "currency"},
    "historical_transactions": {"branch", "currency", "lifecycle", "settlement_status", "source_document_id", "budget_id"},
    "matching_allocations": {"transaction_id", "po_id", "po_line_id", "grn_line_id", "quantity", "amount", "currency", "lifecycle"},
    "documents": {"source_type", "representation", "verification", "facts"},
    "cases": {"case_id", "branch", "preparation_status", "evaluation_at", "decision_mode", "transaction", "reference_ids", "reference_snapshot", "expected_facts", "expected_decision", "intended_test_ids", "expected_rule_concepts", "expected_reason_concepts", "expected_evidence", "rationale"},
    "transactions": {"branch", "submitter_id", "currency", "category", "submission_date", "budget_id", "cost_center_id", "approval_policy_id", "required_approval_roles", "history_ids", "approvals"},
    "invoice_lines": {"transaction_id", "po_id", "po_line_id", "grn_line_id", "quantity", "unit_price", "uom", "currency", "net_amount", "tax_rate", "tax_amount", "gross_amount"},
    "expense_items": {"transaction_id", "source_document_id", "category", "currency", "expense_date", "local_timezone", "claimed_amount", "receipt_total_amount", "eligible_nights", "company_paid_amount", "applied_advance_amount"},
    "approvals": {"transaction_id", "transaction_version", "approval_policy_id", "actor_id", "role", "sequence", "state", "approved_at"},
    "receipt_allocations": {"source_document_id", "employee_id", "amount", "currency", "lifecycle", "authorized_by_id", "rationale"},
    "snapshots": {"records", "description"},
}
LINKS = {
    "tenant_id": {"tenants"}, "legal_entity_id": {"legal_entities"},
    "vendor_id": {"vendors"}, "employee_id": {"employees"}, "manager_id": {"employees"},
    "submitter_id": {"employees"}, "actor_id": {"employees"}, "authorized_by_id": {"employees"},
    "cost_center_id": {"cost_centers"}, "po_id": {"purchase_orders"},
    "po_line_id": {"po_lines"}, "goods_receipt_id": {"goods_receipts"}, "grn_line_id": {"grn_lines"},
    "budget_id": {"budgets"}, "expense_policy_id": {"expense_policies"}, "approval_policy_id": {"approval_policies"},
    "source_document_id": {"documents"}, "document_id": {"documents"}, "snapshot_id": {"snapshots"},
    "transaction_id": {"transactions", "historical_transactions"},
    "owner_id": {"purchase_orders", "historical_transactions"},
    "record_id": None, "reference_ids": None, "history_ids": {"historical_transactions"}, "claim_ids": {"transactions", "historical_transactions"},
}
FINANCIAL = re.compile(r"(?:_amount|_quantity|_rate)$|^(amount|quantity|unit_price|tax_rate|eligible_nights|quantity_tolerance)$")
NULL_DECIMALS = {"eligible_nights", "amount_per_night", "upper_bound_amount"}
DATE_FIELDS = {"effective_from", "effective_to", "employment_from", "employment_to", "stay_from", "stay_to"}
KINDS = {
    "TRANSACTION": {"transactions"}, "DOCUMENT_FIELD": {"documents"},
    "MASTER_RECORD": {"vendors", "employees", "cost_centers"}, "PO_LINE": {"po_lines"},
    "GRN_LINE": {"grn_lines"}, "POLICY_CLAUSE": {"expense_policies", "approval_policies"},
    "APPROVAL": {"approvals"}, "BUDGET_LEDGER": {"budget_ledger"},
    "HISTORICAL_AGGREGATE": {"historical_transactions", "matching_allocations", "receipt_allocations"},
}


class FixtureError(ValueError):
    """Malformed fixture data; contains a field or record context."""


def require(condition, message):
    if not condition:
        raise FixtureError(message)


def uuid_text(value):
    try:
        parsed = UUID(value) if isinstance(value, str) else None
        require(parsed is not None and parsed.int != 0 and str(parsed) == value, f"invalid UUID: {value!r}")
    except (ValueError, AttributeError) as exc:
        raise FixtureError(f"invalid UUID: {value!r}") from exc
    return parsed


def decimal_text(value):
    require(isinstance(value, str), f"financial value must be decimal text: {value!r}")
    try:
        # Reuse the plain, finite decimal-text contract; no currency conversion.
        return Money(value, "INR").amount
    except (TypeError, ValueError) as exc:
        raise FixtureError(f"invalid decimal text: {value!r}") from exc


def required(obj, keys, where):
    require(isinstance(obj, dict), f"{where}: expected object")
    missing = keys - obj.keys()
    require(not missing, f"{where}: missing required fields {sorted(missing)}")


def positive_int(value, field):
    require(type(value) is int and value > 0, f"{field}: expected positive integer")


def iso_date(value):
    require(isinstance(value, str), f"invalid date: {value!r}")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise FixtureError(f"invalid date: {value!r}") from exc
    require(parsed.isoformat() == value, f"date must be YYYY-MM-DD: {value!r}")
    return parsed


def scalars(value, path="root"):
    """Inspect all nested JSON, including non-record config and expected facts."""
    require(not isinstance(value, float), f"{path}: JSON floats forbidden")
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if FINANCIAL.search(key) or key == "amount_per_night":
                if not (item is None and key in NULL_DECIMALS):
                    decimal_text(item)
            if key in {"currency", "base_currency"}:
                try:
                    require(normalize_currency(item) == item, f"{child}: currency must be uppercase")
                except (TypeError, ValueError) as exc:
                    raise FixtureError(f"{child}: invalid currency") from exc
                require(item == "INR", f"{child}: fixture set is INR-only; no FX data")
            if key in DATE_FIELDS or key.endswith("_date"):
                require(item is not None or key in {"employment_to", "stay_from", "stay_to"}, f"{child}: date cannot be null")
                if item is not None:
                    iso_date(item)
            if key in {"approved_at", "evaluation_at"}:
                require(isinstance(item, str) and item.endswith("Z"), f"{child}: expected UTC timestamp")
                try:
                    datetime.fromisoformat(item[:-1] + "+00:00")
                except ValueError as exc:
                    raise FixtureError(f"{child}: invalid timestamp") from exc
            if key in {"version", "record_version", "transaction_version", "sequence", "submission_window_days"}:
                positive_int(item, child)
            if key.endswith("_status") and key in {"category_limit_status", "allocation_status"}:
                require(item in {s.value for s in RuleStatus}, f"{child}: invalid expected rule status")
            require(key not in {"bank_account", "iban", "routing_number", "account_number", "payment_instructions"}, f"{child}: real payment fields prohibited")
            scalars(item, child)
    elif isinstance(value, list):
        for n, item in enumerate(value):
            scalars(item, f"{path}.{n}")


def collect(records, kind, index, parents, parent=None):
    for obj in records:
        required(obj, REQUIRED[kind] | (COMMON if kind not in {"tenants", "legal_entities"} else set()), kind)
        uuid_text(obj["id"])
        require(obj["id"] not in index, f"duplicate stable ID: {obj['id']}")
        require(obj["synthetic"] is True, f"{kind}: synthetic marker required")
        positive_int(obj["version"], "version")
        for field in REQUIRED[kind]:
            require(obj[field] is not None or field in {"employment_to", "manager_id", "eligible_nights"}, f"{kind}.{field}: required value cannot be null")
            if isinstance(obj[field], str):
                require(bool(obj[field].strip()), f"{kind}.{field}: required text cannot be blank")
        index[obj["id"]] = (kind, obj)
        parents[obj["id"]] = parent
        children = {"ledger": "budget_ledger", "allocations": "matching_allocations",
                    "items": "expense_items", "approvals": "approvals", "receipt_allocations": "receipt_allocations"}
        if "lines" in obj:
            children["lines"] = {"purchase_orders": "po_lines", "goods_receipts": "grn_lines", "transactions": "invoice_lines"}[kind]
        for field, child_kind in children.items():
            if field in obj:
                require(isinstance(obj[field], list), f"{kind}.{field}: expected list")
                if field in {"lines", "items", "ledger", "allocations"}:
                    require(bool(obj[field]), f"{kind}.{field}: records required")
                collect(obj[field], child_kind, index, parents, obj["id"])
        if kind == "cases":
            collect([obj["transaction"]], "transactions", index, parents, obj["id"])
            collect([obj["reference_snapshot"]], "snapshots", index, parents, obj["id"])


def link(owner, field, target_id, index):
    if target_id is None:
        require(field == "manager_id", f"{field}: missing reference")
        return None
    uuid_text(target_id)
    require(target_id in index, f"{field}: unresolved reference {target_id}")
    kind, target = index[target_id]
    require(LINKS[field] is None or kind in LINKS[field], f"{field}: wrong target kind {kind}")
    if kind == "tenants":
        require(owner["tenant_id"] == target_id, f"{field}: tenant mismatch")
    else:
        require(owner["tenant_id"] == target["tenant_id"], f"{field}: tenant mismatch")
        if kind == "legal_entities":
            require(owner["legal_entity_id"] == target_id, f"{field}: entity mismatch")
        else:
            require(owner["legal_entity_id"] == target["legal_entity_id"], f"{field}: entity mismatch")
    if "currency" in owner and "currency" in target:
        require(owner["currency"] == target["currency"], f"{field}: currency mismatch")
    return target


def nested_links(obj, owner, index):
    if isinstance(obj, dict):
        for field, value in obj.items():
            if field in LINKS:
                for target in value if isinstance(value, list) else [value]:
                    link(owner, field, target, index)
            elif field.endswith("_id") and field != "case_id":
                raise FixtureError(f"undeclared reference field {field}")
            nested_links(value, owner if "id" not in obj else obj, index)
    elif isinstance(obj, list):
        for value in obj:
            nested_links(value, owner, index)


def validate_records(index, parents):
    for rid, (kind, obj) in index.items():
        if kind == "tenants":
            continue
        if kind == "legal_entities":
            uuid_text(obj["tenant_id"])
            require(index.get(obj["tenant_id"], (None,))[0] == "tenants", "entity has missing tenant")
            continue
        nested_links(obj, obj, index)
        if "effective_from" in obj or "effective_to" in obj:
            required(obj, {"effective_from", "effective_to"}, kind)
            require(iso_date(obj["effective_from"]) < iso_date(obj["effective_to"]), f"{kind}: invalid effective date ordering")
        if parents[rid] is not None:
            parent = index[parents[rid]][1]
            require(obj["tenant_id"] == parent["tenant_id"] and obj["legal_entity_id"] == parent["legal_entity_id"], f"{kind}: parent scope mismatch")
            require(obj["version"] == parent["version"], f"{kind}: child version mismatch")
        if kind in {"employees", "budgets", "approval_policies"}:
            cc = index[obj["cost_center_id"]][1]
            require(obj["department"] == cc["department"], f"{kind}: cost center department mismatch")
        if kind == "employees":
            end = obj["employment_to"]
            require(end is None or iso_date(obj["employment_from"]) < iso_date(end), "invalid employment dates")
            visited = {rid}
            manager = obj["manager_id"]
            while manager is not None:
                require(manager not in visited, "employee manager cycle")
                visited.add(manager)
                manager = index[manager][1]["manager_id"]
        if kind == "po_lines":
            po = index[obj["po_id"]][1]
            require(obj["po_id"] == parents[rid], "PO line parent mismatch")
            require(all(obj[k] == po[k] for k in ("vendor_id", "budget_id", "currency")), "PO line vendor/budget/currency mismatch")
            required(obj["tolerance"], {"price_absolute_amount", "price_relative_rate", "quantity_tolerance", "operator"}, "tolerance")
            require(obj["tolerance"]["operator"] == "MAX", "unsupported fixture tolerance operator")
        if kind in {"grn_lines", "invoice_lines", "matching_allocations"}:
            po_line = index[obj["po_line_id"]][1]
            require(obj["po_id"] == po_line["po_id"], "PO/PO-line mismatch")
            if "grn_line_id" in obj:
                require(index[obj["grn_line_id"]][1]["po_line_id"] == obj["po_line_id"], "GRN/PO-line mismatch")
            if kind == "grn_lines":
                require(obj["goods_receipt_id"] == parents[rid], "GRN line parent mismatch")
                require(index[parents[rid]][1]["po_id"] == obj["po_id"], "GRN parent PO mismatch")
                require(obj["uom"] == po_line["uom"], "GRN UOM mismatch")
                received, accepted, returned, reversed_qty = [decimal_text(obj[f"{k}_quantity"]) for k in ("received", "accepted", "returned", "reversed")]
                require(0 <= returned + reversed_qty <= accepted <= received <= decimal_text(po_line["ordered_quantity"]), "incoherent GRN quantities")
        if kind in {"invoice_lines", "expense_items", "approvals", "matching_allocations"}:
            require(obj["transaction_id"] == parents[rid], f"{kind}: transaction parent mismatch")
        if kind == "matching_allocations":
            require(obj["lifecycle"] in {"CONSUMED", "RESERVED", "RELEASED", "REVERSED"}, "invalid matching allocation lifecycle")
            history = index[obj["transaction_id"]][1]
            expected = {"PAID": "CONSUMED", "ACTIVE": "RESERVED", "CANCELLED": "RELEASED", "REVERSED": "REVERSED"}
            require(obj["lifecycle"] == expected.get(history["lifecycle"]), "history/allocation lifecycle mismatch")
        if kind == "receipt_allocations":
            require(obj["lifecycle"] in {"CONSUMED", "PROPOSED"}, "invalid fixture receipt allocation lifecycle")
        if kind == "budget_ledger":
            require(obj["entry_type"] in {"ALLOCATION", "CONSUMPTION", "PO_COMMITMENT", "CLAIM_RESERVATION"}, "invalid budget entry type")
            if obj["entry_type"] != "ALLOCATION":
                required(obj, {"owner_id"}, "budget ledger")
                owner_kind, owner = index[obj["owner_id"]]
                require(owner_kind == ("purchase_orders" if obj["entry_type"] == "PO_COMMITMENT" else "historical_transactions"), "budget ledger owner kind mismatch")
                require(owner["budget_id"] == parents[rid], "budget ledger owner/budget mismatch")
        if kind == "approvals":
            require(obj["state"] in {s.value for s in ReviewApprovalState}, "invalid human approval state")
            tx = index[obj["transaction_id"]][1]
            require(obj["transaction_version"] == tx["version"], "approval transaction version mismatch")
            require(obj["approval_policy_id"] == tx["approval_policy_id"], "approval policy binding mismatch")
            require(obj["role"] in index[obj["actor_id"]][1]["roles"], "approval actor role mismatch")
            require(obj["actor_id"] not in {tx["submitter_id"], tx.get("employee_id")}, "synthetic self-approval")
        if kind in {"transactions", "historical_transactions"}:
            require(obj["branch"] in BRANCHES, "invalid branch")
            keys = {"vendor_id", "invoice_number", "invoice_date", "total_amount"} if obj["branch"] == "VENDOR_INVOICE" else {"employee_id", "category", "expense_date", "local_timezone"}
            if kind == "transactions":
                keys |= {"source_document_id", "po_id", "lines", "subtotal_amount", "tax_amount"} if obj["branch"] == "VENDOR_INVOICE" else {"requested_amount", "expense_policy_id", "items", "receipt_allocations", "country", "location", "department", "project", "business_purpose"}
            else:
                keys |= {"allocations"} if obj["branch"] == "VENDOR_INVOICE" else {"claimed_amount", "capacity_state", "expense_policy_id"}
                require(obj["lifecycle"] in {"PAID", "ACTIVE", "CANCELLED", "REVERSED"}, "invalid history lifecycle")
                require(obj["settlement_status"] in {"PAID", "PENDING", "NOT_PAYABLE"}, "invalid settlement status")
            required(obj, keys, kind)
            budget = index[obj["budget_id"]][1]
            if "category" in obj:
                require(obj["category"] in budget["covered_categories"], "budget category mismatch")
            if "cost_center_id" in obj:
                require(obj["cost_center_id"] == budget["cost_center_id"], "budget cost center mismatch")
            if kind == "transactions":
                transaction_date = obj["invoice_date"] if obj["branch"] == "VENDOR_INVOICE" else obj["expense_date"]
                approval_policy = index[obj["approval_policy_id"]][1]
                require(approval_policy["effective_from"] <= transaction_date < approval_policy["effective_to"], "declared approval policy outside effective period")
                if obj["branch"] == "EMPLOYEE_EXPENSE":
                    employee = index[obj["employee_id"]][1]
                    policy = index[obj["expense_policy_id"]][1]
                    require(obj["department"] == employee["department"] and obj["cost_center_id"] == employee["cost_center_id"], "claim employee cost center mismatch")
                    require(policy["category"] == obj["category"], "declared expense policy category mismatch")
                    require(policy["dimensions"] == {"grade": employee["grade"], "country": obj["country"], "location": obj["location"]}, "declared expense policy dimensions mismatch")
                    require(policy["effective_from"] <= transaction_date < policy["effective_to"], "declared expense policy outside effective period")
                else:
                    po = index[obj["po_id"]][1]
                    require(obj["vendor_id"] == po["vendor_id"] and obj["budget_id"] == po["budget_id"], "invoice PO/vendor/budget mismatch")
        if kind == "documents":
            require(obj["representation"] == "SYNTHETIC_JSON_FACTS_ONLY" and obj["verification"] == "ADJUDICATED_SYNTHETIC_FACTS", "document fixture must declare facts-only representation")
            require(obj["source_type"] in BRANCHES, "invalid source type")
            keys = {"invoice_number", "invoice_date", "quantity", "total_amount", "currency"} if obj["source_type"] == "VENDOR_INVOICE" else {"receipt_number", "expense_date", "receipt_total_amount", "currency", "eligible_nights", "receipt_type", "readable", "local_timezone"}
            required(obj["facts"], keys, "document facts")
        if kind == "vendors":
            require(obj["tax_identifier"].startswith("DEMO-NONREG-"), "tax identifier must be fictional")
            require(obj["payment_account_token"].startswith("DEMO-NONPAYABLE-"), "payment token must be nonpayable")


def validate_policies(references):
    for name in ("expense_policies", "approval_policies"):
        groups = {}
        applicable_groups = {}
        for policy in references[name]:
            require(policy["label"] == "DEMO / SYNTHETIC POLICY", "policy must be labeled demo")
            key = (policy["tenant_id"], policy["legal_entity_id"], policy["policy_code"])
            for prior in groups.setdefault(key, []):
                require(prior["version"] != policy["version"], "duplicate logical policy version")
                require(policy["effective_to"] <= prior["effective_from"] or prior["effective_to"] <= policy["effective_from"], "overlapping policy periods")
            groups[key].append(policy)
            dimensions = (policy["category"], json.dumps(policy["dimensions"], sort_keys=True)) if name == "expense_policies" else (policy["department"], policy["cost_center_id"])
            applicable_key = (policy["tenant_id"], policy["legal_entity_id"], policy["currency"], dimensions)
            for prior in applicable_groups.setdefault(applicable_key, []):
                require(policy["effective_to"] <= prior["effective_from"] or prior["effective_to"] <= policy["effective_from"], "overlapping applicable policy periods")
            applicable_groups[applicable_key].append(policy)
            if name == "expense_policies":
                required(policy["dimensions"], {"grade", "country", "location"}, "expense policy dimensions")
            else:
                require(policy["branches"] == ["VENDOR_INVOICE", "EMPLOYEE_EXPENSE"], "approval branches inconsistent")
                require(policy["separation_of_duties"] == {"claimant_may_approve": False, "submitter_may_approve": False}, "demo separation of duties inconsistent")
                require(isinstance(policy["bands"], list) and bool(policy["bands"]), "approval bands required")
                previous_upper = None
                for n, band in enumerate(policy["bands"]):
                    required(band, {"lower_bound_amount", "upper_bound_amount", "lower_inclusive", "upper_inclusive", "required_roles"}, "approval band")
                    low = decimal_text(band["lower_bound_amount"])
                    high = None if band["upper_bound_amount"] is None else decimal_text(band["upper_bound_amount"])
                    require(type(band["lower_inclusive"]) is bool and band["upper_inclusive"] is False, "bands must be half-open")
                    require(low == 0 and band["lower_inclusive"] is False if n == 0 else low == previous_upper and band["lower_inclusive"] is True, "approval band gap/overlap")
                    require(high is None and n == len(policy["bands"]) - 1 or high is not None and high > low, "invalid approval band limits")
                    require(isinstance(band["required_roles"], list) and bool(band["required_roles"]) and len(set(band["required_roles"])) == len(band["required_roles"]), "approval roles required/unique")
                    require(set(band["required_roles"]) <= {"MANAGER", "DEPARTMENT_HEAD", "DIRECTOR", "CFO"}, "unknown demo approval role")
                    previous_upper = high
                require(previous_upper is None, "last approval band must be unbounded")


def field_exists(obj, path):
    try:
        for part in path.split("."):
            obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    except (KeyError, IndexError, ValueError, TypeError):
        return False
    return True


def reference_targets(obj):
    if isinstance(obj, dict):
        for field, value in obj.items():
            if field in LINKS:
                yield from value if isinstance(value, list) else [value]
            yield from reference_targets(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from reference_targets(value)


@dataclass
class FixtureSet:
    references: dict
    cases: dict
    manifest: dict

    def normalized(self):
        return json.dumps(dict(references=self.references, cases=self.cases, manifest=self.manifest), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)

    def digest(self):
        return hashlib.sha256(self.normalized().encode("utf-8")).hexdigest()


def validate_fixture_set(fixtures, root=ROOT):
    require(set(fixtures.references) == set(REFERENCE_NAMES), "reference file set incomplete")
    ref_index, ref_parents = {}, {}
    for name, records in fixtures.references.items():
        require(isinstance(records, list) and bool(records), f"{name}: records required")
        scalars(records, name)
        for obj in records:
            if name not in {"tenants", "legal_entities"}:
                required(obj, {"effective_from", "effective_to"}, name)
        collect(records, name, ref_index, ref_parents)
    validate_records(ref_index, ref_parents)
    validate_policies(fixtures.references)
    ref_roots = {}
    for rid in ref_index:
        ancestor = rid
        while ref_parents[ancestor] is not None:
            ancestor = ref_parents[ancestor]
        ref_roots[rid] = ancestor
    catalog = set(re.findall(r"^\| (T\d{2}) \|", (root / "docs/test_coverage.md").read_text(), re.MULTILINE))
    require(catalog == {f"T{n:02}" for n in range(1, 43)}, "T01–T42 catalog incomplete")
    rule_catalog = set(re.findall(r"^\| ([A-Z]+-\d{3}) \|", (root / "docs/AP_Exception_Assistant_Codex_Spec.md").read_text(), re.MULTILINE))
    manifest = fixtures.manifest
    required(manifest, {"fixture_schema_version", "synthetic", "cases"}, "manifest")
    require(manifest["synthetic"] is True and manifest["fixture_schema_version"] == "p0-03-v1", "manifest markers invalid")
    require(isinstance(manifest["cases"], list) and bool(manifest["cases"]), "manifest cases required")
    for entry in manifest["cases"]:
        required(entry, {"path", "case_id", "branch", "expected_decision", "intended_test_ids"}, "manifest entry")
    require({entry["path"] for entry in manifest["cases"]} == set(fixtures.cases), "manifest/case file mismatch")
    require(len({entry["path"] for entry in manifest["cases"]}) == len(manifest["cases"]), "duplicate manifest path")
    global_ids, case_ids = set(ref_index), set()
    for entry in manifest["cases"]:
        required(entry, {"path", "case_id", "branch", "expected_decision", "intended_test_ids"}, "manifest entry")
        case = fixtures.cases[entry["path"]]
        scalars(case, entry["path"])
        local_index, local_parents = {}, {}
        collect([case], "cases", local_index, local_parents)
        require(not (set(local_index) & global_ids), "duplicate stable ID across cases/references")
        global_ids.update(local_index)
        require(case["case_id"] not in case_ids, "duplicate golden case ID")
        case_ids.add(case["case_id"])
        require(case["branch"] in BRANCHES and case["transaction"]["branch"] == case["branch"], "invalid/mismatched golden branch")
        require(Path(entry["path"]).parent.as_posix() == ("vendor" if case["branch"] == "VENDOR_INVOICE" else "employee"), "golden branch directory mismatch")
        require(case["expected_decision"] in {s.value for s in ScreeningDecision}, "invalid expected decision")
        require(case["preparation_status"] == "Fixture prepared; rule not yet implemented.", "golden readiness must remain data-only")
        require(case["decision_mode"] == "RULES_ONLY", "fixture has no model data")
        require(isinstance(case["intended_test_ids"], list) and bool(case["intended_test_ids"]) and len(set(case["intended_test_ids"])) == len(case["intended_test_ids"]), "intended test IDs required/unique")
        require(set(case["intended_test_ids"]) <= catalog, "golden references nonexistent intended test ID")
        require(bool(case["expected_rule_concepts"]) and set(case["expected_rule_concepts"]) <= rule_catalog, "unknown rule concept")
        require(bool(case["expected_reason_concepts"]) and isinstance(case["rationale"], str) and bool(case["rationale"].strip()), "reason/rationale required")
        require(all(entry[k] == case[k] for k in ("case_id", "branch", "expected_decision", "intended_test_ids")), "manifest metadata mismatch")
        index, parents = ref_index | local_index, ref_parents | local_parents
        # Validate local records against this case only; other golden cases cannot supply links.
        validate_records(index, parents)
        require(len(set(case["reference_ids"])) == len(case["reference_ids"]), "duplicate reference ID")
        for obj in [case] + [ref_index[r][1] for r in case["reference_ids"]]:
            for target_id in reference_targets(obj):
                if target_id in ref_index:
                    require(ref_roots[target_id] in case["reference_ids"], "reference snapshot lacks dependency root")
        pins = case["reference_snapshot"]["records"]
        require({p["record_id"] for p in pins} == set(case["reference_ids"]) and len(pins) == len(case["reference_ids"]), "snapshot reference set mismatch")
        for pin in pins:
            require(pin["record_id"] in ref_index, "snapshot pins nonexistent reference")
            require(pin["record_version"] == ref_index[pin["record_id"]][1]["version"], "snapshot version mismatch")
        require(bool(case["expected_evidence"]), "golden evidence required")
        for ev in case["expected_evidence"]:
            required(ev, {"kind", "record_id", "record_version", "tenant_id", "legal_entity_id", "field_path"}, "expected evidence")
            try:
                EvidenceReference(kind=EvidenceKind(ev["kind"]), record_id=uuid_text(ev["record_id"]),
                    record_version=ev["record_version"], tenant_id=uuid_text(ev["tenant_id"]), legal_entity_id=uuid_text(ev["legal_entity_id"]),
                    field_path=ev["field_path"], observed_value=ev.get("observed_value"),
                    document_id=uuid_text(ev["document_id"]) if ev.get("document_id") is not None else None,
                    snapshot_id=uuid_text(ev["snapshot_id"]) if ev.get("snapshot_id") is not None else None)
            except (TypeError, ValueError) as exc:
                raise FixtureError(f"invalid evidence contract: {exc}") from exc
            target_kind, target = index[ev["record_id"]]
            require(target_kind in KINDS.get(ev["kind"], set()), "evidence kind/target mismatch")
            require(ev["record_version"] == target["version"], "evidence version mismatch")
            require(field_exists(target, ev["field_path"]), "evidence field path missing")
            if ev["kind"] == "DOCUMENT_FIELD":
                require(ev.get("document_id") == ev["record_id"], "document evidence identity mismatch")


def _no_float(text):
    raise FixtureError(f"JSON floats/constants forbidden: {text}")


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), parse_float=_no_float, parse_constant=_no_float, object_pairs_hook=_unique_keys)


def load_fixture_set(root=ROOT):
    directory = root / "data/synthetic/reference"
    require({p.stem for p in directory.glob("*.json")} == set(REFERENCE_NAMES), "reference file set incomplete/unexpected")
    references = {}
    for name in REFERENCE_NAMES:
        envelope = read_json(directory / f"{name}.json")
        required(envelope, {"fixture_schema_version", "synthetic", "source_system", "records"}, name)
        require(envelope["synthetic"] is True and envelope["fixture_schema_version"] == "p0-03-v1" and envelope["source_system"] == "SYNTHETIC_JSON", "reference envelope markers invalid")
        scalars(envelope, name)
        references[name] = envelope["records"]
    golden = root / "data/golden_cases"
    manifest = read_json(golden / "manifest.json")
    required(manifest, {"cases"}, "manifest")
    cases = {}
    for entry in manifest["cases"]:
        required(entry, {"path"}, "manifest entry")
        path = Path(entry["path"])
        require(path.parent.as_posix() in {"vendor", "employee"} and path.suffix == ".json" and len(path.parts) == 2, "unsafe/unexpected manifest path")
        require(entry["path"] not in cases, "duplicate manifest path")
        cases[entry["path"]] = read_json(golden / path)
    require({p.relative_to(golden).as_posix() for branch in ("vendor", "employee") for p in (golden / branch).glob("*.json")} == set(cases), "unlisted/missing golden file")
    fixtures = FixtureSet(references, cases, manifest)
    validate_fixture_set(fixtures, root)
    return fixtures
