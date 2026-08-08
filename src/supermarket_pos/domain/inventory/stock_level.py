"""StockLevel: how many of a given item are currently on hand.

Deliberately a separate concept from ProductDescription (catalog/
reference data — name, price — that changes rarely) rather than an
extra field bolted onto it. ProductDescription is a frozen value
type specifically because catalog data is stable; quantity-on-hand
changes with every delivery, sale, and stock adjustment, which is a
fundamentally different rate and reason for change (Larman's own
guidance on grouping responsibilities by what varies together, e.g.
Ch.26's Protected Variations discussion, applies here even though this
isn't itself a GoF pattern).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockLevel:
    """A snapshot of one item's on-hand quantity. item_id doubles as
    both the natural key and this type's OID value, exactly as for
    ProductDescription."""

    item_id: str
    quantity_on_hand: int
