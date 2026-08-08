import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.persistence_facade import PersistenceFacade
from supermarket_pos.persistence.product_description_mapper import ProductDescriptionMapper
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


@pytest.fixture
def facade() -> PersistenceFacade:
    mapper = ProductDescriptionMapper(SQLiteConnection(":memory:"))
    return PersistenceFacade({ProductDescription: mapper})


def test_save_delegates_to_the_mapper_for_the_object_s_type(facade):
    description = ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00"))

    oid = facade.save(description)

    assert oid == OID("SKU-001")


def test_get_delegates_to_the_mapper_for_the_requested_class(facade):
    description = ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00"))
    facade.save(description)

    fetched = facade.get(OID("SKU-001"), ProductDescription)

    assert fetched == description


def test_get_all_delegates_to_the_mapper_for_the_requested_class(facade):
    facade.save(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    facade.save(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")))

    all_products = facade.get_all(ProductDescription)

    assert len(all_products) == 2


def test_delete_delegates_to_the_mapper_for_the_requested_class(facade):
    facade.save(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    facade.delete(OID("SKU-001"), ProductDescription)

    assert facade.get_all(ProductDescription) == []


def test_unregistered_class_raises_a_clear_error(facade):
    class SomeUnmappedType:
        pass

    with pytest.raises(ValueError, match="No mapper registered"):
        facade.get_all(SomeUnmappedType)
