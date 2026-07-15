"""
Iteration-1 demo: Start Up + Process Sale (cash payment, happy path).

Simulates UC1's main success scenario (steps 1-12) ending in extension
9a (paying by cash). A real UI (desktop or web) replaces this console
driver in a later iteration; per Larman, the domain layer is built and
proven first, independent of whatever UI technology is chosen later.
"""
from __future__ import annotations

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.register import LineItemResult, Register
from supermarket_pos.domain.store import Store


def seed_catalog(store: Store) -> None:
    """Start Up use case: populate the catalog before the store opens."""
    store.catalog.add_product(
        ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00"))
    )
    store.catalog.add_product(
        ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50"))
    )
    store.catalog.add_product(
        ProductDescription("SKU-003", "Loaf of Bread", Money("18.00"))
    )


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


def main() -> None:
    # --- Start Up use case ---
    store = Store("Supermarket POS - Demo Branch", "Lusaka, Zambia")
    seed_catalog(store)

    print(f"=== {store.name} ===")

    # --- Process Sale: main success scenario, cash payment (9a) ---
    process_demo_sale(store.register)

    print(f"Sale complete. Receipt logged for {store.name}.")
    print(f"Sales logged so far: {len(store.completed_sales)}")


if __name__ == "__main__":
    main()
