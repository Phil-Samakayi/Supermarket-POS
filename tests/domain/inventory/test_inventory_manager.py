import pytest

from supermarket_pos.domain.inventory.inventory_manager import InventoryManager
from supermarket_pos.persistence.sqlite_persistence_factory import build_sqlite_persistence_facade


def test_receive_stock_on_a_new_item_starts_from_zero():
    manager = InventoryManager()

    new_quantity = manager.receive_stock("SKU-001", 20)

    assert new_quantity == 20
    assert manager.get_stock_level("SKU-001") == 20


def test_receive_stock_accumulates():
    manager = InventoryManager()
    manager.receive_stock("SKU-001", 20)

    manager.receive_stock("SKU-001", 5)

    assert manager.get_stock_level("SKU-001") == 25


def test_adjust_stock_can_decrease():
    manager = InventoryManager()
    manager.receive_stock("SKU-001", 20)

    new_quantity = manager.adjust_stock("SKU-001", -3)

    assert new_quantity == 17


def test_adjust_stock_below_zero_raises():
    manager = InventoryManager()
    manager.receive_stock("SKU-001", 5)

    with pytest.raises(ValueError, match="below zero"):
        manager.adjust_stock("SKU-001", -10)


def test_get_stock_level_for_unknown_item_is_zero():
    manager = InventoryManager()

    assert manager.get_stock_level("SKU-999") == 0


def test_low_stock_items_reflects_current_quantities():
    manager = InventoryManager()
    manager.receive_stock("SKU-001", 2)
    manager.receive_stock("SKU-002", 50)

    assert manager.low_stock_items(threshold=5) == ["SKU-001"]


def test_stock_persists_when_manager_has_a_persistence_facade(tmp_path):
    facade = build_sqlite_persistence_facade(str(tmp_path / "store.db"))
    manager = InventoryManager(facade)

    manager.receive_stock("SKU-001", 20)

    from supermarket_pos.domain.inventory.stock_level import StockLevel

    persisted = facade.get_all(StockLevel)
    assert len(persisted) == 1
    assert persisted[0].quantity_on_hand == 20


def test_inventory_manager_loads_persisted_stock_on_construction(tmp_path):
    db_path = str(tmp_path / "store.db")

    first_manager = InventoryManager(build_sqlite_persistence_facade(db_path))
    first_manager.receive_stock("SKU-001", 20)

    second_manager = InventoryManager(build_sqlite_persistence_facade(db_path))

    assert second_manager.get_stock_level("SKU-001") == 20


def test_adjust_stock_persists_the_new_quantity(tmp_path):
    db_path = str(tmp_path / "store.db")
    manager = InventoryManager(build_sqlite_persistence_facade(db_path))
    manager.receive_stock("SKU-001", 20)

    manager.adjust_stock("SKU-001", -5)

    reloaded = InventoryManager(build_sqlite_persistence_facade(db_path))
    assert reloaded.get_stock_level("SKU-001") == 15
