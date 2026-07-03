"""Unit tests for forms.py — RegisterForm & LoginForm validation."""

import pytest
from pydantic import ValidationError
from forms import RegisterForm, LoginForm


class TestRegisterForm:
    def test_valid_registration(self):
        form = RegisterForm(
            nombre="Test User",
            email="test@example.com",
            password="secret123",
            confirm_password="secret123",
        )
        assert form.nombre == "Test User"
        assert form.email == "test@example.com"
        assert form.password == "secret123"

    def test_email_lowercased(self):
        form = RegisterForm(
            nombre="Test",
            email="Test@Example.COM",
            password="secret123",
            confirm_password="secret123",
        )
        assert form.email == "test@example.com"

    def test_nombre_stripped(self):
        form = RegisterForm(
            nombre="  Spaced Name  ",
            email="test@example.com",
            password="secret123",
            confirm_password="secret123",
        )
        assert form.nombre == "Spaced Name"

    def test_empty_nombre_raises(self):
        with pytest.raises(ValidationError) as exc:
            RegisterForm(
                nombre="",
                email="test@example.com",
                password="secret123",
                confirm_password="secret123",
            )
        assert "nombre" in str(exc.value).lower()

    def test_whitespace_nombre_raises(self):
        with pytest.raises(ValidationError):
            RegisterForm(
                nombre="   ",
                email="test@example.com",
                password="secret123",
                confirm_password="secret123",
            )

    def test_invalid_email_no_at_raises(self):
        with pytest.raises(ValidationError):
            RegisterForm(
                nombre="Test",
                email="notanemail",
                password="secret123",
                confirm_password="secret123",
            )

    def test_invalid_email_no_dot_raises(self):
        with pytest.raises(ValidationError):
            RegisterForm(
                nombre="Test",
                email="test@example",
                password="secret123",
                confirm_password="secret123",
            )

    def test_empty_email_raises(self):
        with pytest.raises(ValidationError):
            RegisterForm(
                nombre="Test",
                email="",
                password="secret123",
                confirm_password="secret123",
            )

    def test_short_password_raises(self):
        with pytest.raises(ValidationError) as exc:
            RegisterForm(
                nombre="Test",
                email="test@example.com",
                password="12345",
                confirm_password="12345",
            )
        assert "6" in str(exc.value) or "caracteres" in str(exc.value)

    def test_passwords_dont_match_raises(self):
        with pytest.raises(ValidationError) as exc:
            RegisterForm(
                nombre="Test",
                email="test@example.com",
                password="secret123",
                confirm_password="different",
            )
        assert "coinciden" in str(exc.value).lower()

    def test_empty_confirm_password_raises(self):
        with pytest.raises(ValidationError):
            RegisterForm(
                nombre="Test",
                email="test@example.com",
                password="secret123",
                confirm_password="",
            )


class TestLoginForm:
    def test_valid_login(self):
        form = LoginForm(email="test@example.com", password="secret123")
        assert form.email == "test@example.com"
        assert form.password == "secret123"

    def test_email_lowercased(self):
        form = LoginForm(email="Test@Example.COM", password="pass")
        assert form.email == "test@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            LoginForm(email="notanemail", password="secret123")

    def test_empty_email_raises(self):
        with pytest.raises(ValidationError):
            LoginForm(email="", password="secret123")

    def test_empty_password_raises(self):
        with pytest.raises(ValidationError):
            LoginForm(email="test@example.com", password="")

    def test_valid_with_minimal_email(self):
        form = LoginForm(email="a@b.co", password="secret123")
        assert form.email == "a@b.co"
