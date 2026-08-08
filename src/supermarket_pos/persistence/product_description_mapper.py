"""ProductDescriptionMapper: the Database Mapper (Larman Ch.38.10) for
ProductDescription.

Every piece of SQL against the ``product_descriptions`` table lives in
this one class — Ch.38.15, "Consolidating and Hiding SQL Statements in
One Class". No other class in the codebase issues SQL for this entity.
ProductDescription itself (see domain/product/product_description.py)
has no idea this class exists.
"""
from __future__ import annotations

from typing import List

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


class ProductDescriptionMapper:
    """Materializes/dematerializes ProductDescription <-> the
    ``product_descriptions`` table. ``item_id`` doubles as both the
    domain's natural key and the table's primary key/OID value."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._connection = connection.connection
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_descriptions (
                item_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                price TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def get(self, oid: OID) -> ProductDescription:
        row = self._connection.execute(
            "SELECT item_id, description, price FROM product_descriptions WHERE item_id = ?",
            (oid.value,),
        ).fetchone()
        if row is None:
            raise ProductNotFoundError(oid.value)
        return self._to_domain(row)

    def get_all(self) -> List[ProductDescription]:
        rows = self._connection.execute(
            "SELECT item_id, description, price FROM product_descriptions ORDER BY item_id"
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    def save(self, description: ProductDescription) -> OID:
        """Upsert — save() is used for both first-time save and
        updates, matching how Store.add_product() already treats
        adding a product as idempotent (ProductCatalog.add_product()
        overwrites on a repeated item_id)."""
        self._connection.execute(
            """
            INSERT INTO product_descriptions (item_id, description, price)
            VALUES (:item_id, :description, :price)
            ON CONFLICT(item_id) DO UPDATE SET
                description = excluded.description,
                price = excluded.price
            """,
            {
                "item_id": description.item_id,
                "description": description.description,
                "price": str(description.price.amount),
            },
        )
        self._connection.commit()
        return OID(description.item_id)

    def delete(self, oid: OID) -> None:
        self._connection.execute(
            "DELETE FROM product_descriptions WHERE item_id = ?", (oid.value,)
        )
        self._connection.commit()

    @staticmethod
    def _to_domain(row) -> ProductDescription:
        return ProductDescription(
            item_id=row["item_id"],
            description=row["description"],
            price=Money(row["price"]),
        )
