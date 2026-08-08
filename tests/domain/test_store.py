import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.store import Store
from supermarket_pos.persistence.sqlite_persistence_factory import build_sqlite_persistence_facade
from supermarket_pos.persistence.sqlite_return_history_factory import build_sqlite_return_history_mapper
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


# --- Return history (CompletedReturnMapper) --------------------------------

def test_return_history_is_empty_without_a_return_history_mapper():
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = store.register
    register.start_return()
    register.enter_return_item("SKU-001", 1)
    register.end_return()
    register.make_cash_refund()

    assert store.return_history() == []


def test_completed_return_is_persisted_and_shows_up_in_return_history(tmp_path):
    mapper = build_sqlite_return_history_mapper(str(tmp_path / "store.db"))
    store = Store("Test Store", "Test Address", return_history_mapper=mapper)
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = store.register
    register.start_return()
    register.enter_return_item("SKU-001", 2)
    register.end_return()
    register.make_cash_refund()

    history = store.return_history()

    assert len(history) == 1
    assert history[0].total_refund == Money("170.00")


def test_return_history_survives_a_restart(tmp_path):
    db_path = str(tmp_path / "store.db")

    first_store = Store(
        "Test Store", "Test Address", return_history_mapper=build_sqlite_return_history_mapper(db_path)
    )
    first_store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = first_store.register
    register.start_return()
    register.enter_return_item("SKU-001", 1)
    register.end_return()
    register.make_cash_refund()

    second_store = Store(
        "Test Store", "Test Address", return_history_mapper=build_sqlite_return_history_mapper(db_path)
    )

    history = second_store.return_history()
    assert len(history) == 1
    assert history[0].total_refund == Money("85.00")


def test_completed_returns_property_is_unaffected_by_return_history_mapper(tmp_path):
    mapper = build_sqlite_return_history_mapper(str(tmp_path / "store.db"))
    store = Store("Test Store", "Test Address", return_history_mapper=mapper)
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = store.register
    register.start_return()
    register.enter_return_item("SKU-001", 1)
    register.end_return()
    register.make_cash_refund()

    assert len(store.completed_returns) == 1
    from supermarket_pos.domain.returns.sale_return import SaleReturn
    assert isinstance(store.completed_returns[0], SaleReturn)


# --- Reporting (SalesReportGenerator) --------------------------------------

def test_sales_summary_report_reflects_sales_and_returns(tmp_path):
    store = Store(
        "Test Store",
        "Test Address",
        sale_history_mapper=build_sqlite_sale_history_mapper(str(tmp_path / "store.db")),
        return_history_mapper=build_sqlite_return_history_mapper(str(tmp_path / "store.db")),
    )
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = store.register

    register.make_new_sale()
    register.enter_item("SKU-001", 2)
    register.end_sale()
    register.make_cash_payment(Money("200.00"))

    register.start_return()
    register.enter_return_item("SKU-001", 1)
    register.end_return()
    register.make_cash_refund()

    report = store.sales_summary_report()

    assert report.sale_count == 1
    assert report.return_count == 1
    assert report.gross_revenue == Money("170.00")
    assert report.total_refunds == Money("85.00")
    assert report.net_revenue == Money("85.00")
    assert report.revenue_by_payment_method == {"cash": Money("170.00")}


def test_sales_summary_report_is_zeroed_without_any_history_mappers():
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()
    register.make_cash_payment(Money("100.00"))

    report = store.sales_summary_report()

    assert report.sale_count == 0
    assert report.gross_revenue == Money("0.00")


def test_top_selling_items_reflects_persisted_sale_history(tmp_path):
    store = Store(
        "Test Store",
        "Test Address",
        sale_history_mapper=build_sqlite_sale_history_mapper(str(tmp_path / "store.db")),
    )
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    store.catalog.add_product(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")))
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 3)
    register.enter_item("SKU-002", 1)
    register.end_sale()
    register.make_cash_payment(Money("300.00"))

    rows = store.top_selling_items()

    assert rows[0].item_id == "SKU-001"
    assert rows[0].quantity_sold == 3


# --- Manage Inventory --------------------------------------------------

def test_receive_stock_via_store_inventory():
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    store.inventory.receive_stock("SKU-001", 20)

    assert store.inventory.get_stock_level("SKU-001") == 20


def test_inventory_persists_when_store_has_a_persistence_facade(tmp_path):
    facade = build_sqlite_persistence_facade(str(tmp_path / "store.db"))
    store = Store("Test Store", "Test Address", persistence_facade=facade)
    store.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    store.inventory.receive_stock("SKU-001", 20)

    second_store = Store(
        "Test Store", "Test Address", persistence_facade=build_sqlite_persistence_facade(str(tmp_path / "store.db"))
    )
    assert second_store.inventory.get_stock_level("SKU-001") == 20


def test_stock_summary_report_combines_catalog_and_inventory():
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    store.catalog.add_product(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")))
    store.inventory.receive_stock("SKU-001", 2)
    store.inventory.receive_stock("SKU-002", 50)

    report = store.stock_summary_report(low_stock_threshold=5)

    by_id = {row.item_id: row for row in report.rows}
    assert by_id["SKU-001"].is_low_stock is True
    assert by_id["SKU-002"].is_low_stock is False


def test_stock_summary_report_reflects_a_sale_only_if_manually_adjusted():
    """Documented scope cut: this slice does not auto-decrement stock
    on sale completion (see ARCHITECTURE.md) — ringing up a sale must
    not, by itself, move the stock summary."""
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    store.inventory.receive_stock("SKU-001", 20)

    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 5)
    register.end_sale()
    register.make_cash_payment(Money("100.00"))

    assert store.inventory.get_stock_level("SKU-001") == 20


# --- Manage Users / Authenticate User --------------------------------------

FAST_ITERATIONS = 1000  # test-speed only, see password_hasher.py


def make_fast_store(**kwargs) -> Store:
    from supermarket_pos.domain.users.user_manager import UserManager

    return Store(
        "Test Store",
        "Test Address",
        user_manager=UserManager(password_hash_iterations=FAST_ITERATIONS),
        **kwargs,
    )


def test_store_authenticate_delegates_to_authentication_service():
    store = make_fast_store()
    store.users.bootstrap_administrator("admin", "adminpass123")

    user = store.authenticate("admin", "adminpass123")

    assert user.username == "admin"


def test_store_authenticate_with_wrong_password_raises():
    from supermarket_pos.domain.users.exceptions import AuthenticationError

    store = make_fast_store()
    store.users.bootstrap_administrator("admin", "adminpass123")

    with pytest.raises(AuthenticationError):
        store.authenticate("admin", "wrongpassword")


def test_store_users_manager_is_a_separate_controller_from_register():
    from supermarket_pos.domain.users.user_manager import UserManager

    store = make_fast_store()

    assert isinstance(store.users, UserManager)
    assert store.users is not store.register


def test_users_persist_when_store_has_a_persistence_facade(tmp_path):
    from supermarket_pos.domain.users.user_manager import UserManager

    facade = build_sqlite_persistence_facade(str(tmp_path / "store.db"))
    store = Store(
        "Test Store",
        "Test Address",
        persistence_facade=facade,
        user_manager=UserManager(facade, password_hash_iterations=FAST_ITERATIONS),
    )

    store.users.bootstrap_administrator("admin", "adminpass123")

    second_manager = UserManager(
        build_sqlite_persistence_facade(str(tmp_path / "store.db")),
        password_hash_iterations=FAST_ITERATIONS,
    )
    assert second_manager.get_user("admin").username == "admin"
