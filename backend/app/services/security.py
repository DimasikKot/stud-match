from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.USER_JWT_ACCESS_TOKEN_EXPIRATION_HOURS
    )
    payload = {"sub": str(subject), "exp": expire, "type": "access"}
    return jwt.encode(
        payload,
        settings.USER_JWT_ACCESS_TOKEN_SECRET,
        algorithm="HS256",
    )


def create_refresh_token(subject: str | int, jti: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.USER_JWT_REFRESH_TOKEN_EXPIRATION_HOURS
    )
    payload = {"sub": str(subject), "exp": expire, "type": "refresh", "jti": jti}
    return jwt.encode(
        payload,
        settings.USER_JWT_REFRESH_TOKEN_SECRET,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.USER_JWT_ACCESS_TOKEN_SECRET,
            algorithms=["HS256"],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.USER_JWT_REFRESH_TOKEN_SECRET,
            algorithms=["HS256"],
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
