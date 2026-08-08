from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.persistence.sqlite_persistence_factory import build_sqlite_persistence_facade


def test_build_sqlite_persistence_facade_wires_a_working_product_description_mapper(tmp_path):
    db_path = str(tmp_path / "test.db")
    facade = build_sqlite_persistence_facade(db_path)

    facade.save(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    assert len(facade.get_all(ProductDescription)) == 1


def test_data_survives_across_separate_connections_to_the_same_file(tmp_path):
    """The actual point of file-backed SQLite over :memory: — proves
    this isn't just testing the in-process cache."""
    db_path = str(tmp_path / "test.db")

    first_facade = build_sqlite_persistence_facade(db_path)
    first_facade.save(ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00")))

    second_facade = build_sqlite_persistence_facade(db_path)
    products = second_facade.get_all(ProductDescription)

    assert len(products) == 1
    assert products[0].item_id == "SKU-001"
