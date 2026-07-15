"""
Money value type.

Modeled as a Money "quantity" per Larman Ch.9 (Domain Models): quantities
with a unit should not be represented as a plain number. Money wraps
``decimal.Decimal`` rather than ``float`` to avoid rounding errors in
currency arithmetic. Amounts are Zambian Kwacha (ZMW) by convention.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from functools import total_ordering
from typing import Union

Numeric = Union[str, int, float, Decimal]


@total_ordering
class Money:
    """An immutable monetary amount."""

    __slots__ = ("_amount",)

    def __init__(self, amount: Numeric) -> None:
        self._amount: Decimal = Decimal(str(amount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def amount(self) -> Decimal:
        return self._amount

    def plus(self, other: "Money") -> "Money":
        return Money(self._amount + other._amount)

    def minus(self, other: "Money") -> "Money":
        return Money(self._amount - other._amount)

    def times(self, quantity: int) -> "Money":
        return Money(self._amount * quantity)

    def is_negative(self) -> bool:
        return self._amount < 0

    def __add__(self, other: "Money") -> "Money":
        return self.plus(other)

    def __sub__(self, other: "Money") -> "Money":
        return self.minus(other)

    def __mul__(self, quantity: int) -> "Money":
        return self.times(quantity)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Money) and self._amount == other._amount

    def __lt__(self, other: "Money") -> bool:
        return self._amount < other._amount

    def __hash__(self) -> int:
        return hash(self._amount)

    def __repr__(self) -> str:
        return f"Money('{self._amount}')"

    def __str__(self) -> str:
        return f"K{self._amount:.2f}"


ZERO = Money("0.00")
