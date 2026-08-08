"""PaymentServiceProxy: GoF Proxy — specifically the Redirection/
Failover Proxy variant Larman walks through in Ch.35 ("Failover to
Local Services with a Proxy (GoF)").

The structural point of Proxy is that it implements the *same*
interface as the thing it stands in for, so a client sends it messages
"as though it was the actual external accounting service" (Larman's
own wording, describing the NextGen POS's equivalent problem). Here:
Register and Payment collaborate with whatever IPaymentGatewayAdapter
PaymentGatewayFactory hands them — they have no way to tell, and don't
need to, whether that's a raw adapter or one wrapped in this Proxy.

Larman's motivating quote for this pattern is exactly the project's
top-ranked risk: "retailers really don't want to stop making sales!"
On GatewayUnavailableError, instead of the sale failing outright, the
authorization request is queued to an OfflineSyncQueue (Command
pattern, Ch.38) for later replay, and a *pending* approval is returned
so the sale can complete now.

This trade-off is applied only to mobile money (see
PaymentGatewayFactory) — it does not apply to card payments, which
have no real-world equivalent of "trust now, verify later"; a card
gateway that can't be reached must simply fail the payment.
"""
from __future__ import annotations

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)
from supermarket_pos.domain.payment.gateway.offline_payment_command import OfflinePaymentCommand
from supermarket_pos.domain.payment.gateway.offline_sync_queue import OfflineSyncQueue
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter


class PaymentServiceProxy(IPaymentGatewayAdapter):
    """Stands in for a real IPaymentGatewayAdapter, failing over to
    an OfflineSyncQueue when the real gateway is unreachable."""

    def __init__(
        self,
        real_adapter: IPaymentGatewayAdapter,
        offline_queue: OfflineSyncQueue,
        provider: str,
    ) -> None:
        self._real_adapter = real_adapter
        self._offline_queue = offline_queue
        self._provider = provider

    def authorize(self, amount: Money, payer_reference: str) -> AuthorizationResult:
        try:
            return self._real_adapter.authorize(amount, payer_reference)
        except GatewayUnavailableError:
            command = OfflinePaymentCommand(
                self._real_adapter, amount, payer_reference, self._provider
            )
            self._offline_queue.enqueue(command)
            return AuthorizationResult(
                approved=True,
                reference=None,
                message=(
                    f"{self._provider} gateway unreachable — payment queued "
                    "for offline verification"
                ),
                pending=True,
            )

    @property
    def real_adapter(self) -> IPaymentGatewayAdapter:
        """Exposed for tests that need to reach the wrapped adapter
        (e.g. to toggle a Simulated*GatewayClient's connectivity).
        Not intended for production collaborators — they should only
        ever see this Proxy through the IPaymentGatewayAdapter
        interface."""
        return self._real_adapter
