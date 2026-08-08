"""OID: Object Identifier (Larman Ch.38.8, "Pattern: Object Identifier").

Larman: "It is desirable to have a consistent way to relate objects to
records... The Object Identifier pattern proposes assigning an object
identifier (OID) to each record and object... within object land, an
OID is represented by an OID interface or class that encapsulates the
actual value and its representation."

For ProductDescription, ``item_id`` (e.g. "SKU-001") is already a
natural, stable, unique business key, so OID wraps it directly rather
than introducing a synthetic surrogate key — see ARCHITECTURE.md for
the reasoning. A future persistent entity with no natural key (e.g. a
completed Sale) may need OID to wrap a generated value instead; OID's
job is only to give the persistence subsystem one consistent identifier
type to key on, regardless of how the value was produced.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OID:
    """An opaque, stable identifier for a persistent object."""

    value: str
