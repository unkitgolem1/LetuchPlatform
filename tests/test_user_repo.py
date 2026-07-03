"""Integration tests for UserRepo — uses mocked Database."""

import pytest
from unittest.mock import AsyncMock
from auth import hash_password
from repos.user_repo import UserRepo
from models import User, UserWithPsw
from tests.conftest import fake_record


class TestGetBySession:
    async def test_returns_user_when_found(self, user_repo, mock_fetchrow):
        mock_fetchrow.return_value = fake_record({
            "id_usuario": "u1", "id_sesion": "s1",
            "nombre": "Alice", "email": "alice@test.com",
            "avatar": "", "created_at": None,
        })
        user = await user_repo.get_by_session("s1")
        assert isinstance(user, User)
        assert user.nombre == "Alice"
        assert user.email == "alice@test.com"
        mock_fetchrow.assert_awaited_once()

    async def test_returns_none_when_not_found(self, user_repo, mock_fetchrow):
        mock_fetchrow.return_value = None
        user = await user_repo.get_by_session("nonexistent")
        assert user is None


class TestGetByEmail:
    async def test_returns_user_when_found(self, user_repo, mock_fetchrow):
        mock_fetchrow.return_value = fake_record({
            "id_usuario": "u1", "id_sesion": "s1",
            "nombre": "Bob", "email": "bob@test.com",
            "avatar": "", "password_hash": hash_password("pass"),
            "created_at": None,
        })
        user = await user_repo.get_by_email("bob@test.com")
        assert isinstance(user, UserWithPsw)
        assert user.nombre == "Bob"
        assert user.password_hash

    async def test_returns_none_when_not_found(self, user_repo, mock_fetchrow):
        mock_fetchrow.return_value = None
        user = await user_repo.get_by_email("noone@test.com")
        assert user is None


class TestCreate:
    async def test_creates_user(self, user_repo, mock_fetchrow):
        mock_fetchrow.return_value = fake_record({
            "id_usuario": "new-uuid",
            "id_sesion": "s1",
            "nombre": "New User",
            "email": "new@test.com",
            "avatar": "",
            "created_at": None,
        })
        user = await user_repo.create("s1", "New User", "new@test.com", hash_password("pass"))
        assert isinstance(user, User)
        assert user.nombre == "New User"
        assert user.email == "new@test.com"
        mock_fetchrow.assert_awaited_once()

    async def test_create_sql_contains_insert(self, user_repo, mock_fetchrow):
        mock_fetchrow.return_value = fake_record({
            "id_usuario": "uuid", "id_sesion": "s", "nombre": "N",
            "email": "e@t.com", "avatar": "", "created_at": None,
        })
        await user_repo.create("s", "N", "e@t.com", "hash")
        call_query = mock_fetchrow.await_args[0][0]
        assert "INSERT" in call_query.upper()
        assert "usuarios" in call_query.lower()


class TestLinkToSession:
    async def test_links_session(self, user_repo, mock_execute):
        mock_execute.return_value = "OK"
        await user_repo.link_to_session("user-id", "session-id")
        mock_execute.assert_awaited_once()
        call_query = mock_execute.await_args[0][0]
        assert "UPDATE" in call_query.upper()
        assert "id_sesion" in call_query.lower()


class TestUnlinkSession:
    async def test_sets_session_to_null(self, user_repo, mock_execute):
        mock_execute.return_value = "OK"
        await user_repo.unlink_session("session-id")
        mock_execute.assert_awaited_once()
        call_query = mock_execute.await_args[0][0]
        assert "UPDATE" in call_query.upper()
        assert "NULL" in call_query.upper() or "null" in call_query.lower()
        assert "id_sesion" in call_query.lower()

    async def test_unlink_does_not_delete(self, user_repo, mock_execute):
        """Verifica que NO sea un DELETE (regresión del bug)."""
        mock_execute.return_value = "OK"
        await user_repo.unlink_session("session-id")
        call_query = mock_execute.await_args[0][0]
        assert "DELETE" not in call_query.upper()
