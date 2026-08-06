"""AirtelMoneyAdapter: resource Adapter for Airtel Money.

Airtel's API returns ISO-8583-style numeric result codes rather than
MTN's SUCCESS/FAILED strings — a genuinely different wire shape, which
is exactly the situation Adapter exists for (Larman Ch.26): both
providers end up looking identical to everything above this class.
"""
from __future__ import annotations

from typing import Protocol

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
    GatewayUnavailableError,
)
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter

APPROVED_RESULT_CODE = "00"


class AirtelMoneyGatewayClient(Protocol):
    """The real network client this adapter depends on. A genuine
    implementation (not built here) would call Airtel's Money API."""

    def initiate_payment(self, msisdn: str, amount: str) -> dict:
        ...


class SimulatedAirtelMoneyGatewayClient:
    """
    Stand-in for a real Airtel client. Deterministic for tests: the
    fixed sentinel phone number always declines with resultCode "51"
    (insufficient funds, in Airtel's own coding scheme); everything
    else approves with resultCode "00".
    """

    DECLINE_TEST_MSISDN = "0000000000"

    def __init__(self, simulate_outage: bool = False) -> None:
        self._simulate_outage = simulate_outage
        self._next_transaction_id = 1

    def initiate_payment(self, msisdn: str, amount: str) -> dict:
        if self._simulate_outage:
            raise ConnectionError("Airtel Money API unreachable")
        if msisdn == self.DECLINE_TEST_MSISDN:
            return {"resultCode": "51", "transactionId": None, "resultDesc": "Insufficient funds"}
        txn_id = f"AIRTEL-{self._next_transaction_id:06d}"
        self._next_transaction_id += 1
        return {"resultCode": APPROVED_RESULT_CODE, "transactionId": txn_id, "resultDesc": "Success"}


class AirtelMoneyAdapter(IPaymentGatewayAdapter):
    """Adapts Airtel Money to IPaymentGatewayAdapter."""

    DECLINE_TEST_MSISDN = SimulatedAirtelMoneyGatewayClient.DECLINE_TEST_MSISDN

    def __init__(self, client: AirtelMoneyGatewayClient) -> None:
        self._client = client

    def authorize(self, amount: Money, payer_reference: str) -> AuthorizationResult:
        try:
            raw = self._client.initiate_payment(msisdn=payer_reference, amount=str(amount.amount))
        except ConnectionError as exc:
            raise GatewayUnavailableError("Airtel Money", str(exc)) from exc

        approved = raw["resultCode"] == APPROVED_RESULT_CODE
        return AuthorizationResult(
            approved=approved,
            reference=raw.get("transactionId"),
            message=raw.get("resultDesc") or ("Approved" if approved else "Declined"),
        )
