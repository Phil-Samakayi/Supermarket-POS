"""CashPayment: Iteration-1's only Payment subtype."""
from __future__ import annotations

from supermarket_pos.domain.payment.payment import Payment


class CashPayment(Payment):
    """A payment tendered in cash. Requires no external authorization."""
