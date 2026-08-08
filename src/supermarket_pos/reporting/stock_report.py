"""Stock summary reporting.

Deliberately not a class like SalesReportGenerator — that class earns
its shape by aggregating many CompletedSaleRecord snapshots (summing,
grouping, ranking). A stock summary is a much simpler operation:
combine each catalog product with its current Inventory quantity and
flag anything at or below a threshold. A plain function is enough;
introducing a class here would be the same pattern-for-pattern's-sake
mistake already avoided once in this codebase for the SQLite wiring
functions. See ARCHITECTURE.md.

This also closes the gap flagged in the Reporting slice's memo: "stock
summaries" were explicitly deferred there because no quantity concept
existed yet. It exists now (domain/inventory/), so this report can be
built honestly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from supermarket_pos.domain.inventory.inventory_manager import InventoryManager
from supermarket_pos.domain.product.product_catalog import ProductCatalog


@dataclass(frozen=True)
class StockSummaryRow:
    item_id: str
    description: str
    quantity_on_hand: int
    is_low_stock: bool


@dataclass(frozen=True)
class StockSummaryReport:
    rows: Tuple[StockSummaryRow, ...]
    low_stock_threshold: int


def build_stock_summary_report(
    catalog: ProductCatalog, inventory_manager: InventoryManager, low_stock_threshold: int = 5
) -> StockSummaryReport:
    """One row per catalog product, in catalog order (by item_id).
    Products with no recorded stock level show a quantity of 0 and
    count as low stock, same as InventoryManager.get_stock_level()'s
    default. Takes InventoryManager (its public read API), not the
    Inventory collection it holds internally — Store shouldn't need to
    reach past the Controller to build this."""
    rows = tuple(
        StockSummaryRow(
            item_id=product.item_id,
            description=product.description,
            quantity_on_hand=inventory_manager.get_stock_level(product.item_id),
            is_low_stock=inventory_manager.get_stock_level(product.item_id) <= low_stock_threshold,
        )
        for product in catalog.all_products()
    )
    return StockSummaryReport(rows=rows, low_stock_threshold=low_stock_threshold)
