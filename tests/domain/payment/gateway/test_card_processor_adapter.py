import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.card_processor_adapter import (
    CardProcessorAdapter,
    SimulatedCardProcessorGatewayClient,
)
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)


def test_approved_card_payment_translates_to_authorization_result():
    adapter = CardProcessorAdapter(SimulatedCardProcessorGatewayClient())

    result = adapter.authorize(Money("120.00"), "4111111111111111")

    assert result.approved is True
    assert result.reference is not None
    assert result.reference.startswith("AUTH")


def test_declined_card_maps_decline_reason_to_message():
    adapter = CardProcessorAdapter(SimulatedCardProcessorGatewayClient())

    result = adapter.authorize(
        Money("120.00"), CardProcessorAdapter.DECLINE_TEST_CARD_REFERENCE
    )

    assert result.approved is False
    assert result.reference is None
    assert result.message == "insufficient_funds"


def test_network_outage_raises_gateway_unavailable_error():
    adapter = CardProcessorAdapter(SimulatedCardProcessorGatewayClient(simulate_outage=True))

    with pytest.raises(GatewayUnavailableError) as exc_info:
        adapter.authorize(Money("120.00"), "4111111111111111")

    assert exc_info.value.provider_name == "Card processor"
