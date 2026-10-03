"""Untrusted structured intake. Authority, scope and approvals are never accepted."""
import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator


def decimal_text(value):
    if not isinstance(value, str) or not re.fullmatch(r'-?(?:0|[1-9][0-9]{0,13})(?:\.[0-9]{1,6})?', value):
        raise ValueError('Use a finite ungrouped decimal string with at most 14 integer and 6 fractional digits.')
    Decimal(value)  # validated, never converted through float
    return value


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Use an explicit ISO date YYYY-MM-DD.')
    date.fromisoformat(value)
    return value


Amount = Annotated[str, BeforeValidator(decimal_text)]
ISODate = Annotated[str, BeforeValidator(iso_date)]


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_max_length=500)


class Line(Strict):
    id: UUID | None = None
    contract_line_id: UUID | None = None
    service_acceptance_id: UUID | None = None
    po_line_id: UUID | None = None
    grn_line_id: UUID | None = None
    quantity: Amount | None = None
    unit_price: Amount | None = None
    discount_amount: Amount | None = None
    net_amount: Amount | None = None
    tax_rate: Amount | None = None
    tax_amount: Amount | None = None
    gross_amount: Amount | None = None
    currency: str | None = None
    uom: str | None = None


class ExpenseItem(Strict):
    id: UUID | None = None
    source_document_id: UUID | None = None
    category: str | None = None
    currency: str | None = None
    expense_date: ISODate | None = None
    local_timezone: str | None = None
    claimed_amount: Amount | None = None
    receipt_total_amount: Amount | None = None
    eligible_nights: Amount | None = None
    eligible_business_amount: Amount | None = None
    company_paid_amount: Amount | None = None
    applied_advance_amount: Amount | None = None


class Canonical(Strict):
    branch: Literal['VENDOR_INVOICE', 'EMPLOYEE_EXPENSE']
    document_type: Literal['ORDINARY', 'CREDIT_NOTE', 'REFUND'] = 'ORDINARY'
    vendor_id: UUID | None = None
    employee_id: UUID | None = None
    invoice_number: str | None = Field(None, max_length=160)
    claim_number: str | None = Field(None, max_length=160)
    invoice_date: ISODate | None = None
    expense_date: ISODate | None = None
    submission_date: ISODate | None = None
    currency: str | None = None
    category: str | None = None
    source_document_id: UUID | None = None
    payment_account_token: str | None = None  # synthetic equality token; never a bank-master update
    contract_id: UUID | None = None
    service_from: ISODate | None = None
    service_to: ISODate | None = None
    fiscal_period: str | None = None
    merchant: str | None = None
    receipt_number: str | None = None
    attendees: list[str] = Field(default_factory=list,max_length=100)
    travel_class: str | None = None
    po_id: UUID | None = None
    budget_id: UUID | None = None
    cost_center_id: UUID | None = None
    approval_policy_id: UUID | None = None
    expense_policy_id: UUID | None = None
    subtotal_amount: Amount | None = None
    tax_amount: Amount | None = None
    total_amount: Amount | None = None
    requested_amount: Amount | None = None
    document_discount_amount: Amount | None = None
    shipping_amount: Amount | None = None
    other_charges_amount: Amount | None = None
    tax_basis: str | None = None
    local_timezone: str | None = None
    department: str | None = None
    project: str | None = None
    country: str | None = None
    location: str | None = None
    business_purpose: str | None = None
    trip_reference: str | None = None
    lines: list[Line] = Field(default_factory=list, max_length=200)
    items: list[ExpenseItem] = Field(default_factory=list, max_length=200)

    @model_validator(mode='after')
    def branch_items(self):
        if (self.branch=='VENDOR_INVOICE' and self.items) or (self.branch=='EMPLOYEE_EXPENSE' and self.lines):
            raise ValueError('Line/item collection must match the branch.')
        for collection in (self.lines,self.items):
            ids=[item.id for item in collection if item.id]
            if len(ids)!=len(set(ids)):raise ValueError('Item UUIDs must be unique within the transaction.')
        return self

    @field_validator('currency')
    @classmethod
    def currency_code(cls, value):
        if value is not None:
            value = value.strip().upper()
            if not re.fullmatch('[A-Z]{3}', value):
                raise ValueError('Use a three-letter ASCII currency.')
        return value


class Revision(Strict):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)
    transaction: Canonical


class EvaluationRequest(Strict):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)


def fixture_canonical(transaction):
    """Trusted seed conversion removes fixture authority fields before ordinary validation."""
    data = {k: v for k, v in transaction.items() if k in Canonical.model_fields}
    for name, schema in [('lines', Line), ('items', ExpenseItem)]:
        data[name] = [{k: v for k, v in r.items() if k in schema.model_fields} for r in transaction.get(name, [])]
    for line in data.get('lines', []):
        line['discount_amount'] = '0.00'  # explicit fixture convention, not a general intake default
    return Canonical.model_validate(data).model_dump(mode='json')
