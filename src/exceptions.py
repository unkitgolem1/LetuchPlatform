"""Application-specific exceptions for clean error handling."""


class AppError(Exception):
    """Base exception for all application errors."""


class NotFoundError(AppError):
    """Resource not found."""


class CartEmptyError(AppError):
    """Cart has no items."""


class CartNotFoundError(AppError):
    """No active cart found for session."""


class InvalidCredentialsError(AppError):
    """Email or password is incorrect."""


class EmailAlreadyRegisteredError(AppError):
    """Email already in use during registration."""
