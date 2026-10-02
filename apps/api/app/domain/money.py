"""Exact, immutable money without implicit currency conversion or rounding.

Inputs are finite Decimal, canonical ungrouped decimal text, or integers.
Floats, bools, and None are rejected. Currency checking is structural only;
three ASCII letters do not prove a currency is active or supported by policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import (
    MAX_EMAX,
    MIN_EMIN,
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    Inexact,
    InvalidOperation,
    Overflow,
    Rounded,
)
import re
from types import NotImplementedType


class CurrencyMismatchError(ValueError):
    """Two monetary values require different currencies; no FX is implied."""


def normalize_currency(currency: str) -> str:
    """Normalize exactly three ASCII letters; do not consult a registry."""
    if not isinstance(currency, str):
        raise TypeError("currency must be a three-letter string")
    if re.fullmatch(r"[A-Za-z]{3}", currency) is None:
        raise ValueError("currency must contain exactly three ASCII letters")
    return currency.upper()


def _decimal_amount(amount: Decimal | str | int) -> Decimal:
    if isinstance(amount, bool) or not isinstance(amount, (Decimal, str, int)):
        raise TypeError("amount must be Decimal, decimal text, or int; floats/bools/None are forbidden")
    if isinstance(amount, str) and re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", amount) is None:
        raise ValueError("amount text must be an ungrouped plain decimal without whitespace")
    value = amount if isinstance(amount, Decimal) else Decimal(amount)
    if not value.is_finite():
        raise ValueError("amount must be finite")
    return value


@dataclass(frozen=True, slots=True, init=False)
class Money:
    """A value, not an invoice eligibility check; negatives and explicit zero are valid.

    Decimal scale is preserved at construction. Addition/subtraction use enough
    precision for both operands plus a carry and trap any rounding, independent
    of the caller's ambient Decimal context. No minor-unit policy is assumed.
    """

    amount: Decimal
    currency: str

    def __init__(self, amount: Decimal | str | int, currency: str) -> None:
        object.__setattr__(self, "amount", _decimal_amount(amount))
        object.__setattr__(self, "currency", normalize_currency(currency))

    def _combine(self, other: Money, *, subtract: bool) -> Money:
        if self.currency != other.currency:
            raise CurrencyMismatchError(f"cannot combine {self.currency} and {other.currency}")
        left = self.amount.as_tuple()
        right = other.amount.as_tuple()
        exponent = min(int(left.exponent), int(right.exponent))
        precision = max(
            len(left.digits) + int(left.exponent) - exponent,
            len(right.digits) + int(right.exponent) - exponent,
        ) + 1
        context = Context(
            prec=precision,
            rounding=ROUND_HALF_EVEN,
            Emin=MIN_EMIN,
            Emax=MAX_EMAX,
            capitals=1,
            clamp=0,
            flags=[],
            traps=[InvalidOperation, Inexact, Rounded, Overflow],
        )
        result = context.subtract(self.amount, other.amount) if subtract else context.add(self.amount, other.amount)
        return Money(result, self.currency)

    def __add__(self, other: object) -> Money | NotImplementedType:
        if not isinstance(other, Money):
            return NotImplemented
        return self._combine(other, subtract=False)

    def __sub__(self, other: object) -> Money | NotImplementedType:
        if not isinstance(other, Money):
            return NotImplemented
        return self._combine(other, subtract=True)

    def to_dict(self) -> dict[str, str]:
        """JSON-ready plain decimal text; preserve fractional zeros without rounding."""
        return {"amount": format(self.amount, "f"), "currency": self.currency}
