import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.card_payment import CardPayment
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter
from supermarket_pos.domain.payment.mobile_money_payment import MobileMoneyPayment


class FakeAdapter(IPaymentGatewayAdapter):
    """A minimal IPaymentGatewayAdapter test double — no network, no
    simulated client — used to test ElectronicPayment/Payment
    collaboration in isolation from any real provider's translation
    logic (that's covered separately by the adapter-specific tests)."""

    def __init__(self, result: AuthorizationResult) -> None:
        self._result = result
        self.received_amount = None
        self.received_reference = None

    def authorize(self, amount, payer_reference):
        self.received_amount = amount
        self.received_reference = payer_reference
        return self._result


def test_mobile_money_payment_authorize_delegates_to_its_adapter():
    adapter = FakeAdapter(AuthorizationResult(approved=True, reference="TXN1", message="Approved"))
    payment = MobileMoneyPayment(Money("50.00"), adapter, "0977123456", "mtn")

    result = payment.authorize()

    assert result.approved is True
    assert adapter.received_amount == Money("50.00")
    assert adapter.received_reference == "0977123456"
    assert payment.authorization_result is result


def test_payment_authorization_result_is_none_before_authorize_is_called():
    adapter = FakeAdapter(AuthorizationResult(approved=True, reference="TXN1", message="Approved"))
    payment = MobileMoneyPayment(Money("50.00"), adapter, "0977123456", "mtn")

    assert payment.authorization_result is None


def test_card_payment_authorize_delegates_to_its_adapter():
    adapter = FakeAdapter(AuthorizationResult(approved=False, reference=None, message="declined"))
    payment = CardPayment(Money("120.00"), adapter, "4111111111111111")

    result = payment.authorize()

    assert result.approved is False
    assert payment.payer_reference == "4111111111111111"
