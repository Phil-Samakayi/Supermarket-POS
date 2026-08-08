"""ReturnedLineItem: one line of a SaleReturn.

Mirrors SalesLineItem exactly (same GRASP role: Information Expert for
its own subtotal), because a returned item's refund math is the same
shape as a sold item's charge math — quantity times a ProductDescription's
price.
"""
from __future__ import annotations

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription


class ReturnedLineItem:
    """
    GRASP: Information Expert for its own refund subtotal.

    Refund amount is computed from the *current* catalog price, not
    whatever was actually paid at the original sale (which may have
    included a since-removed discount) — this first Handle Returns
    slice deliberately doesn't link a return back to its original
    Sale. See ARCHITECTURE.md.
    """

    def __init__(self, description: ProductDescription, quantity: int) -> None:
        self._description = description
        self._quantity = quantity

    def get_subtotal(self) -> Money:
        return self._description.price.times(self._quantity)

    @property
    def description(self) -> ProductDescription:
        return self._description

    @property
    def quantity(self) -> int:
        return self._quantity
