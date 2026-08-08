"""AuthenticationService: realizes the "Authenticate User" subfunction
use case.

Larman is explicit that this is a subfunction-level use case, not a
standalone goal (Ch.6.16, "Reasonable Violations of the Tests"):
"Authenticate User may not pass the Boss test, but be complex enough
to warrant careful analysis, such as for a 'single sign-on' feature."
The essential-style scenario he gives (Ch.6.11) is exactly this
class's one method:

    1. Administrator identifies self.
    2. System authenticates identity.

— written at the level of intent, not mechanism (no dialog boxes or
password fields in the use case text itself; that concreteness only
belongs in the implementation, which is what this class is).

Deliberately its own class, not folded into UserManager — different
callers. UserManager's mutating operations are Administrator-only,
CRUD, occasional. Every operational use case (Process Sale, Handle
Returns, Manage Inventory, Manage Users itself) needs authentication,
frequently, regardless of actor. Larman's own "include relationship"
guidance for shared subfunctions (linking one subfunction use case to
several base use cases, rather than duplicating its text) maps
directly onto giving it its own collaborator rather than copying
authentication logic into Register, InventoryManager, and UserManager
separately.
"""
from __future__ import annotations

from supermarket_pos.domain.users.exceptions import AuthenticationError, UserNotFoundError
from supermarket_pos.domain.users.password_hasher import PasswordHasher
from supermarket_pos.domain.users.user import User
from supermarket_pos.domain.users.user_manager import UserManager


class AuthenticationService:
    """Realizes Authenticate User. Not yet wired as a precondition of
    Process Sale/Handle Returns/Manage Inventory — see
    ARCHITECTURE.md's Unresolved Issues for why that integration is a
    deliberate, separate follow-up, not built in this slice."""

    def __init__(self, user_manager: UserManager) -> None:
        self._user_manager = user_manager

    def authenticate(self, username: str, plain_password: str) -> User:
        """Raises AuthenticationError on any failure — unknown
        username and wrong password produce the identical error and
        message, deliberately, so neither reveals to a caller whether
        the username exists at all."""
        try:
            user = self._user_manager.get_user(username)
        except UserNotFoundError:
            raise AuthenticationError() from None

        if not PasswordHasher.verify_password(plain_password, user.password_hash):
            raise AuthenticationError()

        return user
