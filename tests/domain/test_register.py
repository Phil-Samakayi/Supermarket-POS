import pytest

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.gateway.airtel_money_adapter import AirtelMoneyAdapter
from supermarket_pos.domain.payment.gateway.card_processor_adapter import CardProcessorAdapter
from supermarket_pos.domain.payment.gateway.mtn_momo_adapter import MTNMoMoAdapter
from supermarket_pos.domain.payment.gateway.unknown_payment_provider_error import (
    UnknownPaymentProviderError,
)
from supermarket_pos.domain.payment.gateway.payment_gateway_factory import PaymentGatewayFactory
from supermarket_pos.domain.payment.gateway.payment_service_proxy import PaymentServiceProxy
from supermarket_pos.domain.payment.payment_declined_error import PaymentDeclinedError
from supermarket_pos.domain.product.exceptions import ProductNotFoundError
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.store import Store


@pytest.fixture
def store() -> Store:
    store = Store("Test Store", "Test Address")
    store.catalog.add_product(
        ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00"))
    )
    return store


def test_process_sale_cash_happy_path_produces_correct_change_and_logs_sale(store):
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 2)

    total = register.end_sale()
    assert total == Money("170.00")

    change = register.make_cash_payment(Money("200.00"))
    assert change == Money("30.00")
    assert len(store.completed_sales) == 1


def test_enter_item_running_total_updates_after_each_item(store):
    register = store.register
    register.make_new_sale()

    result = register.enter_item("SKU-001", 1)

    assert result.running_total == Money("85.00")
    assert result.description.item_id == "SKU-001"
    assert result.quantity == 1


def test_enter_item_unknown_item_id_raises_product_not_found(store):
    register = store.register
    register.make_new_sale()

    with pytest.raises(ProductNotFoundError):
        register.enter_item("UNKNOWN", 1)


def test_each_new_sale_starts_with_a_clean_total(store):
    register = store.register

    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()
    register.make_cash_payment(Money("100.00"))

    register.make_new_sale()
    assert register.current_sale.get_total() == Money("0.00")


def test_process_sale_mobile_money_happy_path_produces_correct_change_and_logs_sale(store):
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    change = register.make_mobile_money_payment("mtn", "0977123456", Money("85.00"))

    assert change == Money("0.00")
    assert len(store.completed_sales) == 1


def test_process_sale_card_happy_path_produces_correct_change_and_logs_sale(store):
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 2)
    register.end_sale()

    change = register.make_card_payment("4111111111111111", Money("170.00"))

    assert change == Money("0.00")
    assert len(store.completed_sales) == 1


def test_declined_mobile_money_payment_raises_and_does_not_log_sale(store):
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    with pytest.raises(PaymentDeclinedError):
        register.make_mobile_money_payment(
            "mtn", MTNMoMoAdapter.DECLINE_TEST_MSISDN, Money("85.00")
        )

    assert len(store.completed_sales) == 0


def test_declined_airtel_payment_raises_payment_declined_error(store):
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    with pytest.raises(PaymentDeclinedError):
        register.make_mobile_money_payment(
            "airtel", AirtelMoneyAdapter.DECLINE_TEST_MSISDN, Money("85.00")
        )


def test_declined_card_payment_raises_payment_declined_error(store):
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    with pytest.raises(PaymentDeclinedError):
        register.make_card_payment(
            CardProcessorAdapter.DECLINE_TEST_CARD_REFERENCE, Money("85.00")
        )


def test_cashier_can_retry_with_a_different_payment_method_after_a_decline(store):
    """Realizes UC1's 'Customer says they intended to pay by X but it's
    declined; Cashier asks for alternate payment' extension: a decline
    must not lock out the sale or double-log it."""
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    with pytest.raises(PaymentDeclinedError):
        register.make_mobile_money_payment(
            "mtn", MTNMoMoAdapter.DECLINE_TEST_MSISDN, Money("85.00")
        )

    change = register.make_cash_payment(Money("100.00"))

    assert change == Money("15.00")
    assert len(store.completed_sales) == 1


