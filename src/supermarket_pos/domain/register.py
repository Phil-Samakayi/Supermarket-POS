"""Register: GRASP Controller for the Process Sale system operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.cash_payment import CashPayment
from supermarket_pos.domain.product.product_catalog import ProductCatalog
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.sales.sale import Sale

if TYPE_CHECKING:
    from supermarket_pos.domain.store import Store


@dataclass(frozen=True)
class LineItemResult:
    """Value object returned to the UI layer after enter_item() -
    everything a checkout screen needs to refresh its display."""

    description: ProductDescription
    quantity: int
    running_total: Money


class Register:
    """
    GRASP: Controller for the system operations implied by UC1's SSDs
    (make_new_sale, enter_item, end_sale, make_cash_payment) — see
    docs/Supermarket_POS_UseCase_UML.docx, Section 4.

    Iteration-1: cash payment only. Iteration-2 will route payment
    through a PaymentServiceProxy that also supports mobile money and
    card, without changing the shape of this class's public methods.
    """

    def __init__(self, store: "Store", catalog: ProductCatalog) -> None:
        self._store = store
        self._catalog = catalog
        self._current_sale: Optional[Sale] = None

    def make_new_sale(self) -> None:
        self._current_sale = Sale()

    def enter_item(self, item_id: str, quantity: int) -> LineItemResult:
        description = self._catalog.get_product_description(item_id)
        self._current_sale.make_line_item(description, quantity)
        return LineItemResult(
            description=description,
            quantity=quantity,
            running_total=self._current_sale.get_total(),
        )

    def end_sale(self) -> Money:
        self._current_sale.become_complete()
        return self._current_sale.get_total()

    def make_cash_payment(self, amount_tendered: Money) -> Money:
        payment = CashPayment(amount_tendered)
        self._current_sale.make_payment(payment)
        self._store.log_completed_sale(self._current_sale)
        return self._current_sale.get_balance()

    @property
    def current_sale(self) -> Optional[Sale]:
        return self._current_sale
