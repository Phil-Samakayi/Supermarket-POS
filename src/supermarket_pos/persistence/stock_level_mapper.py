"""StockLevelMapper: the Database Mapper (Larman Ch.38.10) for
StockLevel.

Unlike CompletedSaleMapper/CompletedReturnMapper, this one fits
PersistenceFacade's symmetric {class: mapper} contract cleanly —
save() takes a StockLevel, get()/get_all() return StockLevel, exactly
like ProductDescriptionMapper. StockLevel has a natural key (item_id,
same as ProductDescription) and no relationships or polymorphism to
navigate around. It's registered in the same PersistenceFacade
alongside ProductDescriptionMapper (see sqlite_persistence_factory.py)
rather than getting its own standalone wiring function — the
asymmetry that justified keeping the sale/return mappers separate
simply doesn't apply here.
"""
from __future__ import annotations

from typing import List

from supermarket_pos.domain.inventory.stock_level import StockLevel
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


class StockLevelMapper:
    """Materializes/dematerializes StockLevel <-> the stock_levels
    table. All SQL for this entity lives here (Ch.38.15)."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._connection = connection.connection
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_levels (
                item_id TEXT PRIMARY KEY,
                quantity_on_hand INTEGER NOT NULL
            )
            """
        )
        self._connection.commit()

    def get(self, oid: OID) -> StockLevel:
        row = self._connection.execute(
            "SELECT item_id, quantity_on_hand FROM stock_levels WHERE item_id = ?",
            (oid.value,),
        ).fetchone()
        if row is None:
            raise ValueError(f"No stock level found for item_id {oid.value!r}")
        return self._to_domain(row)

    def get_all(self) -> List[StockLevel]:
        rows = self._connection.execute(
            "SELECT item_id, quantity_on_hand FROM stock_levels ORDER BY item_id"
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    def save(self, stock_level: StockLevel) -> OID:
        self._connection.execute(
            """
            INSERT INTO stock_levels (item_id, quantity_on_hand)
            VALUES (:item_id, :quantity_on_hand)
            ON CONFLICT(item_id) DO UPDATE SET quantity_on_hand = excluded.quantity_on_hand
            """,
            {"item_id": stock_level.item_id, "quantity_on_hand": stock_level.quantity_on_hand},
        )
        self._connection.commit()
        return OID(stock_level.item_id)

    def delete(self, oid: OID) -> None:
        self._connection.execute("DELETE FROM stock_levels WHERE item_id = ?", (oid.value,))
        self._connection.commit()

    @staticmethod
    def _to_domain(row) -> StockLevel:
        return StockLevel(item_id=row["item_id"], quantity_on_hand=row["quantity_on_hand"])
