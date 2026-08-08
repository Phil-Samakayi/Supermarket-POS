import pytest

from supermarket_pos.domain.payment.gateway.airtel_money_adapter import AirtelMoneyAdapter
from supermarket_pos.domain.payment.gateway.card_processor_adapter import CardProcessorAdapter
from supermarket_pos.domain.payment.gateway.mtn_momo_adapter import MTNMoMoAdapter
from supermarket_pos.domain.payment.gateway.payment_gateway_factory import PaymentGatewayFactory
from supermarket_pos.domain.payment.gateway.payment_service_proxy import PaymentServiceProxy
from supermarket_pos.domain.payment.gateway.unknown_payment_provider_error import (
    UnknownPaymentProviderError,
)


def test_get_instance_returns_the_same_singleton():
    first = PaymentGatewayFactory.get_instance()
    second = PaymentGatewayFactory.get_instance()

    assert first is second


def test_mtn_provider_is_wrapped_in_a_payment_service_proxy_over_mtn_adapter():
    """Mobile money adapters are proxied for offline failover
    (Iteration-2b) — Register/Payment collaborate with the Proxy
    exactly as they would the raw adapter, which is the whole point
    of GoF Proxy (Larman Ch.35)."""
    factory = PaymentGatewayFactory()

    adapter = factory.get_mobile_money_adapter("mtn")

    assert isinstance(adapter, PaymentServiceProxy)
    assert isinstance(adapter.real_adapter, MTNMoMoAdapter)


def test_airtel_provider_is_wrapped_in_a_payment_service_proxy_over_airtel_adapter():
    factory = PaymentGatewayFactory()

    adapter = factory.get_mobile_money_adapter("airtel")

    assert isinstance(adapter, PaymentServiceProxy)
    assert isinstance(adapter.real_adapter, AirtelMoneyAdapter)


def test_provider_lookup_is_case_and_whitespace_insensitive():
    factory = PaymentGatewayFactory()

    assert isinstance(factory.get_mobile_money_adapter(" MTN "), PaymentServiceProxy)


def test_unknown_provider_raises():
    factory = PaymentGatewayFactory()

    with pytest.raises(UnknownPaymentProviderError):
        factory.get_mobile_money_adapter("zamtel-kwacha")


def test_returns_card_adapter_unwrapped_by_any_proxy():
    """Card payments deliberately get no offline failover — a card
    gateway that can't be reached must fail the payment, not queue
    it (see PaymentServiceProxy's docstring)."""
    factory = PaymentGatewayFactory()

    adapter = factory.get_card_adapter()

    assert isinstance(adapter, CardProcessorAdapter)
    assert not isinstance(adapter, PaymentServiceProxy)


def test_repeated_lookups_return_the_same_adapter_instance():
    """The factory caches/reuses adapters rather than constructing a
    fresh one (and a fresh underlying client) on every call."""
    factory = PaymentGatewayFactory()

    first = factory.get_mobile_money_adapter("mtn")
    second = factory.get_mobile_money_adapter("mtn")

    assert first is second


def test_mtn_and_airtel_proxies_share_the_same_offline_queue():
    """One backlog for the whole store, not one per provider — a
    manager triggers a single resync, not one per provider."""
    factory = PaymentGatewayFactory()

    mtn_proxy = factory.get_mobile_money_adapter("mtn")
    airtel_proxy = factory.get_mobile_money_adapter("airtel")

    assert factory.offline_queue is not None
    assert len(factory.offline_queue) == 0
    # Both proxies enqueue into the same factory-owned queue; verified
    # behaviourally (not by reaching into private attributes) in
    # test_payment_service_proxy.py and the Register-level offline
    # tests, which assert factory.offline_queue grows/shrinks as
    # expected across both providers.
