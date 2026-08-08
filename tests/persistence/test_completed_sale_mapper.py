import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.card_payment import CardPayment
from supermarket_pos.domain.payment.cash_payment import CashPayment
from supermarket_pos.domain.payment.gateway.authorization_result import AuthorizationResult
from supermarket_pos.domain.payment.gateway.payment_gateway_adapter import IPaymentGatewayAdapter
from supermarket_pos.domain.payment.mobile_money_payment import MobileMoneyPayment
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.sales.sale import Sale
from supermarket_pos.persistence.completed_sale_mapper import CompletedSaleMapper
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


class ApprovingFakeAdapter(IPaymentGatewayAdapter):
    def authorize(self, amount, payer_reference):
        return AuthorizationResult(approved=True, reference="TXN1", message="Approved")


@pytest.fixture
def mapper() -> CompletedSaleMapper:
    return CompletedSaleMapper(SQLiteConnection(":memory:"))


def make_paid_cash_sale() -> Sale:
    sale = Sale()
    sale.make_line_item(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")), 2)
    sale.make_line_item(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")), 1)
    sale.become_complete()
    sale.make_payment(CashPayment(Money("300.00")))
    return sale


def make_paid_mobile_money_sale() -> Sale:
    sale = Sale()
    sale.make_line_item(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")), 1)
    sale.become_complete()
    payment = MobileMoneyPayment(Money("85.00"), ApprovingFakeAdapter(), "0977123456", "mtn")
    payment.authorize()
    sale.make_payment(payment)
    return sale


def test_save_unpaid_sale_raises():
    mapper = CompletedSaleMapper(SQLiteConnection(":memory:"))
    sale = Sale()
    sale.make_line_item(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")), 1)
    sale.become_complete()

    with pytest.raises(ValueError, match="no payment"):
        mapper.save(sale)


def test_save_then_get_round_trips_totals_and_payment_method(mapper):
    sale = make_paid_cash_sale()

    oid = mapper.save(sale)
    record = mapper.get(oid)

    assert record.total == Money("235.50")
    assert record.payment_method == "cash"
    assert record.payment_reference is None
    assert record.amount_tendered == Money("300.00")
    assert record.change_due == Money("64.50")


def test_save_then_get_round_trips_line_items(mapper):
    sale = make_paid_cash_sale()

    oid = mapper.save(sale)
    record = mapper.get(oid)

    assert len(record.line_items) == 2
    first, second = record.line_items
    assert first.item_id == "SKU-001"
    assert first.quantity == 2
    assert first.subtotal == Money("170.00")
    assert second.item_id == "SKU-002"
    assert second.subtotal == Money("65.50")


def test_mobile_money_payment_method_and_reference_are_captured(mapper):
    sale = make_paid_mobile_money_sale()

    oid = mapper.save(sale)
    record = mapper.get(oid)

    assert record.payment_method == "mtn"
    assert record.payment_reference == "0977123456"


def test_get_all_returns_every_saved_sale_ordered_by_date(mapper):
    mapper.save(make_paid_cash_sale())
    mapper.save(make_paid_mobile_money_sale())

    all_sales = mapper.get_all()

    assert len(all_sales) == 2


def test_get_with_unknown_oid_raises(mapper):
    from supermarket_pos.persistence.oid import OID

    with pytest.raises(ValueError, match="No completed sale"):
        mapper.get(OID("does-not-exist"))


def test_each_saved_sale_gets_a_distinct_oid(mapper):
    first = mapper.save(make_paid_cash_sale())
    second = mapper.save(make_paid_cash_sale())

    assert first != second
