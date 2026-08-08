"""Wires up a CompletedSaleMapper backed by SQLite.

A separate function from build_sqlite_persistence_facade() (not
folded into it) — CompletedSaleMapper isn't registered in
PersistenceFacade's {class: mapper} dict at all (see
completed_sale_mapper.py for why: its save/get shapes are
intentionally asymmetric, which doesn't fit the Facade's generic
per-class contract). Two small, independent wiring functions is more
honest than forcing one generalized entry point to cover both.
"""
from __future__ import annotations

from supermarket_pos.persistence.completed_sale_mapper import CompletedSaleMapper
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


def build_sqlite_sale_history_mapper(db_path: str = "supermarket_pos.db") -> CompletedSaleMapper:
    """Same default db_path as build_sqlite_persistence_facade() — in
    normal use both are pointed at the same file (SQLite handles
    multiple connections to one file safely for this app's
    single-process, low-concurrency use). Pass ":memory:" for tests."""
    return CompletedSaleMapper(SQLiteConnection(db_path))
