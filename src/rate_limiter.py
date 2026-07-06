import time
from collections import defaultdict
from fastapi import Request, HTTPException

_attempts: dict[str, list[float]] = defaultdict(list)
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300


async def rate_limit_login(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    _attempts[ip] = [t for t in _attempts[ip] if now - t < WINDOW_SECONDS]
    if len(_attempts[ip]) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera 5 minutos.")
    _attempts[ip].append(now)
