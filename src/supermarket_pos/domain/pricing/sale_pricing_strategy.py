"""ISalePricingStrategy: GoF Strategy for pluggable sale-total algorithms.

Larman, *Applying UML and Patterns*, Ch.26 (Applying GoF Design Patterns,
"Strategy"): the behavior of pricing varies by policy — plain summation
today, percentage or bulk discounts tomorrow — so each policy is defined
in its own class behind a common interface, rather than as conditional
logic inside Sale.

Following the book's guidance for Strategy/context collaboration, the
context object (Sale) passes a reference to itself into get_total() so
the strategy can ask it for whatever it needs (currently just the
pre-discount subtotal) without Sale having to expose more than that.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from supermarket_pos.domain.common.money import Money

if TYPE_CHECKING:
    from supermarket_pos.domain.sales.sale import Sale


class ISalePricingStrategy(ABC):
    """Common interface for all sale pricing strategies."""

    @abstractmethod
    def get_total(self, sale: "Sale") -> Money:
        """Return the sale total under this strategy's pricing policy."""
        raise NotImplementedError
