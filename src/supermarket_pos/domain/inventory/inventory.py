"""Inventory: GRASP Information Expert for on-hand quantities.

Mirrors ProductCatalog's shape (an in-memory dict keyed by item_id) —
same reasoning: a simple in-memory collection today, persistence
coordinated from outside by whoever holds this (InventoryManager),
exactly as Store coordinates ProductCatalog's persistence without
ProductCatalog knowing persistence exists.
"""
from __future__ import annotations

from typing import Dict, List


class Inventory:
    """Tracks on-hand quantity per item_id. An item with no recorded
    stock level has an implicit quantity of 0 — receiving stock for an
    item is independent of when it was added to the catalog; a manager
    might catalog a product today and receive physical stock later."""

    def __init__(self) -> None:
        self._quantities: Dict[str, int] = {}

    def set_quantity(self, item_id: str, quantity: int) -> None:
        """Sets the on-hand quantity directly — used when loading
        persisted StockLevel records, not for day-to-day adjustments
        (use increase()/adjust() for those, which enforce invariants)."""
        if quantity < 0:
            raise ValueError("Quantity on hand cannot be negative.")
        self._quantities[item_id] = quantity

    def get_quantity(self, item_id: str) -> int:
        return self._quantities.get(item_id, 0)

    def increase(self, item_id: str, quantity: int) -> int:
        """Records newly received stock. Returns the new total."""
        if quantity <= 0:
            raise ValueError("Received quantity must be positive.")
        new_quantity = self.get_quantity(item_id) + quantity
        self._quantities[item_id] = new_quantity
        return new_quantity

    def adjust(self, item_id: str, delta: int) -> int:
        """A manual correction (damaged/lost/miscounted stock); delta
        may be negative. Returns the new total. Raises ValueError if
        the adjustment would take stock below zero."""
        new_quantity = self.get_quantity(item_id) + delta
        if new_quantity < 0:
            raise ValueError(
                f"Adjustment would take {item_id!r} stock below zero "
                f"(currently {self.get_quantity(item_id)}, delta {delta})."
            )
        self._quantities[item_id] = new_quantity
        return new_quantity

    def items_at_or_below(self, threshold: int) -> List[str]:
        """item_ids with quantity_on_hand <= threshold, sorted. Items
        with no recorded stock level at all (implicit 0) count as
        at-or-below any non-negative threshold."""
        return sorted(item_id for item_id, qty in self._quantities.items() if qty <= threshold)

    def __len__(self) -> int:
        return len(self._quantities)
