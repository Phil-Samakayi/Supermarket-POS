"""IMapper: the common interface every Database Mapper implements
(Larman Ch.38.10, "Mapping Objects: Database Mapper or Database Broker
Pattern").

Larman explicitly rejects the alternative of a persistent object class
(e.g. ProductDescription) saving itself — "direct mapping... has a
number of defects": it couples the domain class to persistent storage
knowledge (violating Low Coupling) and gives it "complex
responsibilities in a new and unrelated area to what the object was
previously responsible for" (violating High Cohesion). A separate
Mapper class per persistent type is the alternative he develops instead
("A different mapper class is defined for each persistent object
class").

A Protocol (not an ABC) to match this codebase's existing convention
for narrow, swappable collaborator interfaces (see e.g.
MTNMoMoGatewayClient in the payment gateway package).
"""
from __future__ import annotations

from typing import List, Protocol, TypeVar

from supermarket_pos.persistence.oid import OID

T = TypeVar("T")


class IMapper(Protocol[T]):
    """Materializes/dematerializes one persistent type between the
    domain layer and storage. All SQL for that type lives in the
    concrete mapper implementing this — see Ch.38.15, "Consolidating
    and Hiding SQL Statements in One Class"."""

    def get(self, oid: OID) -> T:
        ...

    def get_all(self) -> List[T]:
        ...

    def save(self, obj: T) -> OID:
        ...

    def delete(self, oid: OID) -> None:
        ...
