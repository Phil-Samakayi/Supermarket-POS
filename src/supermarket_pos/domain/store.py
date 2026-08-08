"""Store: the root object created during the Start Up use case."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from supermarket_pos.domain.payment.gateway.offline_sync_queue import OfflineSyncReport
from supermarket_pos.domain.payment.gateway.payment_gateway_factory import PaymentGatewayFactory
from supermarket_pos.domain.product.product_catalog import ProductCatalog
from supermarket_pos.domain.register import Register

if TYPE_CHECKING:
    from supermarket_pos.domain.sales.sale import Sale


class Store:
    """
    GRASP: Creator of Register and ProductCatalog (Domain Model:
    Store "has" Register, Store "maintains" ProductCatalog).

    Created during the (implicit) Start Up use case; owns the
    completed-sales log used for reporting in a later iteration.
    """

    def __init__(
        self,
        name: str,
        address: str,
        payment_gateway_factory: Optional[PaymentGatewayFactory] = None,
    ) -> None:
        self._name = name
        self._address = address
        self._catalog = ProductCatalog()
        self._register = Register(self, self._catalog, payment_gateway_factory)
        self._completed_sales: list["Sale"] = []

    def log_completed_sale(self, sale: "Sale") -> None:
        self._completed_sales.append(sale)

    def sync_offline_payments(self) -> OfflineSyncReport:
        """Replays every mobile money payment that was queued while
        its gateway was unreachable (PaymentServiceProxy, Larman
        Ch.35). Intended as a manager-triggered action ("try to
        reconnect now") — not called automatically, since Iteration 2
        has no scheduling/session layer yet to decide when."""
        return self._register.offline_queue.replay_all()

    @property
    def catalog(self) -> ProductCatalog:
        return self._catalog

    @property
    def register(self) -> Register:
        return self._register

    @property
    def completed_sales(self) -> tuple["Sale", ...]:
        return tuple(self._completed_sales)

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address
