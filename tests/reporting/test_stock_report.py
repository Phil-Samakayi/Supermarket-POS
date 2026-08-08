from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.inventory.inventory_manager import InventoryManager
from supermarket_pos.domain.product.product_catalog import ProductCatalog
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.reporting.stock_report import build_stock_summary_report


def test_empty_catalog_produces_an_empty_report():
    report = build_stock_summary_report(ProductCatalog(), InventoryManager())

    assert report.rows == ()


def test_one_row_per_catalog_product_with_current_quantity():
    catalog = ProductCatalog()
    catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    inventory_manager = InventoryManager()
    inventory_manager.receive_stock("SKU-001", 12)

    report = build_stock_summary_report(catalog, inventory_manager)

    assert len(report.rows) == 1
    assert report.rows[0].item_id == "SKU-001"
    assert report.rows[0].quantity_on_hand == 12


def test_product_with_no_stock_level_shows_zero_and_counts_as_low_stock():
    catalog = ProductCatalog()
    catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    report = build_stock_summary_report(catalog, InventoryManager())

    assert report.rows[0].quantity_on_hand == 0
    assert report.rows[0].is_low_stock is True


def test_is_low_stock_flag_respects_the_threshold():
    catalog = ProductCatalog()
    catalog.add_product(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))
    catalog.add_product(ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50")))
    inventory_manager = InventoryManager()
    inventory_manager.receive_stock("SKU-001", 3)
    inventory_manager.receive_stock("SKU-002", 50)

    report = build_stock_summary_report(catalog, inventory_manager, low_stock_threshold=5)

    by_id = {row.item_id: row for row in report.rows}
    assert by_id["SKU-001"].is_low_stock is True
    assert by_id["SKU-002"].is_low_stock is False


def test_report_records_the_threshold_used():
    report = build_stock_summary_report(ProductCatalog(), InventoryManager(), low_stock_threshold=10)

    assert report.low_stock_threshold == 10
