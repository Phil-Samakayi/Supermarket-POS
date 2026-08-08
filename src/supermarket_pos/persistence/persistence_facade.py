"""PersistenceFacade: the single entry point the rest of the system
uses to reach persistent storage (Larman Ch.38.9, "Accessing a
Persistence Service with a Facade").

Larman: "Step one in the design of this subsystem is to define a
facade for its services... The PersistenceFacade — as true of all
facades — does not do the work itself, but delegates requests to
subsystem objects [the Database Mappers]." His own sketch:

    class PersistenceFacade {
        public Object get(OID oid, Class persistenceClass) {
            IMapper mapper = (IMapper) mappers.get(persistenceClass);
            return mapper.get(oid);
        }
    }

This is that, translated to Python: one Mapper instance per persistent
type, looked up by type and delegated to.
"""
from __future__ import annotations

from typing import Any, Dict, List, Type

from supermarket_pos.persistence.mapper import IMapper
from supermarket_pos.persistence.oid import OID


class PersistenceFacade:
    """Unified entry point over a set of Database Mappers, one per
    persistent type."""

    def __init__(self, mappers: Dict[type, IMapper]) -> None:
        self._mappers = mappers

    def get(self, oid: OID, persistence_class: Type) -> Any:
        return self._mapper_for(persistence_class).get(oid)

    def get_all(self, persistence_class: Type) -> List[Any]:
        return self._mapper_for(persistence_class).get_all()

    def save(self, obj: Any) -> OID:
        return self._mapper_for(type(obj)).save(obj)

    def delete(self, oid: OID, persistence_class: Type) -> None:
        self._mapper_for(persistence_class).delete(oid)

    def _mapper_for(self, persistence_class: Type) -> IMapper:
        try:
            return self._mappers[persistence_class]
        except KeyError:
            raise ValueError(
                f"No mapper registered for {persistence_class!r}"
            ) from None
