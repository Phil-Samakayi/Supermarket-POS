"""SalesReportGenerator: computes reports from persisted sale/return
history.

GRASP: Pure Fabrication / Information Expert for report computation —
a class invented purely to hold this responsibility (there's no
real-world "report generator" role), given the data it needs
(CompletedSaleRecord/CompletedReturnRecord lists) rather than reaching
for a database or a Store itself. This keeps it trivially unit
testable and reusable regardless of where the records came from.

Scope note: this only covers sales/returns reporting. A "stock
summary" (the other half of Iteration 3's originally-scoped Reporting
item) needs an inventory-quantity concept that doesn't exist anywhere
in the domain model yet — ProductDescription has no quantity_on_hand.
That's Manage Inventory's job, not started. See ARCHITECTURE.md.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence

from supermarket_pos.domain.common.money import Money, ZERO
from supermarket_pos.persistence.completed_return_record import CompletedReturnRecord
from supermarket_pos.persistence.completed_sale_record import CompletedSaleRecord
from supermarket_pos.reporting.sales_report import SalesSummaryReport, TopSellingItemReportRow


class SalesReportGenerator:
    """Computes SalesSummaryReport and top-selling-items breakdowns
    from completed sale/return history."""

    def summarize(
        self,
        sales: Sequence[CompletedSaleRecord],
        returns: Sequence[CompletedReturnRecord],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> SalesSummaryReport:
        filtered_sales = self._filter_by_date(sales, start, end)
        filtered_returns = self._filter_by_date(returns, start, end)

        gross_revenue = self._sum_money(sale.total for sale in filtered_sales)
        total_refunds = self._sum_money(ret.total_refund for ret in filtered_returns)

        revenue_by_method: Dict[str, Money] = {}
        for sale in filtered_sales:
            revenue_by_method[sale.payment_method] = revenue_by_method.get(
                sale.payment_method, ZERO
            ).plus(sale.total)

        return SalesSummaryReport(
            period_start=start,
            period_end=end,
            sale_count=len(filtered_sales),
            return_count=len(filtered_returns),
            gross_revenue=gross_revenue,
            total_refunds=total_refunds,
            net_revenue=gross_revenue.minus(total_refunds),
            revenue_by_payment_method=revenue_by_method,
        )

    def top_selling_items(
        self,
        sales: Sequence[CompletedSaleRecord],
        limit: int = 5,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[TopSellingItemReportRow]:
        filtered_sales = self._filter_by_date(sales, start, end)

        quantity_by_item: Dict[str, int] = {}
        revenue_by_item: Dict[str, Money] = {}
        description_by_item: Dict[str, str] = {}

        for sale in filtered_sales:
            for line_item in sale.line_items:
                quantity_by_item[line_item.item_id] = (
                    quantity_by_item.get(line_item.item_id, 0) + line_item.quantity
                )
                revenue_by_item[line_item.item_id] = revenue_by_item.get(
                    line_item.item_id, ZERO
                ).plus(line_item.subtotal)
                description_by_item[line_item.item_id] = line_item.description

        rows = [
            TopSellingItemReportRow(
                item_id=item_id,
                description=description_by_item[item_id],
                quantity_sold=quantity_by_item[item_id],
                revenue=revenue_by_item[item_id],
            )
            for item_id in quantity_by_item
        ]
        rows.sort(key=lambda row: row.quantity_sold, reverse=True)
        return rows[:limit]

    @staticmethod
    def _filter_by_date(records, start: Optional[datetime], end: Optional[datetime]):
        result = list(records)
        if start is not None:
            result = [r for r in result if r.date_time >= start]
        if end is not None:
            result = [r for r in result if r.date_time <= end]
        return result

    @staticmethod
    def _sum_money(amounts: Iterable[Money]) -> Money:
        total = ZERO
        for amount in amounts:
            total = total.plus(amount)
        return total
