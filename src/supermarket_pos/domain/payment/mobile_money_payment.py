"""MobileMoneyPayment: an ElectronicPayment made via a mobile money
provider (MTN, Airtel, ...)."""
from __future__ import annotations

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.electronic_payment import ElectronicPayment
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter


class MobileMoneyPayment(ElectronicPayment):
    """A payment tendered via mobile money.

    ``payer_reference`` is the payer's phone number; ``provider`` is
    the human-readable provider name (e.g. "mtn"), kept only for
    receipts/logging — the adapter itself was already selected by
    PaymentGatewayFactory before this payment was constructed.
    """

    def __init__(
        self,
        amount_tendered: Money,
        gateway_adapter: IPaymentGatewayAdapter,
        phone_number: str,
        provider: str,
    ) -> None:
        super().__init__(amount_tendered, gateway_adapter, phone_number)
        self._provider = provider

    @property
    def provider(self) -> str:
        return self._provider
