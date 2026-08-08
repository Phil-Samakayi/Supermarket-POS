from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.store import Store
from supermarket_pos.persistence.sqlite_persistence_factory import build_sqlite_persistence_facade


def test_store_without_a_persistence_facade_is_purely_in_memory():
    store = Store("Test Store", "Test Address")
    store.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    assert len(store.catalog) == 1


def test_direct_catalog_add_product_still_works_without_persistence():
    """The pre-Iteration-3 way of adding products to a test store must
    remain valid and unaffected."""
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    assert len(store.catalog) == 1


def test_add_product_persists_when_store_has_a_persistence_facade(tmp_path):
    facade = build_sqlite_persistence_facade(str(tmp_path / "store.db"))
    store = Store("Test Store", "Test Address", persistence_facade=facade)

    store.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    assert len(facade.get_all(ProductDescription)) == 1


def test_store_start_up_loads_previously_persisted_products(tmp_path):
    db_path = str(tmp_path / "store.db")

    first_store = Store(
        "Test Store", "Test Address", persistence_facade=build_sqlite_persistence_facade(db_path)
    )
    first_store.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    # A fresh Store instance, as if the app were restarted, wired to
    # the same underlying database.
    second_store = Store(
        "Test Store", "Test Address", persistence_facade=build_sqlite_persistence_facade(db_path)
    )

    assert len(second_store.catalog) == 1
    assert second_store.catalog.get_product_description("SKU-001").description == "2kg Mealie Meal"


def test_direct_catalog_add_product_does_not_persist_even_with_a_facade(tmp_path):
    """add_product() on Store is the persistence-aware entry point;
    reaching into store.catalog directly stays in-memory-only even
    when a facade is present — this is a deliberate seam, not a bug,
    documented on Store.add_product()."""
    facade = build_sqlite_persistence_facade(str(tmp_path / "store.db"))
    store = Store("Test Store", "Test Address", persistence_facade=facade)

    store.catalog.add_product(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")))

    assert len(store.catalog) == 1
    assert facade.get_all(ProductDescription) == []


def test_store_exposes_name_and_address():
    store = Store("Lusaka Central Supermarket", "Cairo Road, Lusaka")

    assert store.name == "Lusaka Central Supermarket"
    assert store.address == "Cairo Road, Lusaka"
