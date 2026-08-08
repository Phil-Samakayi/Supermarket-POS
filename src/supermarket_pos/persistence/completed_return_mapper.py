"""CompletedReturnMapper: the Database Mapper (Larman Ch.38.10) for
completed return history.

Simpler than CompletedSaleMapper: this slice's refunds are cash-only,
so there's no payment-type dispatch to make. Line items are still a
one-to-many relationship, handled exactly per Ch.38.19 — an associative
table (completed_return_line_items) carrying a return_oid foreign key,
same shape as completed_sale_line_items.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.returns.sale_return import SaleReturn
from supermarket_pos.persistence.completed_return_record import (
    CompletedReturnLineItemRecord,
    CompletedReturnRecord,
)
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


class CompletedReturnMapper:
    """Persists completed returns as read-only historical records."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._connection = connection.connection
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS completed_returns (
                oid TEXT PRIMARY KEY,
                date_time TEXT NOT NULL,
                total_refund TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS completed_return_line_items (
                return_oid TEXT NOT NULL,
                item_id TEXT NOT NULL,
                description TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal TEXT NOT NULL,
                FOREIGN KEY (return_oid) REFERENCES completed_returns(oid)
            )
            """
        )
        self._connection.commit()

    def save(self, sale_return: SaleReturn) -> OID:
        """Persists a completed, refunded SaleReturn. Raises
        ValueError if the return has no refund yet — this mapper only
        ever runs via Store.log_completed_return(), which Register
        already only calls after make_cash_refund() attaches a
        CashRefund, so this guards an invariant, not a normal path."""
        if sale_return.refund is None:
            raise ValueError("Cannot save a return with no refund as completed history.")

        oid = OID(uuid.uuid4().hex)
        self._connection.execute(
            """
            INSERT INTO completed_returns (oid, date_time, total_refund)
            VALUES (:oid, :date_time, :total_refund)
            """,
            {
                "oid": oid.value,
                "date_time": sale_return.date_time.isoformat(),
                "total_refund": str(sale_return.get_total().amount),
            },
        )
        self._connection.executemany(
            """
            INSERT INTO completed_return_line_items
                (return_oid, item_id, description, quantity, subtotal)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    oid.value,
                    line_item.description.item_id,
                    line_item.description.description,
                    line_item.quantity,
                    str(line_item.get_subtotal().amount),
                )
                for line_item in sale_return.line_items
            ],
        )
        self._connection.commit()
        return oid

    def get(self, oid: OID) -> CompletedReturnRecord:
        row = self._connection.execute(
            "SELECT oid, date_time, total_refund FROM completed_returns WHERE oid = ?",
            (oid.value,),
        ).fetchone()
        if row is None:
            raise ValueError(f"No completed return found for OID {oid.value!r}")
        return self._to_record(row)

    def get_all(self) -> List[CompletedReturnRecord]:
        rows = self._connection.execute(
            "SELECT oid, date_time, total_refund FROM completed_returns ORDER BY date_time"
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def _to_record(self, row) -> CompletedReturnRecord:
        line_item_rows = self._connection.execute(
            """
            SELECT item_id, description, quantity, subtotal
            FROM completed_return_line_items WHERE return_oid = ?
            """,
            (row["oid"],),
        ).fetchall()
        line_items = tuple(
            CompletedReturnLineItemRecord(
                item_id=r["item_id"],
                description=r["description"],
                quantity=r["quantity"],
                subtotal=Money(r["subtotal"]),
            )
            for r in line_item_rows
        )
        return CompletedReturnRecord(
            oid=row["oid"],
            date_time=datetime.fromisoformat(row["date_time"]),
            total_refund=Money(row["total_refund"]),
            line_items=line_items,
        )
