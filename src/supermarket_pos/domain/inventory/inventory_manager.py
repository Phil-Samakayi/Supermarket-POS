"""InventoryManager: GRASP Controller for the Manage Inventory CRUD
system operations.

Larman's own naming guideline for CRUD-collapsed use cases (Ch.6.15):
"A common exception to one use case per goal is to collapse CRUD...
into one CRUD use case, idiomatically called Manage <X>." — the exact
convention "Manage Inventory" and "Manage Users" already follow in
this project's iteration plan.

A deliberately separate Controller from Register, not an extension of
it. Larman's Controller pattern guidance (Ch.17) allows either one
facade controller for the whole system, or one controller per use
case/session — this project has so far grown Register to cover
Process Sale *and* Handle Returns together, both Cashier-facing
activities. Manage Inventory is a different actor (Manager/Owner), and
that alone is reason enough, per the book's own framing, to introduce
a new controller rather than keep piling unrelated system operations
onto Register.
"""
from __future__ import annotations

from typing import List, Optional

from supermarket_pos.domain.inventory.inventory import Inventory
from supermarket_pos.domain.inventory.stock_level import StockLevel
from supermarket_pos.persistence.persistence_facade import PersistenceFacade


class InventoryManager:
    """Controller for receive_stock / adjust_stock / get_stock_level /
    low_stock_items — the Manage Inventory system operations."""

    def __init__(self, persistence_facade: Optional[PersistenceFacade] = None) -> None:
        self._inventory = Inventory()
        self._persistence_facade = persistence_facade

        if self._persistence_facade is not None:
            for stock_level in self._persistence_facade.get_all(StockLevel):
                self._inventory.set_quantity(stock_level.item_id, stock_level.quantity_on_hand)

    def receive_stock(self, item_id: str, quantity: int) -> int:
        """Records newly delivered stock. Returns the new on-hand
        quantity."""
        new_quantity = self._inventory.increase(item_id, quantity)
        self._persist(item_id, new_quantity)
        return new_quantity

    def adjust_stock(self, item_id: str, quantity_delta: int) -> int:
        """A manual correction (damaged/lost/miscounted stock);
        quantity_delta may be negative. Returns the new on-hand
        quantity. Raises ValueError if it would go below zero."""
        new_quantity = self._inventory.adjust(item_id, quantity_delta)
        self._persist(item_id, new_quantity)
        return new_quantity

    def get_stock_level(self, item_id: str) -> int:
        return self._inventory.get_quantity(item_id)

    def low_stock_items(self, threshold: int = 5) -> List[str]:
        return self._inventory.items_at_or_below(threshold)

    def _persist(self, item_id: str, quantity: int) -> None:
        if self._persistence_facade is not None:
            self._persistence_facade.save(StockLevel(item_id, quantity))
