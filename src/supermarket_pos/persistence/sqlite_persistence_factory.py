"""Wires up a PersistenceFacade backed by SQLite.

Deliberately a plain function, not a class-based Factory pattern —
unlike PaymentGatewayFactory (which resolves between several
runtime-selectable providers behind a Singleton), this is a one-time,
fixed wiring of "these mappers, this connection." A function is enough;
introducing a class here would be pattern-for-pattern's-sake rather
than solving a real variation point. See ARCHITECTURE.md.
"""
from __future__ import annotations

from supermarket_pos.domain.inventory.stock_level import StockLevel
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.persistence.persistence_facade import PersistenceFacade
from supermarket_pos.persistence.product_description_mapper import ProductDescriptionMapper
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection
from supermarket_pos.persistence.stock_level_mapper import StockLevelMapper


def build_sqlite_persistence_facade(db_path: str = "supermarket_pos.db") -> PersistenceFacade:
    """``db_path`` defaults to a real file so Store Start Up gets a
    durable catalog out of the box; pass ":memory:" for tests."""
    connection = SQLiteConnection(db_path)
    return PersistenceFacade(
        {
            ProductDescription: ProductDescriptionMapper(connection),
            StockLevel: StockLevelMapper(connection),
        }
    )
