"""OfflineSyncQueue: holds OfflinePaymentCommands queued by
PaymentServiceProxy while a gateway was unreachable, and replays them
once connectivity is believed to be restored.

This is the Pure Fabrication counterpart to Larman's Command Processor
role (Ch.38, "Designing a Transaction with the Command Pattern") — a
collaborator whose sole responsibility is queueing and re-executing
Command objects, kept separate from PaymentServiceProxy so the queue
itself has nothing to do with *how* a request was authorized, only
with holding and replaying it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)
from supermarket_pos.domain.payment.gateway.offline_payment_command import OfflinePaymentCommand

ReplayedPair = Tuple[OfflinePaymentCommand, AuthorizationResult]


@dataclass(frozen=True)
class OfflineSyncReport:
    """Outcome of one replay_all() attempt."""

    confirmed: Tuple[ReplayedPair, ...]
    failed: Tuple[ReplayedPair, ...]
    still_pending: Tuple[OfflinePaymentCommand, ...]

    @property
    def has_outstanding_work(self) -> bool:
        return len(self.still_pending) > 0


class OfflineSyncQueue:
    """FIFO queue of deferred payment authorizations."""

    def __init__(self) -> None:
        self._pending: List[OfflinePaymentCommand] = []

    def enqueue(self, command: OfflinePaymentCommand) -> None:
        self._pending.append(command)

    def __len__(self) -> int:
        return len(self._pending)

    @property
    def pending_commands(self) -> Tuple[OfflinePaymentCommand, ...]:
        return tuple(self._pending)

    def replay_all(self) -> OfflineSyncReport:
        """
        Attempt to re-authorize every queued command against its real
        adapter. A command that succeeds (approved or cleanly
        declined) is removed from the queue; a command that raises
        GatewayUnavailableError again is left queued for the next
        replay attempt.

        Declined-on-replay is deliberately reported separately from
        confirmed: it means the store gave the customer their goods
        believing payment was pending, and it turned out the money
        never actually moved — that needs a human (the store follows
        up with the customer), which is exactly the kind of edge case
        Larman's Ch.35 discussion of failure handling flags as
        needing explicit, not silent, treatment.
        """
        confirmed: List[ReplayedPair] = []
        failed: List[ReplayedPair] = []
        still_pending: List[OfflinePaymentCommand] = []

        for command in self._pending:
            try:
                result = command.execute()
            except GatewayUnavailableError:
                still_pending.append(command)
                continue

            if result.approved:
                confirmed.append((command, result))
            else:
                failed.append((command, result))

        self._pending = still_pending
        return OfflineSyncReport(
            confirmed=tuple(confirmed),
            failed=tuple(failed),
            still_pending=tuple(still_pending),
        )
