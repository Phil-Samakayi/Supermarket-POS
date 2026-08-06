"""Sale: the central domain class realizing UC1 (Process Sale)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from supermarket_pos.domain.common.money import Money, ZERO
from supermarket_pos.domain.payment.payment import Payment
from supermarket_pos.domain.pricing.full_pricing_strategy import FullPricingStrategy
from supermarket_pos.domain.pricing.sale_pricing_strategy import ISalePricingStrategy
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.sales.sales_line_item import SalesLineItem


class Sale:
    """
    GRASP: Creator of SalesLineItem (Domain Model: Sale "Contains" SalesLineItem).
    GRASP: Information Expert for the sale subtotal (delegates to each
    SalesLineItem, which is itself the Expert for its own subtotal).

    Iteration-2: pricing is delegated to an ISalePricingStrategy (GoF
    Strategy, Larman Ch.26). Sale defaults to FullPricingStrategy (no
    discount) so existing callers and Iteration-1 tests are unaffected;
    a different strategy can be supplied at construction time or swapped
    in later via set_pricing_strategy().
    """

    def __init__(self, pricing_strategy: Optional[ISalePricingStrategy] = None) -> None:
        self._date_time: datetime = datetime.now()
        self._line_items: list[SalesLineItem] = []
        self._complete: bool = False
        self._payment: Optional[Payment] = None
        self._pricing_strategy: ISalePricingStrategy = pricing_strategy or FullPricingStrategy()

    def make_line_item(self, description: ProductDescription, quantity: int) -> SalesLineItem:
        if self._complete:
            raise ValueError("Cannot add items to a completed sale.")
        line_item = SalesLineItem(description, quantity)
        self._line_items.append(line_item)
        return line_item

    def get_subtotal(self) -> Money:
        """Pre-discount sum of all line-item subtotals. GRASP: Information
        Expert — Sale owns the line items, so it alone can answer this."""
        total = ZERO
        for line_item in self._line_items:
            total = total.plus(line_item.get_subtotal())
        return total

    def get_total(self) -> Money:
        """The sale total under the current pricing strategy."""
        return self._pricing_strategy.get_total(self)

    def set_pricing_strategy(self, pricing_strategy: ISalePricingStrategy) -> None:
        self._pricing_strategy = pricing_strategy

    @property
    def pricing_strategy(self) -> ISalePricingStrategy:
        return self._pricing_strategy

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
