import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)
from supermarket_pos.domain.payment.gateway.mtn_momo_adapter import (
    MTNMoMoAdapter,
    SimulatedMTNMoMoGatewayClient,
)


def test_approved_payment_translates_mtn_shape_to_authorization_result():
    adapter = MTNMoMoAdapter(SimulatedMTNMoMoGatewayClient())

    result = adapter.authorize(Money("50.00"), "0977123456")

    assert result.approved is True
    assert result.reference is not None
    assert result.reference.startswith("MTN-")


def test_declined_payment_returns_unapproved_result_with_reason():
    adapter = MTNMoMoAdapter(SimulatedMTNMoMoGatewayClient())

    result = adapter.authorize(Money("50.00"), MTNMoMoAdapter.DECLINE_TEST_MSISDN)

    assert result.approved is False
    assert result.reference is None
    assert result.message == "Insufficient funds"


def test_network_outage_raises_gateway_unavailable_error_not_connection_error():
    adapter = MTNMoMoAdapter(SimulatedMTNMoMoGatewayClient(simulate_outage=True))

    with pytest.raises(GatewayUnavailableError) as exc_info:
        adapter.authorize(Money("50.00"), "0977123456")

    assert exc_info.value.provider_name == "MTN Mobile Money"
