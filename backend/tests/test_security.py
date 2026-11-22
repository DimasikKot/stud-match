from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.services import auth


def test_password_hashing():
    hashed = auth.hash_password("secret")
    assert hashed != "secret"
    assert auth.verify_password("secret", hashed)
    assert not auth.verify_password("wrong", hashed)


def test_access_token_roundtrip():
    payload = auth.decode_access_token(auth.create_access_token(42))
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    payload = auth.decode_refresh_token(auth.create_refresh_token(7, "jti-1"))
    assert payload["sub"] == "7"
    assert payload["jti"] == "jti-1"


def test_tokens_are_not_interchangeable():
    access = auth.create_access_token(1)
    refresh = auth.create_refresh_token(1, "j")
    assert auth.decode_refresh_token(access) is None
    assert auth.decode_access_token(refresh) is None


def test_access_token_with_refresh_type_is_rejected():
    token = jwt.encode(
        {"sub": "1", "type": "refresh"},
        settings.USER_JWT_ACCESS_TOKEN_SECRET,
        algorithm="HS256",
    )
    assert auth.decode_access_token(token) is None


def test_expired_and_garbage_tokens():
    expired = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.USER_JWT_ACCESS_TOKEN_SECRET,
        algorithm="HS256",
    )
    assert auth.decode_access_token(expired) is None
    assert auth.decode_access_token("not.a.token") is None
    assert auth.decode_refresh_token("") is None
