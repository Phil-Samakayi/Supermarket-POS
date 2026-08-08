import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.product.product_catalog import ProductCatalog
from supermarket_pos.domain.product.product_description import ProductDescription


@pytest.fixture
def catalog() -> ProductCatalog:
    return ProductCatalog()


def test_add_product_then_get_by_id(catalog):
    description = ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00"))
    catalog.add_product(description)

    assert catalog.get_product_description("SKU-001") == description


def test_get_unknown_item_id_raises(catalog):
    with pytest.raises(ProductNotFoundError):
        catalog.get_product_description("SKU-999")


def test_all_products_returns_every_product_ordered_by_item_id(catalog):
    catalog.add_product(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")))
    catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    products = catalog.all_products()

    assert [p.item_id for p in products] == ["SKU-001", "SKU-002"]


def test_all_products_on_empty_catalog_is_empty(catalog):
    assert catalog.all_products() == []


def test_len_reflects_number_of_products(catalog):
    catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    assert len(catalog) == 1
