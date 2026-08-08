"""User: an account, identified by username, with a role.

Frozen, like ProductDescription/StockLevel — the established idiom
throughout this codebase for persistent-but-simple entities: "edit"
operations (UserManager.reset_password, edit_user_role) construct a
new User with the changed field(s) rather than mutating one in place.

Never holds a plaintext password — only the self-describing hash
string PasswordHasher.hash_password() produces (algorithm, iteration
count, salt, and digest all embedded in one string; see that module).
"""
from __future__ import annotations

from dataclasses import dataclass

from supermarket_pos.domain.users.user_role import UserRole


@dataclass(frozen=True)
class User:
    """username doubles as both the natural key and this type's OID
    value, exactly as item_id does for ProductDescription/StockLevel."""

    username: str
    password_hash: str
    role: UserRole
