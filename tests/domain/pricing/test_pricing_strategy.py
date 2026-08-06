import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.cash_payment import CashPayment
from supermarket_pos.domain.pricing.full_pricing_strategy import FullPricingStrategy
from supermarket_pos.domain.pricing.percentage_discount_pricing_strategy import (
    PercentageDiscountPricingStrategy,
)
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.sales.sale import Sale


@pytest.fixture
def bread() -> ProductDescription:
    return ProductDescription("SKU-003", "Loaf of Bread", Money("18.00"))


@pytest.fixture
def oil() -> ProductDescription:
    return ProductDescription("SKU-002", "1L Cooking Oil", Money("65.50"))


class TestFullPricingStrategy:
    def test_default_sale_uses_full_pricing_strategy(self, bread):
        sale = Sale()

        assert isinstance(sale.pricing_strategy, FullPricingStrategy)

    def test_full_pricing_strategy_charges_the_full_subtotal(self, bread, oil):
        sale = Sale(FullPricingStrategy())
        sale.make_line_item(bread, 1)
        sale.make_line_item(oil, 2)

        assert sale.get_total() == sale.get_subtotal() == Money("149.00")


class TestPercentageDiscountPricingStrategy:
    def test_ten_percent_discount_reduces_total(self, bread):
        sale = Sale(PercentageDiscountPricingStrategy("10"))
        sale.make_line_item(bread, 1)

        assert sale.get_subtotal() == Money("18.00")
        assert sale.get_total() == Money("16.20")

    def test_zero_percent_discount_matches_subtotal(self, bread):
        sale = Sale(PercentageDiscountPricingStrategy("0"))
        sale.make_line_item(bread, 1)

        assert sale.get_total() == sale.get_subtotal()

    def test_hundred_percent_discount_gives_free_sale(self, bread):
        sale = Sale(PercentageDiscountPricingStrategy("100"))
        sale.make_line_item(bread, 2)

        assert sale.get_total() == Money("0.00")

    @pytest.mark.parametrize("bad_percentage", ["-5", "100.01", "150"])
    def test_out_of_range_percentage_raises(self, bad_percentage):
        with pytest.raises(ValueError):
            PercentageDiscountPricingStrategy(bad_percentage)

    def test_set_pricing_strategy_swaps_strategy_on_existing_sale(self, bread):
        sale = Sale()
        sale.make_line_item(bread, 1)
        assert sale.get_total() == Money("18.00")

        sale.set_pricing_strategy(PercentageDiscountPricingStrategy("50"))

        assert sale.get_total() == Money("9.00")

    def test_discount_applies_to_subtotal_not_running_total_twice(self, bread, oil):
        """Regression guard: get_total() must not accumulate discounts
        across repeated calls (Strategy recomputes from get_subtotal()
        each time, it does not mutate state)."""
        sale = Sale(PercentageDiscountPricingStrategy("10"))
        sale.make_line_item(bread, 1)
        sale.make_line_item(oil, 1)

        first_call = sale.get_total()
        second_call = sale.get_total()

        assert first_call == second_call == Money("75.15")

    def test_get_balance_reflects_discounted_total(self, bread):
        sale = Sale(PercentageDiscountPricingStrategy("10"))
        sale.make_line_item(bread, 1)  # subtotal 18.00, discounted 16.20
        sale.become_complete()

        sale.make_payment(CashPayment(Money("20.00")))

        assert sale.get_balance() == Money("3.80")
