from repos.interfaces import DatabaseInterface
from models import User, UserWithPsw
from typing import Optional


class UserRepo:
    def __init__(self, db: DatabaseInterface):
        self.db = db

    async def get_by_session(self, session_id: str) -> Optional[User]:
        row = await self.db.fetchrow(
            """
            SELECT id_usuario, id_sesion, nombre, email, avatar, created_at
            FROM usuarios
            WHERE id_sesion = $1::uuid
            """,
            session_id,
        )
        if not row:
            return None
        return User(**dict(row))

    async def get_with_psw_by_session(self, session_id: str) -> Optional[UserWithPsw]:
        row = await self.db.fetchrow(
            """
            SELECT id_usuario, id_sesion, nombre, email, avatar, password_hash, created_at
            FROM usuarios
            WHERE id_sesion = $1::uuid
            """,
            session_id,
        )
        if not row:
            return None
        return UserWithPsw(**dict(row))

    async def create(
        self, session_id: str, nombre: str, email: str, password_hash: str
    ) -> User:
        row = await self.db.fetchrow(
            """
            INSERT INTO usuarios (id_sesion, nombre, email, password_hash)
            VALUES ($1::uuid, $2, $3, $4)
            RETURNING id_usuario, id_sesion, nombre, email, avatar, created_at
            """,
            session_id, nombre, email, password_hash,
        )
        return User(**dict(row))

    async def update(self, user: UserWithPsw) -> None:
        await self.db.execute(
            """
            UPDATE usuarios
            SET nombre = $1, email = $2, password_hash = $3, avatar = $4, updated_at = NOW()
            WHERE id_usuario = $5::uuid
            """,
            user.nombre, user.email, user.password_hash, user.avatar, user.id_usuario,
        )

    async def unlink_session(self, session_id: str) -> None:
        """Desvincula la sesión del usuario sin borrar la cuenta."""
        await self.db.execute(
            "UPDATE usuarios SET id_sesion = NULL, updated_at = NOW() WHERE id_sesion = $1::uuid",
            session_id,
        )

    async def get_by_email(self, email: str) -> Optional[UserWithPsw]:
        row = await self.db.fetchrow(
            """
            SELECT id_usuario, id_sesion, nombre, email, avatar, password_hash, created_at
            FROM usuarios
            WHERE email = $1
            """,
            email,
        )
        if not row:
            return None
        return UserWithPsw(**dict(row))

    async def link_to_session(self, user_id: str, session_id: str) -> None:
        """Vincula un usuario existente a una nueva sesión (login desde otro dispositivo)."""
        await self.db.execute(
            "UPDATE usuarios SET id_sesion = $1::uuid, updated_at = NOW() WHERE id_usuario = $2::uuid",
            session_id, user_id,
        )
