from pydantic import BaseModel
import uuid
from datetime import timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Security,
    status,
)
from redis import Redis
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.security_deps import (
    get_current_user,
    get_redis,
    refresh_cookie_scheme,
)
from app.models.db import User
from app.services.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["Users"])


class UserRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

COOKIE_OPTIONS = dict(
    httponly=settings.COOKIE_HTTPONLY,
    secure=settings.COOKIE_SECURE,
    samesite=settings.COOKIE_SAMESITE,
)


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        max_age=settings.USER_JWT_ACCESS_TOKEN_EXPIRATION_HOURS * 3600,
        **COOKIE_OPTIONS,  # type: ignore
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        max_age=settings.USER_JWT_REFRESH_TOKEN_EXPIRATION_HOURS * 3600,
        **COOKIE_OPTIONS,  # type: ignore
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        ACCESS_COOKIE,
        **COOKIE_OPTIONS,  # type: ignore
    )
    response.delete_cookie(
        REFRESH_COOKIE,
        **COOKIE_OPTIONS,  # type: ignore
    )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_in: UserRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    response: Response,
    user_in: UserRequest,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Создаём access-токен
    access_token = create_access_token(user.id)

    # Создаём refresh-токен с уникальным jti
    jti = str(uuid.uuid4())
    refresh_token = create_refresh_token(user.id, jti)

    # Сохраняем jti в Redis (с TTL, равным времени жизни refresh-токена)
    redis.setex(
        f"refresh:{jti}",
        timedelta(hours=settings.USER_JWT_REFRESH_TOKEN_EXPIRATION_HOURS),
        str(user.id),
    )

    # Устанавливаем куки
    _set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    response: Response,
    refresh_token: str | None = Security(refresh_cookie_scheme),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
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
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # --- РОТАЦИЯ: удаляем старый jti и создаём новый ---
    redis.delete(f"refresh:{jti}")

    new_access_token = create_access_token(user.id)

    new_jti = str(uuid.uuid4())
    new_refresh_token = create_refresh_token(user.id, new_jti)

    redis.setex(
        f"refresh:{new_jti}",
        timedelta(hours=settings.USER_JWT_REFRESH_TOKEN_EXPIRATION_HOURS),
        str(user.id),
    )

    # Устанавливаем новые куки
    _set_auth_cookies(response, new_access_token, new_refresh_token)

    return TokenResponse(access_token=new_access_token)


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str | None = Security(refresh_cookie_scheme),
    redis: Redis = Depends(get_redis),
):
    # Отзываем refresh-токен, если он есть
    if refresh_token:
        payload = decode_refresh_token(refresh_token)
        if payload and payload.get("jti"):
            redis.delete(f"refresh:{payload['jti']}")

    # Удаляем куки
    _clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
