"""Raised when a gateway legitimately declines a payment (as opposed
to being unreachable — see GatewayUnavailableError). This is a normal
business outcome the Cashier reacts to by asking the Customer for an
alternate payment method (UC1 extensions 9a/9b: "System receives
payment denial")."""
from __future__ import annotations


class PaymentDeclinedError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
