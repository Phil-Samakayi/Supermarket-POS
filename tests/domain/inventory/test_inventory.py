import pytest

from supermarket_pos.domain.inventory.inventory import Inventory


@pytest.fixture
def inventory() -> Inventory:
    return Inventory()


def test_unknown_item_has_implicit_zero_quantity(inventory):
    assert inventory.get_quantity("SKU-001") == 0


def test_increase_adds_to_the_current_quantity(inventory):
    inventory.increase("SKU-001", 10)
    inventory.increase("SKU-001", 5)

    assert inventory.get_quantity("SKU-001") == 15


def test_increase_with_non_positive_quantity_raises(inventory):
    with pytest.raises(ValueError, match="must be positive"):
        inventory.increase("SKU-001", 0)


def test_adjust_can_increase_or_decrease(inventory):
    inventory.increase("SKU-001", 10)

    inventory.adjust("SKU-001", -3)

    assert inventory.get_quantity("SKU-001") == 7


def test_adjust_below_zero_raises_and_does_not_change_quantity(inventory):
    inventory.increase("SKU-001", 5)

    with pytest.raises(ValueError, match="below zero"):
        inventory.adjust("SKU-001", -10)

    assert inventory.get_quantity("SKU-001") == 5


def test_set_quantity_overwrites_directly(inventory):
    inventory.set_quantity("SKU-001", 42)

    assert inventory.get_quantity("SKU-001") == 42


def test_set_quantity_negative_raises(inventory):
    with pytest.raises(ValueError, match="cannot be negative"):
        inventory.set_quantity("SKU-001", -1)


def test_items_at_or_below_threshold_includes_zero_stock_items(inventory):
    inventory.increase("SKU-001", 2)
    inventory.increase("SKU-002", 20)

    low = inventory.items_at_or_below(5)

    assert low == ["SKU-001"]


def test_items_at_or_below_is_sorted(inventory):
    inventory.increase("SKU-002", 1)
    inventory.increase("SKU-001", 1)

    assert inventory.items_at_or_below(5) == ["SKU-001", "SKU-002"]


def test_len_counts_items_with_a_recorded_stock_level(inventory):
    inventory.increase("SKU-001", 1)
    inventory.increase("SKU-002", 1)

    assert len(inventory) == 2
