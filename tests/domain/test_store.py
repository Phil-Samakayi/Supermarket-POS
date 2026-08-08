from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.store import Store
from supermarket_pos.persistence.sqlite_persistence_factory import build_sqlite_persistence_facade
from supermarket_pos.persistence.sqlite_sale_history_factory import build_sqlite_sale_history_mapper


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


# --- Sale history (CompletedSaleMapper) -----------------------------------

def test_sale_history_is_empty_without_a_sale_history_mapper():
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()
    register.make_cash_payment(Money("100.00"))

    assert store.sale_history() == []


def test_completed_sale_is_persisted_and_shows_up_in_sale_history(tmp_path):
    mapper = build_sqlite_sale_history_mapper(str(tmp_path / "store.db"))
    store = Store("Test Store", "Test Address", sale_history_mapper=mapper)
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 2)
    register.end_sale()
    register.make_cash_payment(Money("200.00"))

    history = store.sale_history()

    assert len(history) == 1
    assert history[0].total == Money("170.00")
    assert history[0].payment_method == "cash"
    assert history[0].change_due == Money("30.00")


def test_sale_history_survives_a_restart(tmp_path):
    db_path = str(tmp_path / "store.db")

    first_store = Store(
        "Test Store", "Test Address", sale_history_mapper=build_sqlite_sale_history_mapper(db_path)
    )
    first_store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = first_store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()
    register.make_cash_payment(Money("100.00"))

    # Fresh Store, as if the app restarted, wired to the same file.
    second_store = Store(
        "Test Store", "Test Address", sale_history_mapper=build_sqlite_sale_history_mapper(db_path)
    )

    history = second_store.sale_history()
    assert len(history) == 1
    assert history[0].total == Money("85.00")


def test_completed_sales_property_is_unaffected_by_sale_history_mapper(tmp_path):
    """completed_sales stays this session's live Sale objects,
    regardless of whether persistence is wired up — the two concepts
    are deliberately distinct (see Store's docstring)."""
    mapper = build_sqlite_sale_history_mapper(str(tmp_path / "store.db"))
    store = Store("Test Store", "Test Address", sale_history_mapper=mapper)
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()
    register.make_cash_payment(Money("100.00"))

    assert len(store.completed_sales) == 1
    from supermarket_pos.domain.sales.sale import Sale
    assert isinstance(store.completed_sales[0], Sale)
