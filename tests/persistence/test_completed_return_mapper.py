import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.returns.cash_refund import CashRefund
from supermarket_pos.domain.returns.sale_return import SaleReturn
from supermarket_pos.persistence.completed_return_mapper import CompletedReturnMapper
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


@pytest.fixture
def mapper() -> CompletedReturnMapper:
    return CompletedReturnMapper(SQLiteConnection(":memory:"))


def make_refunded_return() -> SaleReturn:
    sale_return = SaleReturn()
    sale_return.make_line_item(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")), 1)
    sale_return.make_line_item(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")), 2)
    sale_return.become_complete()
    sale_return.make_refund(CashRefund(sale_return.get_total()))
    return sale_return


def test_save_unrefunded_return_raises():
    mapper = CompletedReturnMapper(SQLiteConnection(":memory:"))
    sale_return = SaleReturn()
    sale_return.make_line_item(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")), 1)
    sale_return.become_complete()

    with pytest.raises(ValueError, match="no refund"):
        mapper.save(sale_return)


def test_save_then_get_round_trips_total_refund(mapper):
    sale_return = make_refunded_return()

    oid = mapper.save(sale_return)
    record = mapper.get(oid)

    assert record.total_refund == Money("216.00")


def test_save_then_get_round_trips_line_items(mapper):
    sale_return = make_refunded_return()

    oid = mapper.save(sale_return)
    record = mapper.get(oid)

    assert len(record.line_items) == 2
    assert record.line_items[0].item_id == "SKU-001"
    assert record.line_items[0].quantity == 1
    assert record.line_items[1].item_id == "SKU-002"
    assert record.line_items[1].subtotal == Money("131.00")


def test_get_all_returns_every_saved_return(mapper):
    mapper.save(make_refunded_return())
    mapper.save(make_refunded_return())

    assert len(mapper.get_all()) == 2


def test_get_with_unknown_oid_raises(mapper):
    with pytest.raises(ValueError, match="No completed return"):
        mapper.get(OID("does-not-exist"))
