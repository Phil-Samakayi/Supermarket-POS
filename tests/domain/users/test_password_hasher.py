from supermarket_pos.domain.users.password_hasher import PasswordHasher

FAST_ITERATIONS = 1000  # test-speed only, see password_hasher.py's docstring


def test_verify_password_succeeds_for_the_correct_password():
    stored = PasswordHasher.hash_password("correct horse battery staple", iterations=FAST_ITERATIONS)

    assert PasswordHasher.verify_password("correct horse battery staple", stored) is True


def test_verify_password_fails_for_the_wrong_password():
    stored = PasswordHasher.hash_password("correct horse battery staple", iterations=FAST_ITERATIONS)

    assert PasswordHasher.verify_password("wrong password", stored) is False


def test_two_hashes_of_the_same_password_are_different():
    """Different random salts each time — this is what defeats
    rainbow-table attacks."""
    first = PasswordHasher.hash_password("hunter2", iterations=FAST_ITERATIONS)
    second = PasswordHasher.hash_password("hunter2", iterations=FAST_ITERATIONS)

    assert first != second
    assert PasswordHasher.verify_password("hunter2", first) is True
    assert PasswordHasher.verify_password("hunter2", second) is True


def test_stored_hash_embeds_the_iteration_count_used():
    stored = PasswordHasher.hash_password("hunter2", iterations=42)

    assert "$42$" in stored


def test_verify_password_rejects_a_malformed_stored_hash():
    assert PasswordHasher.verify_password("anything", "not-a-real-hash") is False


def test_verify_password_rejects_an_unrecognized_algorithm_prefix():
    stored = PasswordHasher.hash_password("hunter2", iterations=FAST_ITERATIONS)
    tampered = stored.replace("pbkdf2_sha256", "md5", 1)

    assert PasswordHasher.verify_password("hunter2", tampered) is False
