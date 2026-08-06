"""ElectronicPayment: common superclass for payment types that must be
authorized against an external gateway before they're valid.

GRASP: Polymorphism + "Do It Myself" (Larman Ch.35, "Handling Payments
with Polymorphism and Do It Myself"). Each subclass authorizes itself —
Register creates the payment and calls authorize() on it, rather than
Register (or Sale) containing conditional logic per payment type.

CashPayment stays a direct Payment subclass (unchanged from Iteration
1) since cash needs no external authorization at all.
"""
from __future__ import annotations

from typing import Optional

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter
from supermarket_pos.domain.payment.payment import Payment


class ElectronicPayment(Payment):
    """Abstract Payment that authorizes itself via an injected
    IPaymentGatewayAdapter (constructor-supplied by whoever creates the
    payment, i.e. Register, via PaymentGatewayFactory)."""

    def __init__(
        self,
        amount_tendered: Money,
        gateway_adapter: IPaymentGatewayAdapter,
        payer_reference: str,
    ) -> None:
        super().__init__(amount_tendered)
        self._gateway_adapter = gateway_adapter
        self._payer_reference = payer_reference
        self._authorization_result: Optional[AuthorizationResult] = None

    def authorize(self) -> AuthorizationResult:
        """Request authorization from this payment's gateway adapter.
        May raise GatewayUnavailableError (propagated, not caught here —
        that's the future PaymentServiceProxy's job)."""
        self._authorization_result = self._gateway_adapter.authorize(
            self.amount_tendered, self._payer_reference
        )
        return self._authorization_result

    @property
    def payer_reference(self) -> str:
        return self._payer_reference

    @property
    def authorization_result(self) -> Optional[AuthorizationResult]:
        return self._authorization_result
