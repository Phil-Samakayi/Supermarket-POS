"""Exceptions raised by the users package."""
from __future__ import annotations


class UserNotFoundError(Exception):
    """Raised when a username does not match any known User."""

    def __init__(self, username: str) -> None:
        super().__init__(f"No user found for username: {username}")
        self.username = username


class UserAlreadyExistsError(Exception):
    """Raised by UserManager.create_user() for a username already in use."""

    def __init__(self, username: str) -> None:
        super().__init__(f"A user already exists with username: {username}")
        self.username = username


class NotAuthorizedError(Exception):
    """Raised when a non-Administrator attempts a Manage Users
    operation. Realizes the "System administrator: manage users,
    manage security" actor responsibility named in the book's own
    NextGen POS actor list."""

    def __init__(self, username: str, action: str) -> None:
        super().__init__(f"User {username!r} is not authorized to {action}.")
        self.username = username
        self.action = action


class AuthenticationError(Exception):
    """Raised by AuthenticationService.authenticate() on failure.
    Deliberately carries the same message whether the username doesn't
    exist or the password was wrong — never reveal which, or an
    attacker can enumerate valid usernames by the error alone."""

    def __init__(self) -> None:
        super().__init__("Invalid username or password.")


class AdministratorAlreadyExistsError(Exception):
    """Raised by UserManager.bootstrap_administrator() once any user
    already exists — it's a one-time first-run operation, not a
    standing backdoor around normal authorization."""

    def __init__(self) -> None:
        super().__init__(
            "Cannot bootstrap an administrator: at least one user already exists. "
            "Use create_user() with an authorized acting_user instead."
        )
