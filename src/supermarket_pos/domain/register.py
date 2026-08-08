"""Register: GRASP Controller for the Process Sale system operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.card_payment import CardPayment
from supermarket_pos.domain.payment.cash_payment import CashPayment
from supermarket_pos.domain.payment.electronic_payment import ElectronicPayment
from supermarket_pos.domain.payment.gateway.offline_sync_queue import OfflineSyncQueue
from supermarket_pos.domain.payment.gateway.payment_gateway_factory import PaymentGatewayFactory
from supermarket_pos.domain.payment.mobile_money_payment import MobileMoneyPayment
from supermarket_pos.domain.payment.payment_declined_error import PaymentDeclinedError
from supermarket_pos.domain.product.product_catalog import ProductCatalog
from supermarket_pos.domain.product.product_description import ProductDescription
from supermarket_pos.domain.returns.cash_refund import CashRefund
from supermarket_pos.domain.returns.sale_return import SaleReturn
from supermarket_pos.domain.sales.sale import Sale

if TYPE_CHECKING:
    from supermarket_pos.domain.store import Store


@dataclass(frozen=True)
class LineItemResult:
    """Value object returned to the UI layer after enter_item() -
    everything a checkout screen needs to refresh its display."""

    description: ProductDescription
    quantity: int
    running_total: Money


@dataclass(frozen=True)
class ReturnLineItemResult:
    """Value object returned to the UI layer after enter_return_item()
    — mirrors LineItemResult for the Handle Returns flow."""

    description: ProductDescription
    quantity: int
    running_refund_total: Money


class Register:
    """
    GRASP: Controller for the system operations implied by UC1's SSDs
    (make_new_sale, enter_item, end_sale, make_cash_payment,
    make_mobile_money_payment, make_card_payment) — see
    docs/Supermarket_POS_UseCase_UML.docx, Section 4.

    Iteration-2: mobile money and card payments are authorized through
    IPaymentGatewayAdapter implementations resolved via
    PaymentGatewayFactory (GoF Adapter + Factory, Larman Ch.26).
    Register never constructs a concrete adapter itself — Low Coupling
    is preserved because adding a new provider only means editing the
    factory, not this class.

    Iteration-2b: PaymentGatewayFactory now hands back mobile money
    adapters wrapped in a PaymentServiceProxy (Larman Ch.35), which
    fails over to an offline queue when a gateway is unreachable
    instead of raising GatewayUnavailableError. Register did not need
    to change at all to get this — it still just calls authorize()
    without knowing whether a Proxy is involved (that's the point of
    Proxy). Card payments are NOT proxied, so a card GatewayUnavailableError
    still propagates uncaught here, by design — a card gateway that
    can't be reached must fail the payment, not defer it.
    Iteration-3: Handle Returns (cash-refund only for this slice — see
    ARCHITECTURE.md) follows the same Controller shape as Process
    Sale: start_return/enter_return_item/end_return/make_cash_refund
    mirror make_new_sale/enter_item/end_sale/make_cash_payment.
    """

    def __init__(
        self,
        store: "Store",
        catalog: ProductCatalog,
        payment_gateway_factory: Optional[PaymentGatewayFactory] = None,
    ) -> None:
        self._store = store
        self._catalog = catalog
        self._current_sale: Optional[Sale] = None
        self._current_return: Optional[SaleReturn] = None
        self._payment_gateway_factory = payment_gateway_factory or PaymentGatewayFactory.get_instance()

    def make_new_sale(self) -> None:
        self._current_sale = Sale()

    def enter_item(self, item_id: str, quantity: int) -> LineItemResult:
        description = self._catalog.get_product_description(item_id)
        self._current_sale.make_line_item(description, quantity)
        return LineItemResult(
            description=description,
            quantity=quantity,
            running_total=self._current_sale.get_total(),
        )

    def end_sale(self) -> Money:
        self._current_sale.become_complete()
        return self._current_sale.get_total()

    def make_cash_payment(self, amount_tendered: Money) -> Money:
        payment = CashPayment(amount_tendered)
        self._current_sale.make_payment(payment)
        self._store.log_completed_sale(self._current_sale)
        return self._current_sale.get_balance()

    def make_mobile_money_payment(
        self, provider: str, phone_number: str, amount_tendered: Money
    ) -> Money:
        """Realizes UC1 extension 9b (paying by mobile money). Raises
        PaymentDeclinedError if the provider declines; propagates
        UnknownPaymentProviderError for an unrecognized provider name
        and GatewayUnavailableError if the gateway can't be reached."""
        adapter = self._payment_gateway_factory.get_mobile_money_adapter(provider)
        payment = MobileMoneyPayment(amount_tendered, adapter, phone_number, provider)
        return self._authorize_and_complete(payment)

    def make_card_payment(self, card_reference: str, amount_tendered: Money) -> Money:
        """Realizes UC1 extension 9c (paying by card). Raises
        PaymentDeclinedError if the card is declined; propagates
        GatewayUnavailableError if the gateway can't be reached."""
        adapter = self._payment_gateway_factory.get_card_adapter()
        payment = CardPayment(amount_tendered, adapter, card_reference)
        return self._authorize_and_complete(payment)

    def _authorize_and_complete(self, payment: ElectronicPayment) -> Money:
        result = payment.authorize()
        if not result.approved:
            raise PaymentDeclinedError(result.message)
        self._current_sale.make_payment(payment)
        self._store.log_completed_sale(self._current_sale)
        return self._current_sale.get_balance()

    @property
    def current_sale(self) -> Optional[Sale]:
        return self._current_sale

    @property
    def offline_queue(self) -> OfflineSyncQueue:
        """The OfflineSyncQueue shared by this register's mobile money
        PaymentServiceProxy instances. Replay it (e.g. via
        Store.sync_offline_payments()) once connectivity is believed
        to be restored."""
        return self._payment_gateway_factory.offline_queue

    # --- Handle Returns (cash-refund only this slice) ---------------

    def start_return(self) -> None:
        self._current_return = SaleReturn()

    def enter_return_item(self, item_id: str, quantity: int) -> ReturnLineItemResult:
        description = self._catalog.get_product_description(item_id)
        self._current_return.make_line_item(description, quantity)
        return ReturnLineItemResult(
            description=description,
            quantity=quantity,
            running_refund_total=self._current_return.get_total(),
        )

    def end_return(self) -> Money:
        self._current_return.become_complete()
        return self._current_return.get_total()

    def make_cash_refund(self) -> Money:
        refund_amount = self._current_return.get_total()
        self._current_return.make_refund(CashRefund(refund_amount))
        self._store.log_completed_return(self._current_return)
        return refund_amount

    @property
    def current_return(self) -> Optional[SaleReturn]:
        return self._current_return