def test_unknown_mobile_money_provider_raises(store):
    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    with pytest.raises(UnknownPaymentProviderError):
        register.make_mobile_money_payment("zamtel-kwacha", "0977123456", Money("85.00"))


# --- Offline failover (PaymentServiceProxy + OfflineSyncQueue) -----------
#
# These tests use their own PaymentGatewayFactory (not the process-wide
# singleton) so toggling simulated connectivity here can't affect any
# other test in the suite.

@pytest.fixture
def isolated_store():
    """Yields (store, factory) so a test can reach into the factory to
    flip a provider's simulated connectivity via
    factory.get_mobile_money_adapter(x).real_adapter.client.set_outage()."""
    factory = PaymentGatewayFactory()
    store = Store("Test Store", "Test Address", payment_gateway_factory=factory)
    store.catalog.add_product(
        ProductDescription("SKU-001", "2kg Mealie Meal", Money("85.00"))
    )
    return store, factory


def test_mobile_money_payment_still_completes_the_sale_when_gateway_is_unreachable(
    isolated_store,
):
    store, factory = isolated_store
    mtn_proxy = factory.get_mobile_money_adapter("mtn")
    assert isinstance(mtn_proxy, PaymentServiceProxy)
    mtn_proxy.real_adapter.client.set_outage(True)

    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    change = register.make_mobile_money_payment("mtn", "0977123456", Money("85.00"))

    assert change == Money("0.00")
    assert len(store.completed_sales) == 1
    assert len(register.offline_queue) == 1

    payment = store.completed_sales[0].payment
    assert payment.authorization_result.pending is True


def test_offline_payments_do_not_raise_payment_declined_error(isolated_store):
    """A pending (queued) authorization is a provisional *approval*,
    not a decline — the cashier must not be told to try another
    payment method for something that's simply waiting to be
    confirmed."""
    store, factory = isolated_store
    factory.get_mobile_money_adapter("airtel").real_adapter.client.set_outage(True)

    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    # Must not raise.
    register.make_mobile_money_payment("airtel", "0966987654", Money("85.00"))


def test_card_payment_still_raises_gateway_unavailable_error_when_unreachable(isolated_store):
    """Card payments are deliberately NOT proxied — no offline
    fallback exists for card, so the failure must propagate."""
    from supermarket_pos.domain.payment.gateway.gateway_unavailable_error import (
        GatewayUnavailableError,
    )

    store, factory = isolated_store
    card_adapter = factory.get_card_adapter()
    assert not isinstance(card_adapter, PaymentServiceProxy)
    assert isinstance(card_adapter, CardProcessorAdapter)

    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()

    # Simulate outage directly on the card adapter's client — card has
    # no Proxy to reach through by design (see this adapter's docstring).
    card_adapter.client.set_outage(True)

    with pytest.raises(GatewayUnavailableError):
        register.make_card_payment("4111111111111111", Money("85.00"))


def test_sync_offline_payments_confirms_queued_payment_once_gateway_recovers(isolated_store):
    store, factory = isolated_store
    mtn_proxy = factory.get_mobile_money_adapter("mtn")
    mtn_proxy.real_adapter.client.set_outage(True)

    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()
    register.make_mobile_money_payment("mtn", "0977123456", Money("85.00"))

    assert len(register.offline_queue) == 1

    mtn_proxy.real_adapter.client.set_outage(False)  # connectivity restored
    report = store.sync_offline_payments()

    assert len(report.confirmed) == 1
    assert report.confirmed[0][1].approved is True
    assert not report.has_outstanding_work
    assert len(register.offline_queue) == 0


def test_sync_offline_payments_leaves_still_unreachable_ones_queued(isolated_store):
    store, factory = isolated_store
    factory.get_mobile_money_adapter("mtn").real_adapter.client.set_outage(True)

    register = store.register
    register.make_new_sale()
    register.enter_item("SKU-001", 1)
    register.end_sale()
    register.make_mobile_money_payment("mtn", "0977123456", Money("85.00"))

    report = store.sync_offline_payments()  # still offline

    assert report.confirmed == ()
    assert report.has_outstanding_work
    assert len(register.offline_queue) == 1
