"""ProductCatalog: Information Expert for ProductDescription lookups."""
from __future__ import annotations

from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.product.product_description import ProductDescription


class ProductCatalog:
    """
    GRASP: Information Expert for ProductDescription lookups by item ID
    (Domain Model: Store "maintains" ProductCatalog "records" ProductDescription).

    Iteration-1: a simple in-memory catalog, seeded manually at Start Up.
    Iteration-2 will back this with a database-backed mapper / repository,
    without changing this class's public interface.
    """

    def __init__(self) -> None:
        self._descriptions: dict[str, ProductDescription] = {}

    def add_product(self, description: ProductDescription) -> None:
        self._descriptions[description.item_id] = description

    def get_product_description(self, item_id: str) -> ProductDescription:
        try:
            return self._descriptions[item_id]
        except KeyError:
            raise ProductNotFoundError(item_id) from None

    def __len__(self) -> int:
        return len(self._descriptions)
