"""ProductDescription: a product's catalog entry."""
from __future__ import annotations

from dataclasses import dataclass

from supermarket_pos.domain.common.money import Money


@dataclass(frozen=True)
class ProductDescription:
    """Describes a product independent of any particular sale (Domain Model)."""

    item_id: str
    description: str
    price: Money
