import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.store import Store


@pytest.fixture
def store() -> Store:
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(
        ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00"))
    )
    return store


def test_process_sale_cash_happy_path_produces_correct_change_and_logs_sale(store):
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 2)

    total = register.end_sale()
    assert total == Money("170.00")

    change = register.make_cash_payment(Money("200.00"))
    assert change == Money("30.00")
    assert len(store.completed_sales) == 1


def test_enter_item_running_total_updates_after_each_item(store):
    register = store.register
    register.make_new_sale()

    result = register.enter_item("SKU-001", 1)

    assert result.running_total == Money("85.00")
    assert result.description.item_id == "SKU-001"
    assert result.quantity == 1


def test_enter_item_unknown_item_id_raises_product_not_found(store):
    register = store.register
    register.make_new_sale()

    with pytest.raises(ProductNotFoundError):
        register.enter_item("UNKNOWN", 1)


def test_each_new_sale_starts_with_a_clean_total(store):
    register = store.register

    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()
    register.make_cash_payment(Money("100.00"))

    register.make_new_sale()
    assert register.current_sale.get_total() == Money("0.00")
