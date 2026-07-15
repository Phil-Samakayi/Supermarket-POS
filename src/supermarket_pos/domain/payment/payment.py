"""Abstract Payment superclass."""
from __future__ import annotations

from abc import ABC
from datetime import datetime

from supermarket_pos.domain.common.money import Money


class Payment(ABC):
    """
    Abstract superclass for payment types (GRASP: Polymorphism —
    each subclass will eventually authorize itself differently).

    Iteration-1 implements CashPayment only, since it requires no
    external authorization. Iteration-2 adds MobileMoneyPayment and
    CardPayment, authorized through the Adapter/Factory/Proxy design
    captured in docs/Supermarket_POS_UseCase_UML.docx (Section 5).
    """

    def __init__(self, amount_tendered: Money) -> None:
        self._amount_tendered = amount_tendered
        self._date_time = datetime.now()

    @property
    def amount_tendered(self) -> Money:
        return self._amount_tendered

    @property
    def date_time(self) -> datetime:
        return self._date_time
