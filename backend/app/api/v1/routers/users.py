from pydantic import BaseModel, ConfigDict

from fastapi import (
    APIRouter,
    Depends,
    Response,
    Security,
    status,
)
from redis import Redis
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import user as user_service
from app.services.security_deps import (
    get_current_user,
    get_redis,
    refresh_cookie_scheme,
)
from app.models.db import UserDB
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["Users"])


class UserRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


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
    return user_service.register_user(db, user_in.email, user_in.password)


@router.post("/login", response_model=TokenResponse)
def login(
    response: Response,
    user_in: UserRequest,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    user = user_service.authenticate_user(db, user_in.email, user_in.password)

    access_token, refresh_token = user_service.issue_auth_tokens(user, redis)

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
    access_token, new_refresh_token = user_service.rotate_auth_tokens(
        db, redis, refresh_token
    )

    # Устанавливаем новые куки
    _set_auth_cookies(response, access_token, new_refresh_token)

    return TokenResponse(access_token=access_token)


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str | None = Security(refresh_cookie_scheme),
    redis: Redis = Depends(get_redis),
):
    # Отзываем refresh-токен, если он есть
    user_service.revoke_refresh_token(redis, refresh_token)

    # Удаляем куки
    _clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def read_me(current_user: UserDB = Depends(get_current_user)):
    return current_user
