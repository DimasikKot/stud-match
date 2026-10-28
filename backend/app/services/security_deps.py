from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session
from redis import Redis
from app.core.database import get_db
from app.models.db import User
from app.services.security import decode_access_token
from app.core.config import settings


def get_redis() -> Redis:
    use_tls = settings.REDIS_PORT == 6150

    redis_kwargs = {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "password": settings.REDIS_PASSWORD,
        "decode_responses": True,
        "socket_timeout": 5.0,
    }

    if use_tls:
        redis_kwargs.update({"ssl": True, "ssl_cert_reqs": "none"})

    return Redis(**redis_kwargs)


import redis.asyncio as aioredis


def get_async_redis() -> aioredis.Redis:
    use_tls = settings.REDIS_PORT == 6150

    redis_kwargs = {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "password": settings.REDIS_PASSWORD,
        "decode_responses": True,
        "socket_timeout": 5.0,
    }

    if use_tls:
        redis_kwargs.update({"ssl": True, "ssl_cert_reqs": "none"})

    return aioredis.Redis(**redis_kwargs)


access_cookie_scheme = APIKeyCookie(
    name="access_token",
    scheme_name="AccessTokenCookie",
    description="HttpOnly cookie с access-токеном",
    auto_error=False,
)

refresh_cookie_scheme = APIKeyCookie(
    name="refresh_token",
    scheme_name="RefreshTokenCookie",
    description="HttpOnly cookie с refresh-токеном",
    auto_error=False,
)


def get_current_user(
    access_token: str | None = Security(access_cookie_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing",
        )

    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
