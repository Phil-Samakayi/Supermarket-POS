"""SalesLineItem: one line of a Sale."""
from __future__ import annotations

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription


class SalesLineItem:
    """
    GRASP: Information Expert for its own subtotal (it knows its
    quantity and its ProductDescription's price).
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
