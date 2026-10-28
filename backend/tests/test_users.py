from fastapi.testclient import TestClient


class TestRegister:
    def test_success(self, client):
        resp = client.post(
            "/users/register",
            json={"email": "a@b.com", "password": "pw"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "a@b.com"
        assert isinstance(body["id"], int)

    def test_duplicate_email(self, client):
        payload = {"email": "a@b.com", "password": "pw"}
        client.post("/users/register", json=payload)
        resp = client.post("/users/register", json=payload)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]


class TestLogin:
    def test_sets_access_and_refresh_cookies(self, client, registered_user):
        resp = client.post("/users/login", json=registered_user)
        assert resp.status_code == 200

        data = resp.json()
        assert data["token_type"] == "bearer"
        assert data["access_token"]

        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    def test_wrong_password(self, client, registered_user):
        resp = client.post(
            "/users/login",
            json={"email": registered_user["email"], "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_unknown_user(self, client):
        resp = client.post("/users/login", json={"email": "x@y.z", "password": "p"})
        assert resp.status_code == 401


class TestMe:
    def test_requires_auth(self, client):
        resp = client.get("/users/me")
        # 401 или 403 в зависимости от auto_error у security-scheme
        assert resp.status_code in (401, 403)

    def test_returns_current_user(self, auth_client, registered_user):
        resp = auth_client.get("/users/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == registered_user["email"]


class TestRefresh:
    def test_rotates_refresh_token(self, auth_client, fake_redis):
        old_refresh = auth_client.cookies.get("refresh_token")
        assert old_refresh

        old_keys = list(fake_redis.keys("refresh:*"))
        assert len(old_keys) == 1

        resp = auth_client.post("/users/refresh")
        assert resp.status_code == 200

        new_refresh = resp.cookies.get("refresh_token")
        assert new_refresh and new_refresh != old_refresh

        new_keys = list(fake_redis.keys("refresh:*"))
        assert len(new_keys) == 1
        assert old_keys[0] != new_keys[0]  # старый jti удалён, новый добавлен

    def test_missing_cookie(self, client):
        resp = client.post("/users/refresh")
        assert resp.status_code == 401

    def test_reuse_after_rotation_rejected(self, client, registered_user):
        client.post("/users/login", json=registered_user)
        old_refresh = client.cookies.get("refresh_token")

        assert client.post("/users/refresh").status_code == 200

        fresh = TestClient(client.app, base_url="https://testserver")
        fresh.cookies.set("refresh_token", old_refresh, domain="testserver")
        assert fresh.post("/users/refresh").status_code == 401


class TestLogout:
    def test_clears_cookies_and_revokes(self, auth_client, fake_redis):
        old_refresh = auth_client.cookies.get("refresh_token")
        assert old_refresh
        assert len(list(fake_redis.keys("refresh:*"))) == 1

        resp = auth_client.post("/users/logout")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Logged out"}

        # ключ отозван в Redis
        assert list(fake_redis.keys("refresh:*")) == []
        # куки удалены клиентом
        assert auth_client.cookies.get("refresh_token") in (None, "")

        # старый refresh больше не работает
        auth_client.cookies.set("refresh_token", old_refresh, domain="testserver")
        assert auth_client.post("/users/refresh").status_code == 401

    def test_logout_without_cookies_is_idempotent(self, client):
        resp = client.post("/users/logout")
        assert resp.status_code == 200
