import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.returns.cash_refund import CashRefund
from supermarket_pos.domain.returns.sale_return import SaleReturn


@pytest.fixture
def bread() -> ProductDescription:
    return ProductDescription("SKU-003", "Loaf of Bread", Money("18.00"))


def test_make_line_item_adds_line_item_and_updates_refund_total(bread):
    sale_return = SaleReturn()

    sale_return.make_line_item(bread, 2)

    assert sale_return.get_total() == Money("36.00")


def test_get_total_sums_multiple_line_items(bread):
    oil = ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50"))
    sale_return = SaleReturn()
    sale_return.make_line_item(bread, 1)
    sale_return.make_line_item(oil, 1)

    assert sale_return.get_total() == Money("83.50")


def test_new_return_is_not_complete():
    assert SaleReturn().is_complete() is False


def test_become_complete_marks_return_complete(bread):
    sale_return = SaleReturn()
    sale_return.make_line_item(bread, 1)

    sale_return.become_complete()

    assert sale_return.is_complete() is True


def test_become_complete_with_no_items_raises():
    with pytest.raises(ValueError, match="no items"):
        SaleReturn().become_complete()


def test_make_line_item_after_return_complete_raises(bread):
    sale_return = SaleReturn()
    sale_return.make_line_item(bread, 1)
    sale_return.become_complete()

    with pytest.raises(ValueError, match="completed return"):
        sale_return.make_line_item(bread, 1)


def test_make_refund_before_complete_raises(bread):
    sale_return = SaleReturn()
    sale_return.make_line_item(bread, 1)

    with pytest.raises(ValueError, match="before the return is complete"):
        sale_return.make_refund(CashRefund(Money("18.00")))


def test_make_refund_records_the_refund(bread):
    sale_return = SaleReturn()
    sale_return.make_line_item(bread, 1)
    sale_return.become_complete()

    sale_return.make_refund(CashRefund(Money("18.00")))

    assert sale_return.refund is not None
    assert sale_return.refund.amount == Money("18.00")


def test_refund_uses_current_catalog_price_not_original_sale_price(bread):
    """Documented scope cut: this slice doesn't link a return to its
    original Sale, so a since-changed price is reflected as-is."""
    discounted_bread_at_original_sale = Money("15.00")  # what was actually paid
    current_price = bread.price  # K18.00 — what ReturnedLineItem will use

    sale_return = SaleReturn()
    sale_return.make_line_item(bread, 1)

    assert sale_return.get_total() == current_price
    assert sale_return.get_total() != discounted_bread_at_original_sale
