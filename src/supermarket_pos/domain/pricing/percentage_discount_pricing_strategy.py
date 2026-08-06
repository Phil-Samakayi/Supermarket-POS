"""PercentageDiscountPricingStrategy: e.g. a storewide or senior-citizen
discount, applied as a flat percentage off the sale subtotal.

Mirrors the worked example in Larman Ch.26 ("Strategy (GoF)"), where a
percentage discount is one of several concrete SalePricingStrategy
implementations.
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Union

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.pricing.sale_pricing_strategy import ISalePricingStrategy

if TYPE_CHECKING:
    from supermarket_pos.domain.sales.sale import Sale

Numeric = Union[str, int, float, Decimal]


class PercentageDiscountPricingStrategy(ISalePricingStrategy):
    """Applies a flat percentage discount to the sale subtotal.

    ``percentage`` is a value between 0 and 100 inclusive, e.g. ``"10"``
    for 10% off. Rounding is delegated to Money (ROUND_HALF_UP, 2 dp).
    """

    def __init__(self, percentage: Numeric) -> None:
        value = Decimal(str(percentage))
        if not (Decimal("0") <= value <= Decimal("100")):
            raise ValueError("Discount percentage must be between 0 and 100.")
        self._percentage = value

    @property
    def percentage(self) -> Decimal:
        return self._percentage

    def get_total(self, sale: "Sale") -> Money:
        subtotal = sale.get_subtotal()
        retained_fraction = (Decimal("100") - self._percentage) / Decimal("100")
        return subtotal.times(retained_fraction)
