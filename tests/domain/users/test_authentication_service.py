import pytest

from supermarket_pos.domain.users.authentication_service import AuthenticationService
from supermarket_pos.domain.users.exceptions import AuthenticationError
from supermarket_pos.domain.users.user_manager import UserManager
from supermarket_pos.domain.users.user_role import UserRole

FAST_ITERATIONS = 1000  # test-speed only, see password_hasher.py


@pytest.fixture
def user_manager() -> UserManager:
    return UserManager(password_hash_iterations=FAST_ITERATIONS)


@pytest.fixture
def auth_service(user_manager) -> AuthenticationService:
    return AuthenticationService(user_manager)


def test_authenticate_with_correct_credentials_returns_the_user(user_manager, auth_service):
    user_manager.bootstrap_administrator("admin", "adminpass123")

    user = auth_service.authenticate("admin", "adminpass123")

    assert user.username == "admin"


def test_authenticate_with_wrong_password_raises(user_manager, auth_service):
    user_manager.bootstrap_administrator("admin", "adminpass123")

    with pytest.raises(AuthenticationError):
        auth_service.authenticate("admin", "wrongpassword")


def test_authenticate_with_unknown_username_raises(auth_service):
    with pytest.raises(AuthenticationError):
        auth_service.authenticate("ghost", "anypassword")


def test_unknown_username_and_wrong_password_give_the_identical_error_message(
    user_manager, auth_service
):
    """Deliberate: neither error should reveal to a caller whether the
    username exists at all."""
    user_manager.bootstrap_administrator("admin", "adminpass123")

    with pytest.raises(AuthenticationError) as unknown_user_exc:
        auth_service.authenticate("ghost", "anypassword")
    with pytest.raises(AuthenticationError) as wrong_password_exc:
        auth_service.authenticate("admin", "wrongpassword")

    assert str(unknown_user_exc.value) == str(wrong_password_exc.value)


def test_authenticate_works_for_any_role_not_just_administrator(user_manager, auth_service):
    admin = user_manager.bootstrap_administrator("admin", "adminpass123")
    user_manager.create_user(admin, "jchanda", "cashierpass1", UserRole.CASHIER)

    user = auth_service.authenticate("jchanda", "cashierpass1")

    assert user.role == UserRole.CASHIER
