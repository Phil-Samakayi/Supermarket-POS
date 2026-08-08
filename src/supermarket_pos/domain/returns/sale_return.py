"""SaleReturn: the central domain class realizing Handle Returns.

Larman gives Handle Returns only as a casual-format use case (no
worked design in the book): "A customer arrives at a checkout with
items to return. The cashier uses the POS system to record each
returned item..." This class mirrors Sale's shape closely — same
GRASP roles (Creator of its line items, Information Expert for the
refund total) — because the structure of "record items, total them,
settle payment" is the same regardless of direction of money flow.

What's deliberately different from Sale: no pricing strategy (refunds
use current catalog price — see ReturnedLineItem), and no
change-due/get_balance() concept, since nothing is "tendered" in a
return the way cash is tendered in a sale.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from supermarket_pos.domain.common.money import Money, ZERO
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.returns.cash_refund import CashRefund
from supermarket_pos.domain.returns.returned_line_item import ReturnedLineItem


class SaleReturn:
    """
    GRASP: Creator of ReturnedLineItem. Information Expert for the
    refund total (delegates to each ReturnedLineItem for its own
    subtotal, exactly as Sale does for SalesLineItem).
    """

    def __init__(self) -> None:
        self._date_time: datetime = datetime.now()
        self._line_items: list[ReturnedLineItem] = []
        self._complete: bool = False
        self._refund: Optional[CashRefund] = None

    def make_line_item(self, description: ProductDescription, quantity: int) -> ReturnedLineItem:
        if self._complete:
            raise ValueError("Cannot add items to a completed return.")
        line_item = ReturnedLineItem(description, quantity)
        self._line_items.append(line_item)
        return line_item

    def get_total(self) -> Money:
        """Total refund due across all returned line items."""
        total = ZERO
        for line_item in self._line_items:
            total = total.plus(line_item.get_subtotal())
        return total

    def become_complete(self) -> None:
        if not self._line_items:
            raise ValueError("Cannot complete a return with no items.")
        self._complete = True

    def is_complete(self) -> bool:
        return self._complete

    def make_refund(self, refund: CashRefund) -> None:
        if not self._complete:
            raise ValueError("Cannot issue a refund before the return is complete.")
        self._refund = refund

    @property
    def refund(self) -> Optional[CashRefund]:
        return self._refund

    @property
    def line_items(self) -> tuple[ReturnedLineItem, ...]:
        return tuple(self._line_items)

    @property
    def date_time(self) -> datetime:
        return self._date_time
