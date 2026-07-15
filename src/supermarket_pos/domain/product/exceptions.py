"""Exceptions raised by the product package.

ProductNotFoundError realizes Extension 3a of UC1 (Process Sale):
"Item identifier not found / barcode unreadable".
"""
from __future__ import annotations


class ProductNotFoundError(Exception):
    """Raised when an item identifier does not match any ProductDescription."""

    def __init__(self, item_id: str) -> None:
        super().__init__(f"No product found for item identifier: {item_id}")
        self.item_id = item_id
