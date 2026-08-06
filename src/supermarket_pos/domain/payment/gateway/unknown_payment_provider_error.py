"""Raised when PaymentGatewayFactory is asked for a mobile money
provider it does not recognize."""
from __future__ import annotations


class UnknownPaymentProviderError(Exception):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Unknown mobile money provider: {provider!r}")
        self.provider = provider
