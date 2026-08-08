"""CompletedSaleRecord: a read-only historical snapshot of a completed
Sale, as persisted for reporting.

This is deliberately NOT a reconstruction of the live Sale/Payment
object graph. Larman's Ch.38 doesn't cover mapping polymorphic
subtypes to tables at all (38.19 only addresses relationships, not
inheritance) — and more fundamentally, MobileMoneyPayment/CardPayment
hold a live IPaymentGatewayAdapter collaborator that has no meaningful
persisted form; there is nothing sensible to "reconstruct" there. What
a manager actually needs from sale history (Iteration 3's reporting
scope) is a receipt-shaped record: what was sold, what was paid, when
— not a resumable live transaction. See ARCHITECTURE.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from supermarket_pos.domain.common.money import Money


@dataclass(frozen=True)
class CompletedSaleLineItemRecord:
    item_id: str
    description: str
    quantity: int
    subtotal: Money


@dataclass(frozen=True)
class CompletedSaleRecord:
    """A completed sale as it will be read back for reporting."""

    oid: str
    date_time: datetime
    total: Money
    payment_method: str
    """e.g. "cash", "mtn", "airtel", "card" — see
    CompletedSaleMapper._payment_method_of()."""
    payment_reference: Optional[str]
    amount_tendered: Money
    change_due: Money
    line_items: Tuple[CompletedSaleLineItemRecord, ...]
