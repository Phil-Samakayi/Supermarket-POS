"""OfflinePaymentCommand: GoF Command (Larman Ch.38, "Designing a
Transaction with the Command Pattern").

Larman's motivation for Command applies directly here: "functions such
as sorting, queueing, delaying, logging, or undoing" a request require
turning the request itself into an object rather than executing it
immediately. A deferred mobile money authorization is exactly that —
PaymentServiceProxy can't authorize it right now (the gateway is
unreachable), so it captures everything needed to retry later as a
Command, and hands it to an OfflineSyncQueue.
"""
from __future__ import annotations

from datetime import datetime

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter


class OfflinePaymentCommand:
    """A deferred authorization request, replayable via execute()."""

    def __init__(
        self,
        real_adapter: IPaymentGatewayAdapter,
        amount: Money,
        payer_reference: str,
        provider: str,
    ) -> None:
        self._real_adapter = real_adapter
        self._amount = amount
        self._payer_reference = payer_reference
        self._provider = provider
        self._queued_at = datetime.now()

    def execute(self) -> AuthorizationResult:
        """Retry the authorization against the real adapter. May raise
        GatewayUnavailableError again if still offline — the caller
        (OfflineSyncQueue.replay_all) is responsible for handling that."""
        return self._real_adapter.authorize(self._amount, self._payer_reference)

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def amount(self) -> Money:
        return self._amount

    @property
    def payer_reference(self) -> str:
        return self._payer_reference

    @property
    def queued_at(self) -> datetime:
        return self._queued_at
