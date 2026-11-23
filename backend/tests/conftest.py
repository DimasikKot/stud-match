import os

# Дефолт "rustfs host" — невалидный endpoint для boto3, ломает импорт app.services.file
os.environ.setdefault("RUSTFS_URL", "http://localhost:9000")

import pytest  # noqa: E402
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import fakeredis

from app.core.database import Base, get_db
from app.models.db import ROLE_ADMIN, ROLE_TEACHER, UserDB
from app.services.security import hash_password
from app.services.security_deps import get_current_user, get_optional_user, get_redis
from app.api.v1.routers.users import router as users_router  # подправь путь


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(engine):
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def fake_redis():
    # decode_responses=True — код сравнивает redis.get(...) с sub из JWT (str)
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture()
def app(db_session, fake_redis):
    app = FastAPI()
    app.include_router(users_router)

    def _get_db():
        yield db_session

    def _get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_redis] = _get_redis
    yield app
    app.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    with TestClient(app, base_url="https://testserver") as c:
        yield c


@pytest.fixture()
def make_user(db_session):
    """Создаёт пользователя напрямую в БД (регистрация доступна только админу)."""

    def _make(email: str, password: str = "secret123", role: str = ROLE_TEACHER):
        user = UserDB(email=email, hashed_password=hash_password(password), role=role)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture()
def admin(make_user):
    return make_user("admin@example.com", "admin123", ROLE_ADMIN)


@pytest.fixture()
def teacher(make_user):
    return make_user("teacher@example.com")


@pytest.fixture()
def registered_user(make_user):
    payload = {"email": "user@example.com", "password": "secret123"}
    make_user(**payload)
    return payload


@pytest.fixture()
def admin_client(client, admin):
    resp = client.post(
        "/users/login", json={"email": admin.email, "password": "admin123"}
    )
    assert resp.status_code == 200
    return client


@pytest.fixture()
def auth_client(client, registered_user):
    """Клиент, у которого в cookie-jar уже лежат access/refresh после логина."""
    resp = client.post("/users/login", json=registered_user)
    assert resp.status_code == 200
    return client


@pytest.fixture()
def make_client(db_session, fake_redis):
    """Собирает TestClient с нужными роутерами и подменёнными БД/Redis."""

    def _make(*routers, user: UserDB | None = None) -> TestClient:
        """user — от чьего имени выполняются запросы (None — аноним)."""
        app = FastAPI()
        for router in routers:
            app.include_router(router)
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_redis] = lambda: fake_redis
        if user is not None:
            app.dependency_overrides[get_current_user] = lambda: user
            app.dependency_overrides[get_optional_user] = lambda: user
        return TestClient(app, base_url="https://testserver")

    return _make
