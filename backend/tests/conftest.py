import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import fakeredis

from app.core.database import Base, get_db
from app.models.db import User  # noqa: F401 — регистрирует модель на Base
from app.services.security_deps import get_redis
from app.api.v1.routers.user import router as users_router  # подправь путь


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
def registered_user(client):
    payload = {"email": "user@example.com", "password": "secret123"}
    resp = client.post("/users/register", json=payload)
    assert resp.status_code == 201
    return payload


@pytest.fixture()
def auth_client(client, registered_user):
    """Клиент, у которого в cookie-jar уже лежат access/refresh после логина."""
    resp = client.post("/users/login", json=registered_user)
    assert resp.status_code == 200
    return client
