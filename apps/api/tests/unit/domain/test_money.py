"""Exact inputs, context independence, and currency integrity."""

from dataclasses import FrozenInstanceError
from decimal import Decimal, Inexact, ROUND_DOWN, ROUND_UP, Rounded, localcontext
import json
import operator

import pytest

from app.domain.money import CurrencyMismatchError, Money, normalize_currency


@pytest.mark.parametrize("amount,expected", [
    (Decimal("118000.00"), Decimal("118000.00")),
    ("0.10000000000000000000000000001", Decimal("0.10000000000000000000000000001")),
    (100, Decimal(100)),
    (0, Decimal(0)),
    ("-10.50", Decimal("-10.50")),
    (".25", Decimal("0.25")),
])
def test_supported_input_is_exact(amount, expected):
    money = Money(amount, "INR")
    assert isinstance(money.amount, Decimal)
    assert money.amount.as_tuple() == expected.as_tuple()
    if isinstance(amount, Decimal):
        assert money.amount is amount


@pytest.mark.parametrize("amount", [0.1, 100.1, -0.0, float("nan"), float("inf"), True, False, None, object()])
def test_inexact_boolean_or_missing_inputs_cannot_become_money(amount):
    with pytest.raises(TypeError, match="amount must be"):
        Money(amount, "INR")


@pytest.mark.parametrize("amount", [Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_non_finite_decimal_is_rejected(amount):
    with pytest.raises(ValueError, match="finite"):
        Money(amount, "INR")


@pytest.mark.parametrize("amount", ["", " 100.00 ", "1,000.00", "1_000", "INR 10", "1e2", "NaN", "١٢.٣"])
def test_source_formatting_is_not_silently_guessed(amount):
    with pytest.raises(ValueError, match="plain decimal"):
        Money(amount, "INR")


@pytest.mark.parametrize("currency,expected", [("inr", "INR"), ("usd", "USD"), ("INR", "INR"), ("iNr", "INR"), ("zzz", "ZZZ")])
def test_currency_normalization_is_structural_only(currency, expected):
    assert normalize_currency(currency) == expected
    assert Money("1.00", currency).currency == expected


@pytest.mark.parametrize("currency", ["", "IN", "INDIA", "₹", "12A", " INR", "INR ", "éUR", "İNＲ"])
def test_malformed_currency_is_rejected(currency):
    with pytest.raises(ValueError, match="three ASCII letters"):
        Money("1.00", currency)


@pytest.mark.parametrize("currency", [None, 123, True])
def test_currency_is_mandatory_text(currency):
    with pytest.raises(TypeError, match="currency"):
        Money("1.00", currency)


def test_currency_argument_has_no_default():
    with pytest.raises(TypeError):
        Money("1.00")


def test_decimal_fraction_sum_has_no_binary_float_error():
    assert Money("0.1", "INR") + Money("0.2", "inr") == Money("0.3", "INR")


def test_same_currency_subtraction_preserves_exact_negative_result():
    assert Money("100.10", "INR") - Money("150.20", "INR") == Money("-50.10", "INR")


@pytest.mark.parametrize("operation", [operator.add, operator.sub])
def test_cross_currency_arithmetic_is_explicitly_rejected(operation):
    with pytest.raises(CurrencyMismatchError, match="INR and USD"):
        operation(Money("100", "INR"), Money("50", "USD"))


@pytest.mark.parametrize("operation", [operator.add, operator.sub])
@pytest.mark.parametrize("other", [1, Decimal("1"), 0.1, True, None])
def test_arithmetic_does_not_coerce_scalar_operands(operation, other):
    with pytest.raises(TypeError):
        operation(Money("1.00", "INR"), other)


def test_equality_accounts_for_currency_without_rounding_scale():
    assert Money("100.00", "inr") == Money(100, "INR")
    assert Money("100", "INR") != Money("100", "USD")
    assert Money("0.000001", "INR") != Money("0", "INR")
    assert Money("1", "INR") != Decimal("1")


@pytest.mark.parametrize("a,b", [
    ("0", "0"), ("0.1", "0.2"), ("-99.9900", "0.000001"),
    ("999999999999999999999999999999999.99999999", "0.00000001"),
    ("0.000000000000000000000000000001", "1000000000000000000000.0000"),
])
def test_add_then_subtract_restores_original_amount(a, b):
    original, delta = Money(a, "INR"), Money(b, "INR")
    assert (original + delta) - delta == original
    assert original + delta == delta + original


@pytest.mark.parametrize("rounding", [ROUND_DOWN, ROUND_UP])
def test_exact_arithmetic_ignores_restrictive_ambient_context(rounding):
    left = Money("99999999999999999999999999999.999999999", "INR")
    right = Money("0.000000001", "INR")
    with localcontext() as ambient:
        ambient.prec = 1
        ambient.Emax = 3
        ambient.Emin = -3
        ambient.rounding = rounding
        ambient.traps[Inexact] = True
        ambient.traps[Rounded] = True
        ambient.clear_flags()
        result = left + right
        assert result == Money("100000000000000000000000000000.000000000", "INR")
        assert result - right == left
        assert not any(ambient.flags.values())
        assert (ambient.prec, ambient.Emax, ambient.Emin, ambient.rounding) == (1, 3, -3, rounding)


@pytest.mark.parametrize("amount", [Decimal("118000.00"), Decimal("1E+3"), Decimal("1E-8"), Decimal("-0.00")])
def test_json_ready_amount_is_round_trip_decimal_text(amount):
    original = Money(amount, "INR")
    payload = json.loads(json.dumps(original.to_dict()))
    assert isinstance(payload["amount"], str)
    assert payload["currency"] == "INR"
    assert Money(**payload) == original


def test_serialization_preserves_fractional_zeros():
    assert Money("100.2300", "INR").to_dict() == {"amount": "100.2300", "currency": "INR"}


@pytest.mark.parametrize("field,value", [("amount", Decimal(0)), ("currency", "USD")])
def test_money_is_immutable(field, value):
    money = Money("100.00", "INR")
    with pytest.raises(FrozenInstanceError):
        setattr(money, field, value)
