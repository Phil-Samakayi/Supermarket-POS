import pytest

from supermarket_pos.domain.users.user import User
from supermarket_pos.domain.users.user_role import UserRole
from supermarket_pos.persistence.oid import OID
from supermarket_pos.persistence.sqlite_connection import SQLiteConnection
from supermarket_pos.persistence.user_mapper import UserMapper


@pytest.fixture
def mapper() -> UserMapper:
    return UserMapper(SQLiteConnection(":memory:"))


def make_user(username="jchanda", role=UserRole.CASHIER):
    return User(username=username, password_hash="pbkdf2_sha256$1000$abcd$deadbeef", role=role)


def test_save_then_get_round_trips(mapper):
    oid = mapper.save(make_user())

    fetched = mapper.get(oid)

    assert fetched == make_user()


def test_role_round_trips_correctly(mapper):
    mapper.save(make_user(role=UserRole.ADMINISTRATOR))

    fetched = mapper.get(OID("jchanda"))

    assert fetched.role == UserRole.ADMINISTRATOR


def test_get_unknown_username_raises(mapper):
    with pytest.raises(ValueError, match="No user found"):
        mapper.get(OID("ghost"))


def test_save_is_an_upsert(mapper):
    mapper.save(make_user(role=UserRole.CASHIER))
    mapper.save(make_user(role=UserRole.MANAGER))

    all_users = mapper.get_all()

    assert len(all_users) == 1
    assert all_users[0].role == UserRole.MANAGER


def test_get_all_ordered_by_username(mapper):
    mapper.save(make_user(username="zeb"))
    mapper.save(make_user(username="amos"))

    usernames = [user.username for user in mapper.get_all()]

    assert usernames == ["amos", "zeb"]


def test_delete_removes_the_user(mapper):
    oid = mapper.save(make_user())

    mapper.delete(oid)

    with pytest.raises(ValueError, match="No user found"):
        mapper.get(oid)
