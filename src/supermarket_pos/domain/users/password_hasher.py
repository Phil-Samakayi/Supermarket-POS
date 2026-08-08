"""PasswordHasher: salted, iterated password hashing.

Uses PBKDF2-HMAC-SHA256 from the Python standard library (`hashlib`) —
not bcrypt or argon2, which would be the better modern choice for a
production system, but neither is in the standard library and this
project has kept `dependencies = []` throughout (SQLite over an ORM,
plain functions over a DI framework, etc. — see ARCHITECTURE.md for
the recurring pattern). PBKDF2 with a high iteration count and a
per-user random salt is an adequate, honest baseline for a student
project's login feature; it is explicitly not a claim that this is
production-grade. See ARCHITECTURE.md's Unresolved Issues for this
slice.

The stored hash is one self-describing string —
``pbkdf2_sha256$<iterations>$<salt>$<digest>`` — the same approach
Django's password hashers use. This means the iteration count actually
used is always read back from the hash itself, never assumed to match
whatever _DEFAULT_ITERATIONS happens to be at verification time. Two
things fall out of that for free: raising _DEFAULT_ITERATIONS later
doesn't break existing stored hashes, and tests can safely pass a much
lower `iterations` value for speed (this project's test suite would
otherwise cost ~350ms per hashed password at a real production
iteration count) without any risk of a hash/verify mismatch.

Verification uses hmac.compare_digest (constant-time comparison) to
avoid leaking timing information about how much of the hash matched.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_DEFAULT_ITERATIONS = 210_000
"""OWASP's current minimum recommendation for PBKDF2-HMAC-SHA256."""


class PasswordHasher:
    @staticmethod
    def hash_password(plain_password: str, iterations: int = _DEFAULT_ITERATIONS) -> str:
        salt = secrets.token_hex(16)
        digest = PasswordHasher._derive(plain_password, salt, iterations)
        return f"{_ALGORITHM}${iterations}${salt}${digest}"

    @staticmethod
    def verify_password(plain_password: str, stored_hash: str) -> bool:
        try:
            algorithm, iterations_str, salt, digest = stored_hash.split("$")
        except ValueError:
            return False
        if algorithm != _ALGORITHM:
            return False
        candidate = PasswordHasher._derive(plain_password, salt, int(iterations_str))
        return hmac.compare_digest(candidate, digest)

    @staticmethod
    def _derive(plain_password: str, salt: str, iterations: int) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), bytes.fromhex(salt), iterations
        ).hex()

