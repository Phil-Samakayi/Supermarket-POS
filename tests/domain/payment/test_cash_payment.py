from supermarket_pos.domain.common.money import Money
from supermarket_pos.domain.payment.cash_payment import CashPayment


def test_cash_payment_stores_amount_tendered():
    payment = CashPayment(Money("50.00"))

    assert payment.amount_tendered == Money("50.00")


def test_cash_payment_records_a_timestamp():
    payment = CashPayment(Money("50.00"))

    assert payment.date_time is not None
