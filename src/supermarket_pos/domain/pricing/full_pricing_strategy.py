"""FullPricingStrategy: the no-discount default pricing policy."""
from __future__ import annotations

from typing import TYPE_CHECKING

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.pricing.sale_pricing_strategy import ISalePricingStrategy

if TYPE_CHECKING:
    from supermarket_pos.domain.sales.sale import Sale


class FullPricingStrategy(ISalePricingStrategy):
    """
    No discount applied — the sale total is simply the sum of its
    line-item subtotals.

    This is Sale's default strategy, so existing behavior (and every
    Iteration-1 test) is unchanged when no strategy is supplied.
    """

    def get_total(self, sale: "Sale") -> Money:
        return sale.get_subtotal()
