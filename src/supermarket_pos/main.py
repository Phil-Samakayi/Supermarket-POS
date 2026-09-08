"""
Supermarket POS entry point.

Launches the Tkinter checkout UI by default.
Use --console for the original text-only demo.
"""
from __future__ import annotations

import argparse

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.register import LineItemResult, Register
from supermarket_pos.domain.store import Store


def seed_catalog(store: Store) -> None:
    products = [
        ("SKU-001", "2kg Mealie Meal", "85.00"),
        ("SKU-002", "1L Cooking Oil", "65.50"),
        ("SKU-003", "Loaf of Bread", "18.00"),
        ("SKU-004", "500g Sugar", "32.00"),
        ("SKU-005", "1L Fresh Milk", "22.50"),
        ("SKU-006", "Bar of Soap", "15.00"),
        ("SKU-007", "Pack of Eggs (12)", "45.00"),
        ("SKU-008", "2L Soft Drink", "28.00"),
    ]
    for item_id, desc, price in products:
        store.catalog.add_product(ProductDescription(item_id, desc, Money(price)))

    for item_id, _, _ in products:
        store.inventory.receive_stock(item_id, 50)


def print_line_item(result: LineItemResult) -> None:
    print(
        f"  {result.quantity}x {result.description.description} "
        f"({result.description.item_id}) -> running total: {result.running_total}"
    )


def process_demo_sale(register: Register) -> None:
    register.make_new_sale()
    print_line_item(register.enter_item("SKU-001", 2))
    print_line_item(register.enter_item("SKU-002", 1))
    total = register.end_sale()
    print(f"Total due: {total}")
    tendered = Money("300.00")
    change = register.make_cash_payment(tendered)
    print(f"Amount tendered: {tendered}")
    print(f"Change due: {change}")


def run_console_demo() -> None:
    store = Store("Supermarket POS - Demo Branch", "Lusaka, Zambia")
    seed_catalog(store)
    print(f"=== {store.name} ===")
    process_demo_sale(store.register)
    print(f"Sale complete. Sales logged: {len(store.completed_sales)}")
    print(f"Stock of SKU-001 after sale: {store.inventory.get_stock_level('SKU-001')}")


def run_gui() -> None:
    from supermarket_pos.ui.checkout_screen import CheckoutScreen

    store = Store("Pick n Pay POS — Demo Branch", "Lusaka, Zambia")
    seed_catalog(store)
    app = CheckoutScreen(store)
    app.run()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Supermarket POS")
    parser.add_argument(
        "--console",
        action="store_true",
        help="Run the original text-only demo instead of the GUI",
    )
    args = parser.parse_args(argv)

    if args.console:
        run_console_demo()
    else:
        run_gui()


if __name__ == "__main__":
    main()