from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.offline_payment_command import OfflinePaymentCommand
from tests.domain.payment.gateway.flaky_fake_adapter import FlakyFakeAdapter


def test_execute_delegates_to_the_captured_real_adapter():
    adapter = FlakyFakeAdapter(online=True)
    adapter.queue_result(AuthorizationResult(approved=True, reference="TXN9", message="Approved"))
    command = OfflinePaymentCommand(adapter, Money("50.00"), "0977123456", "mtn")

    result = command.execute()

    assert result.approved is True
    assert result.reference == "TXN9"
    assert adapter.calls == [(Money("50.00"), "0977123456")]


def test_command_remembers_what_it_was_queued_for():
    adapter = FlakyFakeAdapter()
    command = OfflinePaymentCommand(adapter, Money("50.00"), "0977123456", "mtn")

    assert command.provider == "mtn"
    assert command.amount == Money("50.00")
    assert command.payer_reference == "0977123456"
    assert command.queued_at is not None
