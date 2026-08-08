"""Report value types produced by SalesReportGenerator.

Reporting is its own Technical Service partition (Larman Ch.13.6/13.7:
"the Technical Services layer may be divided into partitions such as
Security and Reporting") — a sibling to the Persistence partition
already built, not part of the domain layer. These types are computed
purely from CompletedSaleRecord/CompletedReturnRecord snapshots;
SalesReportGenerator has no idea where those came from.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from supermarket_pos.domain.common.money import Money


@dataclass(frozen=True)
class SalesSummaryReport:
    """Revenue/refund summary over an optional date range (None means
    unbounded on that side)."""

    period_start: Optional[datetime]
    period_end: Optional[datetime]
    sale_count: int
    return_count: int
    gross_revenue: Money
    """Sum of completed sale totals in the period."""
    total_refunds: Money
    """Sum of completed return refunds in the period."""
    net_revenue: Money
    """gross_revenue - total_refunds."""
    revenue_by_payment_method: Dict[str, Money]
    """e.g. {"cash": Money("500.00"), "mtn": Money("120.00")}."""


@dataclass(frozen=True)
class TopSellingItemReportRow:
    """One row of a top-selling-items report, ranked by quantity sold."""

    item_id: str
    description: str
    quantity_sold: int
    revenue: Money
