"""CompletedReturnRecord: a read-only historical snapshot of a
completed SaleReturn, persisted for reporting.

Mirrors CompletedSaleRecord's reasoning exactly (see
completed_sale_record.py): this is not a reconstruction of the live
SaleReturn object graph, just a receipt-shaped record of what was
returned and refunded.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from supermarket_pos.domain.common.money import Money


@dataclass(frozen=True)
class CompletedReturnLineItemRecord:
    item_id: str
    description: str
    quantity: int
    subtotal: Money


@dataclass(frozen=True)
class CompletedReturnRecord:
    """A completed return as it will be read back for reporting."""

    oid: str
    date_time: datetime
    total_refund: Money
    line_items: Tuple[CompletedReturnLineItemRecord, ...]
