"""Authentication use cases: register, login, logout."""

from typing import Optional
from repos.interfaces import DatabaseInterface
from repos.user_repo import UserRepo
from auth import hash_password, verify_password
from exceptions import InvalidCredentialsError, EmailAlreadyRegisteredError
from models import User


class AuthService:
    def __init__(self, user_repo: UserRepo, db: DatabaseInterface):
        self.user_repo = user_repo
        self.db = db

    async def register(
        self, session_id: str, nombre: str, email: str, password: str
    ) -> User:
        """Register a new user. Raises EmailAlreadyRegisteredError if email exists."""
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise EmailAlreadyRegisteredError("Este email ya está registrado")

        password_hash = hash_password(password)
        user = await self.user_repo.create(
            session_id, nombre, email, password_hash
        )
        return user

    async def login(
        self, email: str, password: str, current_session_id: str
    ) -> tuple[User, str]:
        """Authenticate and return (user, new_session_id). Raises InvalidCredentialsError."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Email o contraseña incorrectos")

        row = await self.db.fetchrow(
            "SELECT fn_obtener_o_crear_sesion(NULL::uuid) AS id",
        )
        new_session_id = str(row["id"])
        await self.user_repo.link_to_session(user.id_usuario, new_session_id)
        return user, new_session_id

    async def logout(self, session_id: str) -> None:
        """Unlink session from user and invalidate it in the database."""
        await self.user_repo.unlink_session(session_id)
        await self.db.execute(
            "SELECT fn_invalidar_sesion($1::uuid)",
            session_id,
        )
