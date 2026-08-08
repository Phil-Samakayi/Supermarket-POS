"""A small, deterministic IPaymentGatewayAdapter test double used to
unit-test Proxy/Command/Queue behaviour without depending on any real
provider's simulated wire-format translation (that's covered
separately by the MTN/Airtel/card adapter test modules)."""
from __future__ import annotations

from typing import List, Optional

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter


class FlakyFakeAdapter(IPaymentGatewayAdapter):
    """Raises GatewayUnavailableError while ``online`` is False;
    otherwise returns whatever AuthorizationResult was queued up via
    ``queue_result`` (FIFO), or a default approval if none was queued."""

    def __init__(self, online: bool = True) -> None:
        self.online = online
        self._queued_results: List[AuthorizationResult] = []
        self.calls: List[tuple] = []

    def queue_result(self, result: AuthorizationResult) -> None:
        self._queued_results.append(result)

    def authorize(self, amount: Money, payer_reference: str) -> AuthorizationResult:
        self.calls.append((amount, payer_reference))
        if not self.online:
            raise GatewayUnavailableError("Fake", "simulated outage")
        if self._queued_results:
            return self._queued_results.pop(0)
        return AuthorizationResult(approved=True, reference="FAKE-REF", message="Approved")
