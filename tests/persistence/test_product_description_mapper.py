import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.product_description_mapper import ProductDescriptionMapper
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


@pytest.fixture
def mapper() -> ProductDescriptionMapper:
    # Fresh in-memory database per test — SQLiteConnection holds one
    # open connection so ":memory:" actually persists across calls
    # within this fixture's lifetime.
    return ProductDescriptionMapper(SQLiteConnection(":memory:"))


def test_save_then_get_round_trips_the_product(mapper):
    description = ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00"))

    oid = mapper.save(description)
    fetched = mapper.get(oid)

    assert fetched == description


def test_get_with_unknown_oid_raises_product_not_found(mapper):
    with pytest.raises(ProductNotFoundError):
        mapper.get(OID("SKU-999"))


def test_get_all_returns_every_saved_product_ordered_by_item_id(mapper):
    mapper.save(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")))
    mapper.save(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    all_products = mapper.get_all()

    assert [p.item_id for p in all_products] == ["SKU-001", "SKU-002"]


def test_save_is_an_upsert_not_a_duplicate_insert(mapper):
    mapper.save(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    mapper.save(ProductDescription("SKU-001", "2kg Mealie Meal (relabelled)", Money("90.00")))

    all_products = mapper.get_all()

    assert len(all_products) == 1
    assert all_products[0].description == "2kg Mealie Meal (relabelled)"
    assert all_products[0].price == Money("90.00")


def test_delete_removes_the_product(mapper):
    oid = mapper.save(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    mapper.delete(oid)

    with pytest.raises(ProductNotFoundError):
        mapper.get(oid)


def test_price_survives_round_trip_at_full_precision(mapper):
    """A regression guard against float drift — Money is Decimal-backed
    and the mapper must preserve that through the TEXT column."""
    description = ProductDescription("SKU-003", "Sugar 2kg", Money("47.35"))

    mapper.save(description)
    fetched = mapper.get(OID("SKU-003"))

    assert fetched.price == Money("47.35")
    assert str(fetched.price.amount) == "47.35"
