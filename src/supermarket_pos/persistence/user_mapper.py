"""UserMapper: the Database Mapper (Larman Ch.38.10) for User.

Fits PersistenceFacade's symmetric contract cleanly, same reasoning
as StockLevelMapper: User has a natural key (username) and no
relationships or polymorphism to work around, unlike the sale/return
snapshot mappers.
"""
from __future__ import annotations

from typing import List

from supermarket_pos.domain.users.user import User
from supermarket_pos.domain.users.user_role import UserRole
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection


class UserMapper:
    """Materializes/dematerializes User <-> the users table. All SQL
    for this entity lives here (Ch.38.15)."""

    def __init__(self, connection: SQLiteConnection) -> None:
        self._connection = connection.connection
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def get(self, oid: OID) -> User:
        row = self._connection.execute(
            "SELECT username, password_hash, role FROM users WHERE username = ?",
            (oid.value,),
        ).fetchone()
        if row is None:
            raise ValueError(f"No user found for username {oid.value!r}")
        return self._to_domain(row)

    def get_all(self) -> List[User]:
        rows = self._connection.execute(
            "SELECT username, password_hash, role FROM users ORDER BY username"
        ).fetchall()
        return [self._to_domain(row) for row in rows]

    def save(self, user: User) -> OID:
        self._connection.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (:username, :password_hash, :role)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = excluded.password_hash,
                role = excluded.role
            """,
            {
                "username": user.username,
                "password_hash": user.password_hash,
                "role": user.role.value,
            },
        )
        self._connection.commit()
        return OID(user.username)

    def delete(self, oid: OID) -> None:
        self._connection.execute("DELETE FROM users WHERE username = ?", (oid.value,))
        self._connection.commit()

    @staticmethod
    def _to_domain(row) -> User:
        return User(
            username=row["username"],
            password_hash=row["password_hash"],
            role=UserRole(row["role"]),
        )
