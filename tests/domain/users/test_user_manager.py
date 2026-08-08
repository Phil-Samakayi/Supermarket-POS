import pytest

from supermarket_pos.domain.users.exceptions import (
    AdministratorAlreadyExistsError,
    NotAuthorizedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from supermarket_pos.domain.users.user_manager import UserManager
from supermarket_pos.domain.users.user_role import UserRole

FAST_ITERATIONS = 1000  # test-speed only, see password_hasher.py


@pytest.fixture
def manager() -> UserManager:
    return UserManager(password_hash_iterations=FAST_ITERATIONS)


@pytest.fixture
def admin(manager):
    return manager.bootstrap_administrator("admin", "adminpass123")


def test_bootstrap_administrator_creates_the_first_user_as_administrator(manager):
    admin = manager.bootstrap_administrator("admin", "adminpass123")

    assert admin.role == UserRole.ADMINISTRATOR


def test_bootstrap_administrator_after_a_user_exists_raises(manager, admin):
    with pytest.raises(AdministratorAlreadyExistsError):
        manager.bootstrap_administrator("someone-else", "password123")


def test_create_user_by_administrator_succeeds(manager, admin):
    cashier = manager.create_user(admin, "jchanda", "cashierpass1", UserRole.CASHIER)

    assert cashier.username == "jchanda"
    assert cashier.role == UserRole.CASHIER


def test_create_user_by_a_non_administrator_raises(manager, admin):
    cashier = manager.create_user(admin, "jchanda", "cashierpass1", UserRole.CASHIER)

    with pytest.raises(NotAuthorizedError):
        manager.create_user(cashier, "another", "password123", UserRole.CASHIER)


def test_create_user_with_a_duplicate_username_raises(manager, admin):
    manager.create_user(admin, "jchanda", "cashierpass1", UserRole.CASHIER)

    with pytest.raises(UserAlreadyExistsError):
        manager.create_user(admin, "jchanda", "differentpass", UserRole.MANAGER)


def test_edit_user_role_by_administrator_succeeds(manager, admin):
    manager.create_user(admin, "jchanda", "cashierpass1", UserRole.CASHIER)

    updated = manager.edit_user_role(admin, "jchanda", UserRole.MANAGER)

    assert updated.role == UserRole.MANAGER
    assert manager.get_user("jchanda").role == UserRole.MANAGER


def test_edit_user_role_by_non_administrator_raises(manager, admin):
    cashier = manager.create_user(admin, "jchanda", "cashierpass1", UserRole.CASHIER)

    with pytest.raises(NotAuthorizedError):
        manager.edit_user_role(cashier, "jchanda", UserRole.MANAGER)


def test_edit_role_of_unknown_user_raises(manager, admin):
    with pytest.raises(UserNotFoundError):
        manager.edit_user_role(admin, "ghost", UserRole.MANAGER)


def test_reset_password_changes_the_stored_hash(manager, admin):
    manager.create_user(admin, "jchanda", "oldpassword1", UserRole.CASHIER)

    manager.reset_password(admin, "jchanda", "newpassword2")

    from supermarket_pos.domain.users.password_hasher import PasswordHasher

    updated = manager.get_user("jchanda")
    assert PasswordHasher.verify_password("newpassword2", updated.password_hash) is True
    assert PasswordHasher.verify_password("oldpassword1", updated.password_hash) is False


def test_reset_password_by_non_administrator_raises(manager, admin):
    cashier = manager.create_user(admin, "jchanda", "oldpassword1", UserRole.CASHIER)

    with pytest.raises(NotAuthorizedError):
        manager.reset_password(cashier, "jchanda", "newpassword2")


def test_delete_user_by_administrator_removes_them(manager, admin):
    manager.create_user(admin, "jchanda", "cashierpass1", UserRole.CASHIER)

    manager.delete_user(admin, "jchanda")

    with pytest.raises(UserNotFoundError):
        manager.get_user("jchanda")


def test_delete_user_by_non_administrator_raises(manager, admin):
    cashier = manager.create_user(admin, "jchanda", "cashierpass1", UserRole.CASHIER)

    with pytest.raises(NotAuthorizedError):
        manager.delete_user(cashier, "jchanda")


def test_delete_unknown_user_raises(manager, admin):
    with pytest.raises(UserNotFoundError):
        manager.delete_user(admin, "ghost")


def test_list_users_returns_everyone_sorted_by_username(manager, admin):
    manager.create_user(admin, "zeb", "password123", UserRole.CASHIER)
    manager.create_user(admin, "amos", "password123", UserRole.CASHIER)

    usernames = [user.username for user in manager.list_users()]

    assert usernames == ["admin", "amos", "zeb"]


def test_get_user_is_not_administrator_gated():
    """Any caller can look up a user by username — needed by
    AuthenticationService, which isn't itself acting as an
    administrator."""
    manager = UserManager(password_hash_iterations=FAST_ITERATIONS)
    admin = manager.bootstrap_administrator("admin", "adminpass123")

    assert manager.get_user("admin") is admin
