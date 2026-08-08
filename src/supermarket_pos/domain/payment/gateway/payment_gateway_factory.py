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

Iteration-2b: mobile money adapters are now wrapped in a
PaymentServiceProxy (GoF Proxy, Larman Ch.35) sharing one
OfflineSyncQueue, so an unreachable gateway defers the payment instead
of failing the sale outright. Register and Payment need no changes at
all to get this — they still just call authorize() on whatever this
factory hands them. Card payments are deliberately NOT proxied (see
PaymentServiceProxy's docstring for why).

Accessed as a singleton via ``get_instance()``, matching the book's
convention, but the class can also be instantiated directly (e.g. for
an isolated instance in a test) — each instance gets its own fresh
OfflineSyncQueue, so direct instantiation stays safe/isolated and
doesn't leak state between tests.
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
from supermarket_pos.domain.payment.gateway.offline_sync_queue import OfflineSyncQueue
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter
from supermarket_pos.domain.payment.gateway.payment_service_proxy import PaymentServiceProxy
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
        # to real HTTP clients means changing only these lines.
        self._offline_queue = OfflineSyncQueue()

        mtn_adapter = MTNMoMoAdapter(SimulatedMTNMoMoGatewayClient())
        airtel_adapter = AirtelMoneyAdapter(SimulatedAirtelMoneyGatewayClient())

        self._mobile_money_adapters: Dict[str, IPaymentGatewayAdapter] = {
            "mtn": PaymentServiceProxy(mtn_adapter, self._offline_queue, "mtn"),
            "airtel": PaymentServiceProxy(airtel_adapter, self._offline_queue, "airtel"),
        }
        # Deliberately NOT wrapped in a PaymentServiceProxy: card payments
        # require real-time authorization, with no offline equivalent.
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

    @property
    def offline_queue(self) -> OfflineSyncQueue:
        """The queue shared by every mobile money PaymentServiceProxy
        this factory has handed out. Replay it (e.g. via
        Store.sync_offline_payments()) once connectivity is believed
        to be restored."""
        return self._offline_queue
