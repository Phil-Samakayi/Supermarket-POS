"""Sale: the central domain class realizing UC1 (Process Sale)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from supermarket_pos.domain.common.money import Money, ZERO
from supermarket_pos.domain.payment.payment import Payment
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.sales.sales_line_item import SalesLineItem


class Sale:
    """
    GRASP: Creator of SalesLineItem (Domain Model: Sale "Contains" SalesLineItem).
    GRASP: Information Expert for the sale total (delegates to each
    SalesLineItem, which is itself the Expert for its own subtotal).

    Iteration-1 scope: cash payment only, no pricing strategy or tax.
    Iteration-2 will introduce an ISalePricingStrategy (Strategy pattern)
    in place of the plain get_total() summation, without changing this
    class's public interface.
    """

    def __init__(self) -> None:
        self._date_time: datetime = datetime.now()
        self._line_items: list[SalesLineItem] = []
        self._complete: bool = False
        self._payment: Optional[Payment] = None

    def make_line_item(self, description: ProductDescription, quantity: int) -> SalesLineItem:
        if self._complete:
            raise ValueError("Cannot add items to a completed sale.")
        line_item = SalesLineItem(description, quantity)
        self._line_items.append(line_item)
        return line_item

    def get_total(self) -> Money:
        total = ZERO
        for line_item in self._line_items:
            total = total.plus(line_item.get_subtotal())
        return total

    def become_complete(self) -> None:
        self._complete = True

    def is_complete(self) -> bool:
        return self._complete

    def make_payment(self, payment: Payment) -> None:
        if not self._complete:
            raise ValueError("Cannot take payment before the sale is complete.")
        self._payment = payment

    def get_balance(self) -> Money:
        """Change due (positive) once paid; remaining total owed if unpaid."""
        if self._payment is None:
            return self.get_total()
        return self._payment.amount_tendered.minus(self.get_total())

    @property
    def payment(self) -> Optional[Payment]:
        return self._payment

    @property
    def line_items(self) -> tuple[SalesLineItem, ...]:
        return tuple(self._line_items)

    @property
    def date_time(self) -> datetime:
        return self._date_time
