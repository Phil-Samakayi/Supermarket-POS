"""Wires up a CompletedReturnMapper backed by SQLite. Mirrors
sqlite_sale_history_factory.py — same reasoning for being its own
small, independent function."""
from __future__ import annotations

from supermarket_pos.persistence.completed_return_mapper import CompletedReturnMapper
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


def build_sqlite_return_history_mapper(db_path: str = "supermarket_pos.db") -> CompletedReturnMapper:
    """Same default db_path as the other sqlite_*_factory helpers — in
    normal use all three are pointed at the same file."""
    return CompletedReturnMapper(SQLiteConnection(db_path))
