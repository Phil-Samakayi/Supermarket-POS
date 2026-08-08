"""CompletedSaleMapper: the Database Mapper (Larman Ch.38.10) for
completed sale history.

Deliberately NOT shaped like ProductDescriptionMapper's symmetric
IMapper[T] (get returns what save() took). save() takes a live domain
Sale; get()/get_all() return CompletedSaleRecord — a persisted
snapshot, not a resurrected Sale. Forcing symmetry here would be
worse design than admitting the asymmetry; see
completed_sale_record.py and ARCHITECTURE.md for why.

Line items are a one-to-many relationship off Sale, represented per
Ch.38.19 ("How to Represent Relationships in Tables") exactly as the
book prescribes for one-to-many: "create an associative table that
records the OIDs of each object in relationship" —
completed_sale_line_items carries a sale_oid foreign key.

Payment is polymorphic (CashPayment / MobileMoneyPayment /
CardPayment), which Larman's Ch.38 never actually addresses — 38.19
covers relationships, not inheritance. The isinstance dispatch below
is a small, explicit, honestly-scoped answer to a question the book
doesn't answer, confined entirely to this one class (Ch.38.15 still
holds: all the SQL, and now this dispatch too, live in exactly one
place).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.card_payment import CardPayment
from supermarket_pos.domain.payment.cash_payment import CashPayment
from supermarket_pos.domain.payment.electronic_payment import ElectronicPayment
from supermarket_pos.domain.payment.mobile_money_payment import MobileMoneyPayment
from supermarket_pos.domain.payment.payment import Payment
from supermarket_pos.domain.sales.sale import Sale
from supermarket_pos.persistence.completed_sale_record import (
    CompletedSaleLineItemRecord,
    CompletedSaleRecord,
)
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


class CompletedSaleMapper:
    """Persists completed sales as read-only historical records."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._connection = connection.connection
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS completed_sales (
                oid TEXT PRIMARY KEY,
                date_time TEXT NOT NULL,
                total TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                payment_reference TEXT,
                amount_tendered TEXT NOT NULL,
                change_due TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS completed_sale_line_items (
                sale_oid TEXT NOT NULL,
                item_id TEXT NOT NULL,
                description TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal TEXT NOT NULL,
                FOREIGN KEY (sale_oid) REFERENCES completed_sales(oid)
            )
            """
        )
        self._connection.commit()

    def save(self, sale: Sale) -> OID:
        """Persists a completed, paid Sale as a historical snapshot.
        Raises ValueError if the sale has no payment yet — this mapper
        only ever runs via Store.log_completed_sale(), which Register
        already only calls after a successful payment, so this guards
        against a future caller skipping that invariant, not a normal
        code path."""
        payment = sale.payment
        if payment is None:
            raise ValueError("Cannot save a sale with no payment as completed history.")

        oid = OID(uuid.uuid4().hex)
        self._connection.execute(
            """
            INSERT INTO completed_sales
                (oid, date_time, total, payment_method, payment_reference,
                 amount_tendered, change_due)
            VALUES (:oid, :date_time, :total, :payment_method, :payment_reference,
                    :amount_tendered, :change_due)
            """,
            {
                "oid": oid.value,
                "date_time": sale.date_time.isoformat(),
                "total": str(sale.get_total().amount),
                "payment_method": self._payment_method_of(payment),
                "payment_reference": self._payment_reference_of(payment),
                "amount_tendered": str(payment.amount_tendered.amount),
                "change_due": str(sale.get_balance().amount),
            },
        )
        self._connection.executemany(
            """
            INSERT INTO completed_sale_line_items
                (sale_oid, item_id, description, quantity, subtotal)
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
                for line_item in sale.line_items
            ],
        )
        self._connection.commit()
        return oid

    def get(self, oid: OID) -> CompletedSaleRecord:
        row = self._connection.execute(
            """
            SELECT oid, date_time, total, payment_method, payment_reference,
                   amount_tendered, change_due
            FROM completed_sales WHERE oid = ?
            """,
            (oid.value,),
        ).fetchone()
        if row is None:
            raise ValueError(f"No completed sale found for OID {oid.value!r}")
        return self._to_record(row)

    def get_all(self) -> List[CompletedSaleRecord]:
        rows = self._connection.execute(
            """
            SELECT oid, date_time, total, payment_method, payment_reference,
                   amount_tendered, change_due
            FROM completed_sales ORDER BY date_time
            """
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def _to_record(self, row) -> CompletedSaleRecord:
        line_item_rows = self._connection.execute(
            """
            SELECT item_id, description, quantity, subtotal
            FROM completed_sale_line_items WHERE sale_oid = ?
            """,
            (row["oid"],),
        ).fetchall()
        line_items = tuple(
            CompletedSaleLineItemRecord(
                item_id=r["item_id"],
                description=r["description"],
                quantity=r["quantity"],
                subtotal=Money(r["subtotal"]),
            )
            for r in line_item_rows
        )
        return CompletedSaleRecord(
            oid=row["oid"],
            date_time=datetime.fromisoformat(row["date_time"]),
            total=Money(row["total"]),
            payment_method=row["payment_method"],
            payment_reference=row["payment_reference"],
            amount_tendered=Money(row["amount_tendered"]),
            change_due=Money(row["change_due"]),
            line_items=line_items,
        )

    @staticmethod
    def _payment_method_of(payment: Payment) -> str:
        if isinstance(payment, CashPayment):
            return "cash"
        if isinstance(payment, MobileMoneyPayment):
            return payment.provider
        if isinstance(payment, CardPayment):
            return "card"
        raise ValueError(f"Unrecognized payment type for persistence: {type(payment)!r}")

    @staticmethod
    def _payment_reference_of(payment: Payment) -> Optional[str]:
        if isinstance(payment, ElectronicPayment):
            return payment.payer_reference
        return None
