"""CardPayment: an ElectronicPayment made via a debit/credit card."""
from __future__ import annotations

from supermarket_pos.domain.payment.electronic_payment import ElectronicPayment


class CardPayment(ElectronicPayment):
    """A payment tendered by card.

    ``payer_reference`` (inherited) is the card token/reference read
    from the card reader — never a raw PAN. Iteration-1's Special
    Requirements deliberately keep raw card data out of this domain
    layer entirely; how that token is produced is a UI/device concern.
    """
