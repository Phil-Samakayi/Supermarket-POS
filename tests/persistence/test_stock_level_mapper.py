import pytest

from supermarket_pos.domain.inventory.stock_level import StockLevel
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection
from supermarket_pos.persistence.stock_level_mapper import StockLevelMapper


@pytest.fixture
def mapper() -> StockLevelMapper:
    return StockLevelMapper(SQLiteConnection(":memory:"))


def test_save_then_get_round_trips(mapper):
    oid = mapper.save(StockLevel("SKU-001", 25))

    fetched = mapper.get(oid)

    assert fetched == StockLevel("SKU-001", 25)


def test_get_unknown_oid_raises(mapper):
    with pytest.raises(ValueError, match="No stock level"):
        mapper.get(OID("SKU-999"))


def test_save_is_an_upsert(mapper):
    mapper.save(StockLevel("SKU-001", 25))
    mapper.save(StockLevel("SKU-001", 40))

    all_levels = mapper.get_all()

    assert len(all_levels) == 1
    assert all_levels[0].quantity_on_hand == 40


def test_get_all_ordered_by_item_id(mapper):
    mapper.save(StockLevel("SKU-002", 10))
    mapper.save(StockLevel("SKU-001", 5))

    all_levels = mapper.get_all()

    assert [level.item_id for level in all_levels] == ["SKU-001", "SKU-002"]


def test_delete_removes_the_stock_level(mapper):
    oid = mapper.save(StockLevel("SKU-001", 25))

    mapper.delete(oid)

    with pytest.raises(ValueError, match="No stock level"):
        mapper.get(oid)
