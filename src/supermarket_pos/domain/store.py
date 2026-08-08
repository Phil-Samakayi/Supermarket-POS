"""Store: the root object created during the Start Up use case."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from supermarket_pos.domain.payment.gateway.offline_sync_queue import OfflineSyncReport
from supermarket_pos.domain.payment.gateway.payment_gateway_factory import PaymentGatewayFactory
from supermarket_pos.domain.product.product_catalog import ProductCatalog
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.register import Register
from supermarket_pos.persistence.persistence_facade import PersistenceFacade

if TYPE_CHECKING:
    from supermarket_pos.domain.sales.sale import Sale


class Store:
    """
    GRASP: Creator of Register and ProductCatalog (Domain Model:
    Store "has" Register, Store "maintains" ProductCatalog).

    Created during the (implicit) Start Up use case; owns the
    completed-sales log used for reporting in a later iteration.

    Iteration-3: Store optionally accepts a PersistenceFacade (Larman
    Ch.38.9). If given, Start Up loads every previously-saved
    ProductDescription into the catalog, and add_product() persists
    new ones. ProductCatalog and ProductDescription themselves are
    completely unaware this happens — per Larman's own argument in
    Ch.17 (Information Expert contraindications) and Ch.38.10 against
    a persistent object saving itself, Store is the coordinator here,
    not the domain objects. Without a facade (the default), Store
    behaves exactly as in Iterations 1-2: pure in-memory catalog.
    """

    def __init__(
        self,
        name: str,
        address: str,
        payment_gateway_factory: Optional[PaymentGatewayFactory] = None,
        persistence_facade: Optional[PersistenceFacade] = None,
    ) -> None:
        self._name = name
        self._address = address
        self._catalog = ProductCatalog()
        self._register = Register(self, self._catalog, payment_gateway_factory)
        self._completed_sales: list["Sale"] = []
        self._persistence_facade = persistence_facade

        if self._persistence_facade is not None:
            for description in self._persistence_facade.get_all(ProductDescription):
                self._catalog.add_product(description)

    def add_product(self, description: ProductDescription) -> None:
        """Adds a product to the catalog and, if this Store was built
        with a PersistenceFacade, persists it too. Calling
        store.catalog.add_product() directly still works and stays
        in-memory-only — this method is the persistence-aware entry
        point, not a replacement for the domain method."""
        self._catalog.add_product(description)
        if self._persistence_facade is not None:
            self._persistence_facade.save(description)

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
