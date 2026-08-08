"""CardProcessorAdapter: resource Adapter for card payments.

A third, again differently-shaped, provider response — a card
processor's decline reason is typically a short code
("insufficient_funds", "card_declined") rather than free text, and its
reference field is an authorization code rather than a transaction ID.
"""
from __future__ import annotations

from typing import Protocol

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter


class CardProcessorGatewayClient(Protocol):
    """The real network client this adapter depends on. A genuine
    implementation (not built here) would call the card processor's
    authorization API."""

    def charge(self, card_reference: str, amount: str) -> dict:
        ...


class SimulatedCardProcessorGatewayClient:
    """
    Stand-in for a real card processor client. Deterministic for tests:
    the fixed sentinel card reference always declines; everything else
    approves.
    """

    DECLINE_TEST_CARD_REFERENCE = "0000000000000000"

    def __init__(self, simulate_outage: bool = False) -> None:
        self._simulate_outage = simulate_outage
        self._next_auth_code = 1

    def set_outage(self, active: bool) -> None:
        """Flip connectivity mid-test without constructing a fresh
        client (see SimulatedMTNMoMoGatewayClient.set_outage)."""
        self._simulate_outage = active

    def charge(self, card_reference: str, amount: str) -> dict:
        if self._simulate_outage:
            raise ConnectionError("card processor API unreachable")
        if card_reference == self.DECLINE_TEST_CARD_REFERENCE:
            return {"approved": False, "authCode": None, "declineReason": "insufficient_funds"}
        auth_code = f"AUTH{self._next_auth_code:06d}"
        self._next_auth_code += 1
        return {"approved": True, "authCode": auth_code, "declineReason": None}


class CardProcessorAdapter(IPaymentGatewayAdapter):
    """Adapts a card processor to IPaymentGatewayAdapter."""

    DECLINE_TEST_CARD_REFERENCE = SimulatedCardProcessorGatewayClient.DECLINE_TEST_CARD_REFERENCE

    def __init__(self, client: CardProcessorGatewayClient) -> None:
        self._client = client

    @property
    def client(self) -> CardProcessorGatewayClient:
        """Exposed for tests that need to toggle the underlying
        client's simulated connectivity. Not intended for production
        collaborators."""
        return self._client

    def authorize(self, amount: Money, payer_reference: str) -> AuthorizationResult:
        try:
            raw = self._client.charge(card_reference=payer_reference, amount=str(amount.amount))
        except ConnectionError as exc:
            raise GatewayUnavailableError("Card processor", str(exc)) from exc

        approved = bool(raw["approved"])
        return AuthorizationResult(
            approved=approved,
            reference=raw.get("authCode"),
            message="Approved" if approved else (raw.get("declineReason") or "Declined"),
        )
