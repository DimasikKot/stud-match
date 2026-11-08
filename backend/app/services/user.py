import uuid
from datetime import timedelta

from fastapi import HTTPException, status
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db import UserDB
from app.services.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


def register_user(db: Session, email: str, password: str) -> UserDB:
    existing = db.query(UserDB).filter(UserDB.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = UserDB(
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def fetch_users(db: Session) -> list[UserDB]:
    return db.query(UserDB).order_by(UserDB.id).all()


def change_password(
    db: Session, user: UserDB, old_password: str, new_password: str
) -> None:
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )
    user.hashed_password = hash_password(new_password)
    db.commit()


def authenticate_user(db: Session, email: str, password: str) -> UserDB:
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return user


def _store_refresh_jti(redis: Redis, user_id: int, jti: str) -> None:
    # Сохраняем jti в Redis (с TTL, равным времени жизни refresh-токена)
    redis.set(
        f"refresh:{jti}",
        str(user_id),
        ex=timedelta(hours=settings.USER_JWT_REFRESH_TOKEN_EXPIRATION_HOURS),
    )


def issue_auth_tokens(user: UserDB, redis: Redis) -> tuple[str, str]:
    """Создаёт access + refresh токены и сохраняет jti refresh-токена в Redis."""
    access_token = create_access_token(user.id)

    jti = str(uuid.uuid4())
    refresh_token = create_refresh_token(user.id, jti)
    _store_refresh_jti(redis, user.id, jti)

    return access_token, refresh_token


def rotate_auth_tokens(
    db: Session, redis: Redis, refresh_token: str | None
) -> tuple[str, str]:
    """Проверяет refresh-токен, ротирует его и возвращает новую пару токенов."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not user_id or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Проверяем, что jti существует в Redis (токен не отозван)
    stored_user_id = redis.get(f"refresh:{jti}")
    if not stored_user_id or stored_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or reuse detected",
        )

    # Проверяем, что пользователь существует
    user = db.query(UserDB).filter(UserDB.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # --- РОТАЦИЯ: удаляем старый jti и создаём новую пару токенов ---
    redis.delete(f"refresh:{jti}")
    return issue_auth_tokens(user, redis)


def revoke_refresh_token(redis: Redis, refresh_token: str | None) -> None:
    """Отзывает refresh-токен (удаляет его jti из Redis)."""
    if refresh_token:
        payload = decode_refresh_token(refresh_token)
        if payload and payload.get("jti"):
            redis.delete(f"refresh:{payload['jti']}")
