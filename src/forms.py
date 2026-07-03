from pydantic import BaseModel, field_validator


class RegisterForm(BaseModel):
    nombre: str
    email: str
    password: str
    confirm_password: str

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre es obligatorio")
        return v.strip()

    @field_validator("email")
    @classmethod
    def email_valido(cls, v):
        if not v or "@" not in v or "." not in v:
            raise ValueError("Email inválido")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def password_segura(cls, v):
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_coinciden(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Las contraseñas no coinciden")
        return v


class LoginForm(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_valido(cls, v):
        if not v or "@" not in v:
            raise ValueError("Email inválido")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def password_no_vacio(cls, v):
        if not v:
            raise ValueError("La contraseña es obligatoria")
        return v
