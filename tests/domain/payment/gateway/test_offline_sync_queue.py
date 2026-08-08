from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.offline_payment_command import OfflinePaymentCommand
from supermarket_pos.domain.payment.gateway.offline_sync_queue import OfflineSyncQueue
from tests.domain.payment.gateway.flaky_fake_adapter import FlakyFakeAdapter


def make_command(adapter, phone="0977123456", provider="mtn"):
    return OfflinePaymentCommand(adapter, Money("50.00"), phone, provider)


def test_new_queue_is_empty():
    queue = OfflineSyncQueue()

    assert len(queue) == 0
    assert queue.pending_commands == ()


def test_enqueue_adds_a_command():
    queue = OfflineSyncQueue()
    command = make_command(FlakyFakeAdapter())

    queue.enqueue(command)

    assert len(queue) == 1
    assert queue.pending_commands == (command,)


def test_replay_all_confirms_a_command_whose_gateway_is_back_online():
    queue = OfflineSyncQueue()
    adapter = FlakyFakeAdapter(online=False)
    command = make_command(adapter)
    queue.enqueue(command)

    adapter.online = True  # connectivity restored
    report = queue.replay_all()

    assert len(report.confirmed) == 1
    assert report.confirmed[0][0] is command
    assert report.confirmed[0][1].approved is True
    assert len(queue) == 0
    assert not report.has_outstanding_work


def test_replay_all_leaves_still_unreachable_commands_queued():
    queue = OfflineSyncQueue()
    adapter = FlakyFakeAdapter(online=False)
    command = make_command(adapter)
    queue.enqueue(command)

    report = queue.replay_all()  # still offline

    assert report.confirmed == ()
    assert report.failed == ()
    assert report.still_pending == (command,)
    assert len(queue) == 1
    assert report.has_outstanding_work


def test_replay_all_reports_a_decline_discovered_on_replay_as_failed_not_confirmed():
    """The money genuinely never moved — this must be surfaced
    distinctly from a normal confirmation so a human follows up."""
    queue = OfflineSyncQueue()
    adapter = FlakyFakeAdapter(online=True)
    adapter.queue_result(
        AuthorizationResult(approved=False, reference=None, message="Insufficient funds")
    )
    command = make_command(adapter)
    queue.enqueue(command)

    report = queue.replay_all()

    assert report.confirmed == ()
    assert len(report.failed) == 1
    assert report.failed[0][0] is command
    assert report.failed[0][1].approved is False
    assert len(queue) == 0


def test_replay_all_handles_a_mix_of_providers_independently():
    queue = OfflineSyncQueue()
    still_down = FlakyFakeAdapter(online=False)
    now_up = FlakyFakeAdapter(online=True)
    command_mtn = make_command(still_down, provider="mtn")
    command_airtel = make_command(now_up, provider="airtel")
    queue.enqueue(command_mtn)
    queue.enqueue(command_airtel)

    report = queue.replay_all()

    assert report.still_pending == (command_mtn,)
    assert len(report.confirmed) == 1
    assert report.confirmed[0][0] is command_airtel
    assert len(queue) == 1
