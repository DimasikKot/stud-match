import httpx
import pytest
from botocore.exceptions import ClientError

from app.api.v1.routers import healths
from app.services.security_deps import get_async_redis


class FakeAsyncRedis:
    def __init__(self, fail=False):
        self.fail = fail
        self.closed = False

    async def ping(self):
        if self.fail:
            raise ConnectionError("redis down")
        return True

    async def info(self, section):
        return {
            "memory": {"used_memory_human": "1M", "used_memory_peak_human": "2M"},
            "clients": {"connected_clients": 3},
        }[section]

    async def aclose(self):
        self.closed = True


@pytest.fixture()
def client(make_client, admin):
    return make_client(healths.router, user=admin)


def test_metrics_hidden_from_non_admin(make_client, teacher):
    client = make_client(healths.router, user=teacher)
    body = client.get("/healths/backend").json()
    assert body["success"] is True
    assert body["detail"]
    assert body["metrics"] is None


@pytest.mark.parametrize(
    "path",
    ["/healths/backend", "/healths/postgres", "/healths/redis", "/healths/rustfs"],
)
def test_endpoints_require_auth(make_client, path):
    client = make_client(healths.router)
    assert client.get(path).status_code == 401


def test_backend(client):
    body = client.get("/healths/backend").json()
    assert body["success"] is True
    assert set(body["metrics"]["cookie_settings"]) == {"httpOnly", "secure", "sameSite"}


def test_postgres_unhealthy_reports_error(client):
    # SQLite в тестах не знает version()/pg_database_size — проверяем ветку ошибки
    body = client.get("/healths/postgres").json()
    assert body["success"] is False
    assert body["metrics"]["error"]


@pytest.mark.parametrize("fail", [False, True])
def test_redis(client, fail):
    redis = FakeAsyncRedis(fail=fail)
    client.app.dependency_overrides[get_async_redis] = lambda: redis

    body = client.get("/healths/redis").json()
    assert body["success"] is not fail
    if fail:
        assert body["metrics"]["error"] == "redis down"
    else:
        assert body["metrics"]["used_memory_human"] == "1M"
        assert body["metrics"]["connected_clients"] == 3
    assert redis.closed


class FakeS3:
    def __init__(self, bucket_error=False):
        self.bucket_error = bucket_error

    def head_bucket(self, Bucket):
        if self.bucket_error:
            raise ClientError({"Error": {"Code": "403"}}, "HeadBucket")


@pytest.fixture()
def rustfs(monkeypatch):
    def _setup(status_code=200, bucket_error=False):
        transport = httpx.MockTransport(
            lambda request: httpx.Response(status_code, json={"status": "ok"})
        )
        real_client = httpx.AsyncClient
        monkeypatch.setattr(
            healths.httpx,
            "AsyncClient",
            lambda **kwargs: real_client(transport=transport),
        )
        monkeypatch.setattr(
            healths.boto3, "client", lambda *a, **kw: FakeS3(bucket_error)
        )

    return _setup


def test_rustfs_healthy(client, rustfs):
    rustfs()
    body = client.get("/healths/rustfs").json()
    assert body["success"] is True
    assert body["metrics"]["health_endpoint"]["status_code"] == 200
    assert body["metrics"]["s3_bucket_access"] == "ok"


def test_rustfs_bucket_error_is_still_healthy(client, rustfs):
    rustfs(bucket_error=True)
    body = client.get("/healths/rustfs").json()
    assert body["success"] is True
    assert body["metrics"]["s3_bucket_access"].startswith("error")


def test_rustfs_unhealthy(client, rustfs):
    rustfs(status_code=503)
    body = client.get("/healths/rustfs").json()
    assert body["success"] is False
    assert "503" in body["metrics"]["error"]
