import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.airtel_money_adapter import (
    AirtelMoneyAdapter,
    SimulatedAirtelMoneyGatewayClient,
)
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)


def test_approved_payment_translates_airtel_result_code_to_authorization_result():
    adapter = AirtelMoneyAdapter(SimulatedAirtelMoneyGatewayClient())

    result = adapter.authorize(Money("50.00"), "0966987654")

    assert result.approved is True
    assert result.reference is not None
    assert result.reference.startswith("AIRTEL-")


def test_declined_payment_maps_non_zero_result_code_to_unapproved():
    adapter = AirtelMoneyAdapter(SimulatedAirtelMoneyGatewayClient())

    result = adapter.authorize(Money("50.00"), AirtelMoneyAdapter.DECLINE_TEST_MSISDN)

    assert result.approved is False
    assert result.reference is None
    assert result.message == "Insufficient funds"


def test_network_outage_raises_gateway_unavailable_error():
    adapter = AirtelMoneyAdapter(SimulatedAirtelMoneyGatewayClient(simulate_outage=True))

    with pytest.raises(GatewayUnavailableError) as exc_info:
        adapter.authorize(Money("50.00"), "0966987654")

    assert exc_info.value.provider_name == "Airtel Money"
