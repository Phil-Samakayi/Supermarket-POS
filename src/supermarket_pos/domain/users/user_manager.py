"""UserManager: GRASP Controller for the Manage Users CRUD system
operations.

A separate Controller from both Register and InventoryManager — a
third distinct actor. Larman's book names all three explicitly in its
NextGen POS actor list: Cashier (Register), Manager/Owner
(InventoryManager, SalesReportGenerator's caller), and "System
administrator: manage users, manage security, manage system tables"
(this class). The CRUD-collapsing naming convention itself is Larman's
own (Ch.6.15): "the goals 'edit user,' 'delete user,' and so forth are
all satisfied by the Manage Users use case."

Every mutating operation here requires an ``acting_user`` with the
ADMINISTRATOR role — this is the "manage security" half of the
System administrator's responsibility, not just CRUD plumbing.
"""
from __future__ import annotations

from typing import List, Optional

from supermarket_pos.domain.users.exceptions import (
    AdministratorAlreadyExistsError,
    NotAuthorizedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from supermarket_pos.domain.users.password_hasher import PasswordHasher
from supermarket_pos.domain.users.user import User
from supermarket_pos.domain.users.user_role import UserRole
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.persistence_facade import PersistenceFacade


class UserManager:
    """Controller for create_user / edit_user_role / reset_password /
    delete_user / bootstrap_administrator — the Manage Users system
    operations."""

    def __init__(
        self,
        persistence_facade: Optional[PersistenceFacade] = None,
        password_hash_iterations: Optional[int] = None,
    ) -> None:
        self._users: dict[str, User] = {}
        self._persistence_facade = persistence_facade
        self._password_hash_iterations = password_hash_iterations
        """Overrides PasswordHasher's default iteration count for
        every hash this manager produces — exists purely so tests can
        run fast (a real iteration count costs >100ms per call); left
        as None (PasswordHasher's own production default) in normal
        use."""

        if self._persistence_facade is not None:
            for user in self._persistence_facade.get_all(User):
                self._users[user.username] = user

    def _hash(self, plain_password: str) -> str:
        if self._password_hash_iterations is None:
            return PasswordHasher.hash_password(plain_password)
        return PasswordHasher.hash_password(plain_password, iterations=self._password_hash_iterations)

    def bootstrap_administrator(self, username: str, plain_password: str) -> User:
        """Creates the very first user, unconditionally, as
        ADMINISTRATOR — the only way an Administrator account can ever
        come to exist, since create_user() itself requires an acting
        Administrator. Only works while zero users exist; raises
        AdministratorAlreadyExistsError otherwise, so it can't be
        called again as a backdoor once real accounts exist."""
        if self._users:
            raise AdministratorAlreadyExistsError()
        user = User(
            username=username,
            password_hash=self._hash(plain_password),
            role=UserRole.ADMINISTRATOR,
        )
        self._save(user)
        return user

    def create_user(
        self, acting_user: User, username: str, plain_password: str, role: UserRole
    ) -> User:
        self._require_administrator(acting_user, "create users")
        if username in self._users:
            raise UserAlreadyExistsError(username)
        user = User(username=username, password_hash=self._hash(plain_password), role=role)
        self._save(user)
        return user

    def edit_user_role(self, acting_user: User, username: str, new_role: UserRole) -> User:
        self._require_administrator(acting_user, "edit user roles")
        existing = self._get_or_raise(username)
        updated = User(username=existing.username, password_hash=existing.password_hash, role=new_role)
        self._save(updated)
        return updated

    def reset_password(self, acting_user: User, username: str, new_plain_password: str) -> User:
        self._require_administrator(acting_user, "reset passwords")
        existing = self._get_or_raise(username)
        updated = User(
            username=existing.username,
            password_hash=self._hash(new_plain_password),
            role=existing.role,
        )
        self._save(updated)
        return updated

    def delete_user(self, acting_user: User, username: str) -> None:
        self._require_administrator(acting_user, "delete users")
        self._get_or_raise(username)
        del self._users[username]
        if self._persistence_facade is not None:
            self._persistence_facade.delete(OID(username), User)

    def get_user(self, username: str) -> User:
        """Not Administrator-gated — every authenticated actor needs
        to be able to look up a user (starting with
        AuthenticationService looking up itself), not just admins."""
        return self._get_or_raise(username)

    def list_users(self) -> List[User]:
        return sorted(self._users.values(), key=lambda user: user.username)

    def _require_administrator(self, acting_user: User, action: str) -> None:
        if acting_user.role != UserRole.ADMINISTRATOR:
            raise NotAuthorizedError(acting_user.username, action)

    def _get_or_raise(self, username: str) -> User:
        try:
            return self._users[username]
        except KeyError:
            raise UserNotFoundError(username) from None

    def _save(self, user: User) -> None:
        self._users[user.username] = user
        if self._persistence_facade is not None:
            self._persistence_facade.save(user)
