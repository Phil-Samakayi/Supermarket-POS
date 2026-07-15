import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.cash_payment import CashPayment
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.sales.sale import Sale


@pytest.fixture
def bread() -> ProductDescription:
    return ProductDescription("SKU-003", "Loaf of Bread", Money("18.00"))


@pytest.fixture
def sale() -> Sale:
    return Sale()


def test_make_line_item_adds_line_item_and_updates_total(sale, bread):
    sale.make_line_item(bread, 2)

    assert sale.get_total() == Money("36.00")
    assert len(sale.line_items) == 1


def test_get_total_sums_multiple_line_items(sale, bread):
    oil = ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50"))

    sale.make_line_item(bread, 1)
    sale.make_line_item(oil, 2)

    assert sale.get_total() == Money("149.00")


def test_new_sale_is_not_complete(sale):
    assert not sale.is_complete()


def test_become_complete_marks_sale_complete(sale):
    sale.become_complete()

    assert sale.is_complete()


def test_make_line_item_after_sale_complete_raises(sale, bread):
    sale.become_complete()

    with pytest.raises(ValueError):
        sale.make_line_item(bread, 1)


def test_make_payment_before_sale_complete_raises(sale, bread):
    sale.make_line_item(bread, 1)

    with pytest.raises(ValueError):
        sale.make_payment(CashPayment(Money("20.00")))


def test_get_balance_after_cash_payment_returns_change_due(sale, bread):
    sale.make_line_item(bread, 1)
    sale.become_complete()

    sale.make_payment(CashPayment(Money("20.00")))

    assert sale.get_balance() == Money("2.00")


def test_get_balance_before_payment_returns_total_owed(sale, bread):
    sale.make_line_item(bread, 2)

    assert sale.get_balance() == Money("36.00")
