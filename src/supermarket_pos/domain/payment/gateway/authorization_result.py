"""AuthorizationResult: the neutral, provider-independent outcome of a
payment gateway authorization request.

This is the shape every IPaymentGatewayAdapter must translate its
provider's raw response into — the point of the Adapter pattern (Larman
Ch.26, "Adapter (GoF)") is that nothing above the adapter (Payment,
Register) ever sees MTN's, Airtel's, or the card processor's actual
response format.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AuthorizationResult:
    """Immutable outcome of a gateway authorization attempt.

    ``pending`` distinguishes a *provisional* approval granted by
    PaymentServiceProxy while the real gateway is unreachable (queued
    for offline verification) from a normal, already-confirmed
    approval. Defaults to False so every Iteration-2a adapter and test
    that builds an AuthorizationResult without mentioning it is
    unaffected.
    """

    approved: bool
    reference: Optional[str]
    message: str
    pending: bool = False
