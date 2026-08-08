from datetime import datetime, timedelta

import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.persistence.completed_return_record import (
    CompletedReturnLineItemRecord,
    CompletedReturnRecord,
)
from supermarket_pos.persistence.completed_sale_record import (
    CompletedSaleLineItemRecord,
    CompletedSaleRecord,
)
from supermarket_pos.reporting.sales_report_generator import SalesReportGenerator


def make_sale(
    total,
    payment_method="cash",
    date_time=None,
    line_items=(),
    oid="sale-1",
):
    return CompletedSaleRecord(
        oid=oid,
        date_time=date_time or datetime(2026, 1, 15, 10, 0),
        total=Money(total),
        payment_method=payment_method,
        payment_reference=None,
        amount_tendered=Money(total),
        change_due=Money("0.00"),
        line_items=tuple(line_items),
    )


def make_sale_line_item(item_id, description, quantity, subtotal):
    return CompletedSaleLineItemRecord(
        item_id=item_id, description=description, quantity=quantity, subtotal=Money(subtotal)
    )


def make_return(total_refund, date_time=None, line_items=(), oid="return-1"):
    return CompletedReturnRecord(
        oid=oid,
        date_time=date_time or datetime(2026, 1, 15, 11, 0),
        total_refund=Money(total_refund),
        line_items=tuple(line_items),
    )


@pytest.fixture
def generator() -> SalesReportGenerator:
    return SalesReportGenerator()


class TestSummarize:
    def test_empty_history_produces_a_zeroed_report(self, generator):
        report = generator.summarize([], [])

        assert report.sale_count == 0
        assert report.return_count == 0
        assert report.gross_revenue == Money("0.00")
        assert report.total_refunds == Money("0.00")
        assert report.net_revenue == Money("0.00")
        assert report.revenue_by_payment_method == {}

    def test_gross_refunds_and_net_revenue_are_computed_correctly(self, generator):
        sales = [make_sale("100.00", oid="s1"), make_sale("50.00", oid="s2")]
        returns = [make_return("30.00")]

        report = generator.summarize(sales, returns)

        assert report.sale_count == 2
        assert report.return_count == 1
        assert report.gross_revenue == Money("150.00")
        assert report.total_refunds == Money("30.00")
        assert report.net_revenue == Money("120.00")

    def test_revenue_is_broken_down_by_payment_method(self, generator):
        sales = [
            make_sale("100.00", payment_method="cash", oid="s1"),
            make_sale("50.00", payment_method="cash", oid="s2"),
            make_sale("85.00", payment_method="mtn", oid="s3"),
        ]

        report = generator.summarize(sales, [])

        assert report.revenue_by_payment_method == {
            "cash": Money("150.00"),
            "mtn": Money("85.00"),
        }

    def test_date_range_filters_out_sales_and_returns_outside_it(self, generator):
        in_range = make_sale("100.00", date_time=datetime(2026, 1, 15), oid="s1")
        before_range = make_sale("999.00", date_time=datetime(2026, 1, 1), oid="s2")
        after_range = make_sale("999.00", date_time=datetime(2026, 2, 1), oid="s3")

        report = generator.summarize(
            [in_range, before_range, after_range],
            [],
            start=datetime(2026, 1, 10),
            end=datetime(2026, 1, 20),
        )

        assert report.sale_count == 1
        assert report.gross_revenue == Money("100.00")

    def test_start_only_filter_includes_everything_after_it(self, generator):
        sales = [
            make_sale("10.00", date_time=datetime(2026, 1, 1), oid="s1"),
            make_sale("20.00", date_time=datetime(2026, 6, 1), oid="s2"),
        ]

        report = generator.summarize(sales, [], start=datetime(2026, 3, 1))

        assert report.sale_count == 1
        assert report.gross_revenue == Money("20.00")


class TestTopSellingItems:
    def test_empty_history_produces_no_rows(self, generator):
        assert generator.top_selling_items([]) == []

    def test_ranks_items_by_quantity_sold_descending(self, generator):
        sales = [
            make_sale(
                "185.00",
                line_items=[
                    make_sale_line_item("SKU-001", "Mealie Meal", 3, "255.00"),
                    make_sale_line_item("SKU-002", "Cooking Oil", 1, "65.50"),
                ],
            ),
        ]

        rows = generator.top_selling_items(sales)

        assert [row.item_id for row in rows] == ["SKU-001", "SKU-002"]
        assert rows[0].quantity_sold == 3
        assert rows[0].revenue == Money("255.00")

    def test_aggregates_the_same_item_across_multiple_sales(self, generator):
        sales = [
            make_sale(
                "85.00",
                oid="s1",
                line_items=[make_sale_line_item("SKU-001", "Mealie Meal", 1, "85.00")],
            ),
            make_sale(
                "170.00",
                oid="s2",
                line_items=[make_sale_line_item("SKU-001", "Mealie Meal", 2, "170.00")],
            ),
        ]

        rows = generator.top_selling_items(sales)

        assert len(rows) == 1
        assert rows[0].quantity_sold == 3
        assert rows[0].revenue == Money("255.00")

    def test_limit_caps_the_number_of_rows_returned(self, generator):
        sales = [
            make_sale(
                "30.00",
                line_items=[
                    make_sale_line_item("SKU-001", "A", 3, "30.00"),
                    make_sale_line_item("SKU-002", "B", 2, "20.00"),
                    make_sale_line_item("SKU-003", "C", 1, "10.00"),
                ],
            ),
        ]

        rows = generator.top_selling_items(sales, limit=2)

        assert len(rows) == 2
        assert [row.item_id for row in rows] == ["SKU-001", "SKU-002"]

    def test_date_range_filters_sales_before_aggregating(self, generator):
        sales = [
            make_sale(
                "85.00",
                date_time=datetime(2026, 1, 1),
                oid="s1",
                line_items=[make_sale_line_item("SKU-001", "Mealie Meal", 1, "85.00")],
            ),
            make_sale(
                "85.00",
                date_time=datetime(2026, 6, 1),
                oid="s2",
                line_items=[make_sale_line_item("SKU-001", "Mealie Meal", 5, "425.00")],
            ),
        ]

        rows = generator.top_selling_items(sales, start=datetime(2026, 5, 1))

        assert len(rows) == 1
        assert rows[0].quantity_sold == 5
