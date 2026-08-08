"""MTNMoMoAdapter: resource Adapter for MTN Mobile Money.

Wraps an MTNMoMoGatewayClient (the thing that would actually make an
HTTP call to MTN's Collections API) and translates MTN's own response
shape into the neutral AuthorizationResult defined by
IPaymentGatewayAdapter.
"""
from __future__ import annotations

from typing import Protocol

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter


class MTNMoMoGatewayClient(Protocol):
    """The real network client this adapter depends on. A genuine
    implementation (not built here) would call MTN's Collections API
    over HTTPS. Kept as a narrow Protocol so it can be swapped without
    touching MTNMoMoAdapter."""

    def request_payment(self, msisdn: str, amount: str) -> dict:
        ...


class SimulatedMTNMoMoGatewayClient:
    """
    Stand-in for a real MTN client, used until network access to MTN's
    sandbox is available. Deterministic (no randomness) so tests are
    reliable: a fixed sentinel phone number always declines, everything
    else approves. Returns data shaped like MTN's own API
    (``status`` / ``financialTransactionId``), not our neutral format —
    that translation is the adapter's job, not this client's.
    """

    DECLINE_TEST_MSISDN = "0000000000"

    def __init__(self, simulate_outage: bool = False) -> None:
        self._simulate_outage = simulate_outage
        self._next_transaction_id = 1

    def set_outage(self, active: bool) -> None:
        """Flip connectivity mid-test (e.g. simulate a network drop
        during a sale, then a recovery before replaying the offline
        queue) without having to construct a fresh client."""
        self._simulate_outage = active

    def request_payment(self, msisdn: str, amount: str) -> dict:
        if self._simulate_outage:
            raise ConnectionError("MTN Collections API unreachable")
        if msisdn == self.DECLINE_TEST_MSISDN:
            return {"status": "FAILED", "financialTransactionId": None, "reason": "Insufficient funds"}
        txn_id = f"MTN-{self._next_transaction_id:06d}"
        self._next_transaction_id += 1
        return {"status": "SUCCESS", "financialTransactionId": txn_id, "reason": None}


class MTNMoMoAdapter(IPaymentGatewayAdapter):
    """Adapts MTN Mobile Money to IPaymentGatewayAdapter."""

    DECLINE_TEST_MSISDN = SimulatedMTNMoMoGatewayClient.DECLINE_TEST_MSISDN

    def __init__(self, client: MTNMoMoGatewayClient) -> None:
        self._client = client

    @property
    def client(self) -> MTNMoMoGatewayClient:
        """Exposed for tests that need to toggle the underlying
        client's simulated connectivity (see SimulatedMTNMoMoGatewayClient.
        set_outage). Not intended for production collaborators."""
        return self._client

    def authorize(self, amount: Money, payer_reference: str) -> AuthorizationResult:
        try:
            raw = self._client.request_payment(msisdn=payer_reference, amount=str(amount.amount))
        except ConnectionError as exc:
            raise GatewayUnavailableError("MTN Mobile Money", str(exc)) from exc

        approved = raw["status"] == "SUCCESS"
        return AuthorizationResult(
            approved=approved,
            reference=raw.get("financialTransactionId"),
            message="Approved" if approved else (raw.get("reason") or "Declined"),
        )
