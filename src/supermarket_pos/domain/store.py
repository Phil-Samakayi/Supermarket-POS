"""Store: the root object created during the Start Up use case."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from supermarket_pos.domain.inventory.inventory_manager import InventoryManager
from supermarket_pos.domain.payment.gateway.offline_sync_queue import OfflineSyncReport
from supermarket_pos.domain.payment.gateway.payment_gateway_factory import PaymentGatewayFactory
from supermarket_pos.domain.product.product_catalog import ProductCatalog
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.register import Register
from supermarket_pos.persistence.completed_return_mapper import CompletedReturnMapper
from supermarket_pos.persistence.completed_return_record import CompletedReturnRecord
from supermarket_pos.persistence.completed_sale_mapper import CompletedSaleMapper
from supermarket_pos.persistence.completed_sale_record import CompletedSaleRecord
from supermarket_pos.persistence.persistence_facade import PersistenceFacade
from supermarket_pos.reporting.sales_report import SalesSummaryReport, TopSellingItemReportRow
from supermarket_pos.reporting.sales_report_generator import SalesReportGenerator
from supermarket_pos.reporting.stock_report import StockSummaryReport, build_stock_summary_report

if TYPE_CHECKING:
    from supermarket_pos.domain.returns.sale_return import SaleReturn
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

    Store also optionally accepts a CompletedSaleMapper. This is kept
    deliberately separate from `completed_sales` (which is this
    session's live Sale objects, in memory, reset on restart — used by
    Register/tests as before) — `sale_history()` is the durable,
    persisted, read-only view across all sessions, sourced as
    CompletedSaleRecord snapshots rather than resurrected Sale objects.
    See ARCHITECTURE.md for why those are intentionally not the same
    thing.
    """

    def __init__(
        self,
        name: str,
        address: str,
        payment_gateway_factory: Optional[PaymentGatewayFactory] = None,
        persistence_facade: Optional[PersistenceFacade] = None,
        sale_history_mapper: Optional[CompletedSaleMapper] = None,
        return_history_mapper: Optional[CompletedReturnMapper] = None,
    ) -> None:
        self._name = name
        self._address = address
        self._catalog = ProductCatalog()
        self._register = Register(self, self._catalog, payment_gateway_factory)
        self._completed_sales: list["Sale"] = []
        self._completed_returns: list["SaleReturn"] = []
        self._persistence_facade = persistence_facade
        self._sale_history_mapper = sale_history_mapper
        self._return_history_mapper = return_history_mapper
        self._report_generator = SalesReportGenerator()
        self._inventory_manager = InventoryManager(persistence_facade)

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
        if self._sale_history_mapper is not None:
            self._sale_history_mapper.save(sale)

    def sale_history(self) -> List[CompletedSaleRecord]:
        """Durable, persisted history of every completed sale ever
        logged through this mapper — this session and prior ones.
        Empty if this Store was built without a sale_history_mapper.
        Distinct from `completed_sales`: that's this session's live
        Sale objects only, and resets on restart."""
        if self._sale_history_mapper is None:
            return []
        return self._sale_history_mapper.get_all()

    def log_completed_return(self, sale_return: "SaleReturn") -> None:
        self._completed_returns.append(sale_return)
        if self._return_history_mapper is not None:
            self._return_history_mapper.save(sale_return)

    def return_history(self) -> List[CompletedReturnRecord]:
        """Mirrors sale_history() for Handle Returns — durable,
        persisted history across sessions, distinct from
        completed_returns (this session's live SaleReturn objects)."""
        if self._return_history_mapper is None:
            return []
        return self._return_history_mapper.get_all()

    def sync_offline_payments(self) -> OfflineSyncReport:
        """Replays every mobile money payment that was queued while
        its gateway was unreachable (PaymentServiceProxy, Larman
        Ch.35). Intended as a manager-triggered action ("try to
        reconnect now") — not called automatically, since Iteration 2
        has no scheduling/session layer yet to decide when."""
        return self._register.offline_queue.replay_all()

    def sales_summary_report(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> SalesSummaryReport:
        """Manager/Owner reporting (Reporting Technical Service
        partition, Larman Ch.13.6). Built entirely from persisted
        sale_history()/return_history() — empty if this Store has no
        history mappers wired up. ``start``/``end`` bound the report to
        a date range; omit either for unbounded."""
        return self._report_generator.summarize(
            self.sale_history(), self.return_history(), start, end
        )

    def top_selling_items(
        self,
        limit: int = 5,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[TopSellingItemReportRow]:
        """Items ranked by quantity sold, from persisted sale history."""
        return self._report_generator.top_selling_items(self.sale_history(), limit, start, end)

    def stock_summary_report(self, low_stock_threshold: int = 5) -> StockSummaryReport:
        """Manage Inventory's read side: one row per catalog product
        with its current on-hand quantity, flagged low-stock at or
        below the threshold. Closes the gap flagged when Reporting was
        first built — no quantity concept existed then."""
        return build_stock_summary_report(self._catalog, self._inventory_manager, low_stock_threshold)

    @property
    def catalog(self) -> ProductCatalog:
        return self._catalog

    @property
    def register(self) -> Register:
        return self._register

    @property
    def inventory(self) -> InventoryManager:
        return self._inventory_manager

    @property
    def completed_sales(self) -> tuple["Sale", ...]:
        return tuple(self._completed_sales)

    @property
    def completed_returns(self) -> tuple["SaleReturn", ...]:
        return tuple(self._completed_returns)

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address
