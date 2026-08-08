"""CashRefund: money given back to the customer for a cash-refunded
SaleReturn.

Deliberately not a Payment subclass — a refund isn't tendered by the
customer (no "amount_tendered"/change-due concept applies), it's paid
out by the cashier. Reusing Payment's shape here would mean fields
that don't mean what their names say. This iteration's Handle Returns
slice is cash-only; electronic refunds (mobile money/card reversal,
which Larman's own casual-format use case text calls out explicitly:
"if the customer paid by credit... reimbursement... rejected... pay
them with cash") are a deliberate follow-up, not built here — see
ARCHITECTURE.md.
"""
from __future__ import annotations

from datetime import datetime

from supermarket_pos.domain.common.money import Money


class CashRefund:
    """Cash paid out to the customer for a completed SaleReturn."""

    def __init__(self, amount: Money) -> None:
        self._amount = amount
        self._date_time = datetime.now()

    @property
    def amount(self) -> Money:
        return self._amount

    @property
    def date_time(self) -> datetime:
        return self._date_time
