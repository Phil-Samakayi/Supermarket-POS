"""PaymentGatewayFactory: GoF Factory + Singleton (Larman Ch.26,
"Factory" and "Singleton (GoF)").

Larman's own worked example (NextGen's ServicesFactory, Section 26.4)
faces the same problem: some object needs to decide which concrete
adapter to hand out, and that decision shouldn't live in the domain
Controller (Register), because Register creating
``MTNMoMoAdapter(SimulatedMTNMoMoGatewayClient())`` by hand would
couple it to every concrete adapter and client class that exists —
a Low Coupling / Protected Variations violation. Adding a fourth
provider later means editing this file only; Register and Payment are
untouched.

Accessed as a singleton via ``get_instance()``, matching the book's
convention, but the class can also be instantiated directly (e.g. for
an isolated instance in a test) since it holds no shared mutable
state that would make that unsafe.
"""
from __future__ import annotations

from typing import ClassVar, Dict, Optional

from supermarket_pos.domain.payment.gateway.airtel_money_adapter import (
    AirtelMoneyAdapter,
    SimulatedAirtelMoneyGatewayClient,
)
from supermarket_pos.domain.payment.gateway.card_processor_adapter import (
    CardProcessorAdapter,
    SimulatedCardProcessorGatewayClient,
)
from supermarket_pos.domain.payment.gateway.mtn_momo_adapter import (
    MTNMoMoAdapter,
    SimulatedMTNMoMoGatewayClient,
)
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter
from supermarket_pos.domain.payment.gateway.unknown_payment_provider_error import (
    UnknownPaymentProviderError,
)


class PaymentGatewayFactory:
    """Resolves mobile money provider names and card payments to the
    correct IPaymentGatewayAdapter instance."""

    _instance: ClassVar[Optional["PaymentGatewayFactory"]] = None

    @classmethod
    def get_instance(cls) -> "PaymentGatewayFactory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        # Wired to the Simulated*GatewayClient stand-ins for now. Swapping
        # to real HTTP clients means changing only these three lines.
        self._mobile_money_adapters: Dict[str, IPaymentGatewayAdapter] = {
            "mtn": MTNMoMoAdapter(SimulatedMTNMoMoGatewayClient()),
            "airtel": AirtelMoneyAdapter(SimulatedAirtelMoneyGatewayClient()),
        }
        self._card_adapter: IPaymentGatewayAdapter = CardProcessorAdapter(
            SimulatedCardProcessorGatewayClient()
        )

    def get_mobile_money_adapter(self, provider: str) -> IPaymentGatewayAdapter:
        key = provider.strip().lower()
        try:
            return self._mobile_money_adapters[key]
        except KeyError:
            raise UnknownPaymentProviderError(provider) from None

    def get_card_adapter(self) -> IPaymentGatewayAdapter:
        return self._card_adapter
