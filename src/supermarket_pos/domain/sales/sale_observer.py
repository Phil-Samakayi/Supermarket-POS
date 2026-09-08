"""ISaleObserver: GoF Observer for Sale state changes (Larman Ch.26 / Ch.35).

Deferred until a real UI existed. A checkout screen implements this
and registers itself with a Sale; the Sale notifies after every
meaningful state change without knowing the concrete UI type.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supermarket_pos.domain.sales.sale import Sale


class ISaleObserver(ABC):
    """Anyone interested in Sale changes implements this and registers
    via Sale.add_observer()."""

    @abstractmethod
    def sale_updated(self, sale: "Sale") -> None:
        """Called after a line item is added, the sale is completed, or
        payment is recorded. The observer should refresh its display
        from the Sale."""
        ...