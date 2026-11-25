from app.core.database import get_db
from app.core.db import UserDB, UserRole
from app.services.auth import decode_access_token
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyCookie
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

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
) -> UserDB:
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

    user = db.query(UserDB).filter(UserDB.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def get_optional_user(
    access_token: str | None = Security(access_cookie_scheme),
    db: Session = Depends(get_db),
) -> UserDB | None:
    """Текущий пользователь или None для анонимного запроса."""
    payload = decode_access_token(access_token) if access_token else None
    if not payload:
        return None
    try:
        return db.query(UserDB).filter(UserDB.id == int(payload["sub"])).first()
    except SQLAlchemyError:
        # БД недоступна - считаем запрос анонимным (например, для /healths)
        db.rollback()
        return None


def require_admin(user: UserDB = Depends(get_current_user)) -> UserDB:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return user
