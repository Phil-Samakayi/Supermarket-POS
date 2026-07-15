"""Store: the root object created during the Start Up use case."""
from __future__ import annotations

from typing import TYPE_CHECKING

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

    def __init__(self, name: str, address: str) -> None:
        self._name = name
        self._address = address
        self._catalog = ProductCatalog()
        self._register = Register(self, self._catalog)
        self._completed_sales: list["Sale"] = []

    def log_completed_sale(self, sale: "Sale") -> None:
        self._completed_sales.append(sale)

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
