"""Inventory: GRASP Information Expert for on-hand quantities.

Mirrors ProductCatalog's shape (an in-memory dict keyed by item_id).
"""
from __future__ import annotations

from typing import Dict, List


class Inventory:
    """Tracks on-hand quantity per item_id. An item with no recorded
    stock level has an implicit quantity of 0."""

    def __init__(self) -> None:
        self._quantities: Dict[str, int] = {}

    def set_quantity(self, item_id: str, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity on hand cannot be negative.")
        self._quantities[item_id] = quantity

    def get_quantity(self, item_id: str) -> int:
        return self._quantities.get(item_id, 0)

    def increase(self, item_id: str, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("Received quantity must be positive.")
        new_quantity = self.get_quantity(item_id) + quantity
        self._quantities[item_id] = new_quantity
        return new_quantity

    def adjust(self, item_id: str, delta: int) -> int:
        new_quantity = self.get_quantity(item_id) + delta
        if new_quantity < 0:
            raise ValueError(
                f"Adjustment would take {item_id!r} stock below zero "
                f"(currently {self.get_quantity(item_id)}, delta {delta})."
            )
        self._quantities[item_id] = new_quantity
        return new_quantity

    def decrease(self, item_id: str, quantity: int) -> int:
        """Decrease stock for a completed sale. Clamps at zero rather
        than raising (business rule: never block a sale for a stock
        discrepancy). Returns the new on-hand quantity."""
        if quantity <= 0:
            raise ValueError("Decrease quantity must be positive.")
        current = self.get_quantity(item_id)
        new_quantity = max(0, current - quantity)
        self._quantities[item_id] = new_quantity
        return new_quantity

    def items_at_or_below(self, threshold: int) -> List[str]:
        return sorted(
            item_id for item_id, qty in self._quantities.items() if qty <= threshold
        )

    def __len__(self) -> int:
        return len(self._quantities)