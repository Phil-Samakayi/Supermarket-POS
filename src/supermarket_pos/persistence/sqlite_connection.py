"""SQLiteConnection: holds the one open sqlite3 connection shared by
every Database Mapper.

Not itself a Larman-named pattern — it exists purely so mappers don't
each manage their own connection lifecycle, and so tests can use
``:memory:`` correctly (a fresh ``sqlite3.connect(':memory:')`` call
creates a *new empty* database each time; the connection must be
created once and reused for the in-memory database to actually
persist across calls within a test).
"""
from __future__ import annotations

import sqlite3


class SQLiteConnection:
    """Thin holder for a single sqlite3 connection. ``db_path``
    defaults to an in-memory database — pass a file path for a real,
    durable store (e.g. "supermarket_pos.db")."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def close(self) -> None:
        self._connection.close()
