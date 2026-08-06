"""IPaymentGatewayAdapter: GoF Adapter (Larman Ch.26, "Adapter (GoF)").

The NextGen-POS case study in the book faces the identical problem with
tax calculators and credit authorizers: several third-party services,
each with a different wire format, that the domain layer must not be
coupled to. The book's solution is to convert each provider's interface
into one common interface via a resource Adapter — this is that
interface for MTN Mobile Money, Airtel Money, and card processing.

Concrete adapters (MTNMoMoAdapter, AirtelMoneyAdapter,
CardProcessorAdapter) are each responsible for translating between this
neutral shape and their provider's actual request/response format.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult


class IPaymentGatewayAdapter(ABC):
    """Common interface for all payment gateway adapters."""

    @abstractmethod
    def authorize(self, amount: Money, payer_reference: str) -> AuthorizationResult:
        """Request authorization for ``amount`` against ``payer_reference``
        (a phone number for mobile money, a card token for card payments).

        Returns an AuthorizationResult on a normal approve/decline
        response. Raises GatewayUnavailableError if the provider cannot
        be reached at all.
        """
        raise NotImplementedError
