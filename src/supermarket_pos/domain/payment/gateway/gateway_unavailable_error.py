"""GatewayUnavailableError: a *technical* failure to reach the external
payment gateway (network/timeout), as distinct from a legitimate
business decline (insufficient funds, etc.).

Larman Ch.35 ("Handling Failure") is explicit about this distinction:
a declined payment is a normal business outcome the cashier reacts to
(ask for alternate payment); an unreachable gateway is a fault that a
future PaymentServiceProxy will catch and fail over to a local/offline
queue (Iteration-2's next slice). Keeping these as two different
exception types now means the Proxy work won't need to touch this
interface later.
"""
from __future__ import annotations


class GatewayUnavailableError(Exception):
    """Raised when a payment gateway adapter cannot reach its provider
    (as opposed to reaching it and receiving a decline)."""

    def __init__(self, provider_name: str, reason: str) -> None:
        super().__init__(f"{provider_name} gateway unavailable: {reason}")
        self.provider_name = provider_name
        self.reason = reason
