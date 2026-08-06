import pytest

from supermarket_pos.domain.payment.gateway.airtel_money_adapter import AirtelMoneyAdapter
from supermarket_pos.domain.payment.gateway.card_processor_adapter import CardProcessorAdapter
from supermarket_pos.domain.payment.gateway.mtn_momo_adapter import MTNMoMoAdapter
from supermarket_pos.domain.payment.gateway.payment_gateway_factory import PaymentGatewayFactory
from supermarket_pos.domain.payment.gateway.unknown_payment_provider_error import (
    UnknownPaymentProviderError,
)


def test_get_instance_returns_the_same_singleton():
    first = PaymentGatewayFactory.get_instance()
    second = PaymentGatewayFactory.get_instance()

    assert first is second


def test_returns_mtn_adapter_for_mtn_provider():
    factory = PaymentGatewayFactory()

    assert isinstance(factory.get_mobile_money_adapter("mtn"), MTNMoMoAdapter)


def test_returns_airtel_adapter_for_airtel_provider():
    factory = PaymentGatewayFactory()

    assert isinstance(factory.get_mobile_money_adapter("airtel"), AirtelMoneyAdapter)


def test_provider_lookup_is_case_and_whitespace_insensitive():
    factory = PaymentGatewayFactory()

    assert isinstance(factory.get_mobile_money_adapter(" MTN "), MTNMoMoAdapter)


def test_unknown_provider_raises():
    factory = PaymentGatewayFactory()

    with pytest.raises(UnknownPaymentProviderError):
        factory.get_mobile_money_adapter("zamtel-kwacha")


def test_returns_card_adapter():
    factory = PaymentGatewayFactory()

    assert isinstance(factory.get_card_adapter(), CardProcessorAdapter)


def test_repeated_lookups_return_the_same_adapter_instance():
    """The factory caches/reuses adapters rather than constructing a
    fresh one (and a fresh underlying client) on every call."""
    factory = PaymentGatewayFactory()

    first = factory.get_mobile_money_adapter("mtn")
    second = factory.get_mobile_money_adapter("mtn")

    assert first is second
