from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.offline_sync_queue import OfflineSyncQueue
from supermarket_pos.domain.payment.gateway.payment_service_proxy import PaymentServiceProxy
from tests.domain.payment.gateway.flaky_fake_adapter import FlakyFakeAdapter


def test_proxy_passes_through_a_normal_approval_untouched():
    real_adapter = FlakyFakeAdapter(online=True)
    real_adapter.queue_result(
        AuthorizationResult(approved=True, reference="TXN1", message="Approved")
    )
    queue = OfflineSyncQueue()
    proxy = PaymentServiceProxy(real_adapter, queue, "mtn")

    result = proxy.authorize(Money("50.00"), "0977123456")

    assert result.approved is True
    assert result.reference == "TXN1"
    assert result.pending is False
    assert len(queue) == 0


def test_proxy_passes_through_a_normal_decline_untouched():
    real_adapter = FlakyFakeAdapter(online=True)
    real_adapter.queue_result(
        AuthorizationResult(approved=False, reference=None, message="Insufficient funds")
    )
    queue = OfflineSyncQueue()
    proxy = PaymentServiceProxy(real_adapter, queue, "mtn")

    result = proxy.authorize(Money("50.00"), "0977123456")

    assert result.approved is False
    assert result.pending is False
    assert len(queue) == 0


def test_proxy_fails_over_to_the_offline_queue_when_gateway_is_unreachable():
    real_adapter = FlakyFakeAdapter(online=False)
    queue = OfflineSyncQueue()
    proxy = PaymentServiceProxy(real_adapter, queue, "mtn")

    result = proxy.authorize(Money("50.00"), "0977123456")

    assert result.approved is True
    assert result.pending is True
    assert result.reference is None
    assert len(queue) == 1
    assert queue.pending_commands[0].provider == "mtn"
    assert queue.pending_commands[0].payer_reference == "0977123456"


def test_real_adapter_property_exposes_the_wrapped_adapter():
    real_adapter = FlakyFakeAdapter()
    proxy = PaymentServiceProxy(real_adapter, OfflineSyncQueue(), "mtn")

    assert proxy.real_adapter is real_adapter


def test_queued_command_can_later_be_confirmed_by_replaying_the_queue():
    """End-to-end within the gateway package: outage -> queued ->
    connectivity restored -> replay confirms it."""
    real_adapter = FlakyFakeAdapter(online=False)
    queue = OfflineSyncQueue()
    proxy = PaymentServiceProxy(real_adapter, queue, "mtn")

    pending_result = proxy.authorize(Money("50.00"), "0977123456")
    assert pending_result.pending is True

    real_adapter.online = True
    real_adapter.queue_result(
        AuthorizationResult(approved=True, reference="TXN-LATE", message="Approved")
    )
    report = queue.replay_all()

    assert len(report.confirmed) == 1
    assert report.confirmed[0][1].reference == "TXN-LATE"
    assert len(queue) == 0
