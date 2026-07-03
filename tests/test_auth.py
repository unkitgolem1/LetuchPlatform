"""Unit tests for auth.py — password hashing & verification."""

import pytest
from auth import hash_password, verify_password


class TestHashPassword:
    def test_hash_returns_string(self):
        hashed = hash_password("secret123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_different_each_time(self):
        h1 = hash_password("secret123")
        h2 = hash_password("secret123")
        assert h1 != h2

    def test_hash_contains_bcrypt_prefix(self):
        hashed = hash_password("secret123")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_hash_empty_password(self):
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_unicode_password(self):
        hashed = hash_password("contraseña_ñ_ü_😀")
        assert isinstance(hashed, str)


class TestVerifyPassword:
    def test_verify_correct_password(self):
        password = "my_secret_pass"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_empty_password(self):
        hashed = hash_password("some_password")
        assert verify_password("", hashed) is False

    def test_verify_empty_hash_raises(self):
        with pytest.raises(ValueError):
            verify_password("password", "")

    def test_verify_wrong_format_raises(self):
        with pytest.raises(ValueError):
            verify_password("password", "not_a_valid_hash")

    def test_verify_special_characters(self):
        password = "p@$$w0rd!ñ_ü_😀"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
