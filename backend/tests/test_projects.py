import pytest
from fastapi.testclient import TestClient

from app.api.v1.routers.projects import router as projects_router
from app.api.v1.routers.users import router as users_router

PROJECT = {"name": "Бот", "description": "Telegram-бот", "skills_vector": {"python": 5}}


@pytest.fixture()
def api(make_client):
    return make_client(users_router, projects_router)


def login(client: TestClient, email: str) -> TestClient:
    creds = {"email": email, "password": "secret123"}
    assert client.post("/users/register", json=creds).status_code == 201
    assert client.post("/users/login", json=creds).status_code == 200
    return client


@pytest.fixture()
def owner(api):
    return login(api, "owner@example.com")


@pytest.fixture()
def stranger(api):
    return login(TestClient(api.app, base_url="https://testserver"), "x@example.com")


def create(client, **overrides):
    resp = client.post("/projects/", json={**PROJECT, **overrides})
    assert resp.status_code == 200, resp.text
    return resp.json()


def project_ids(client, **params):
    resp = client.get("/projects/", params=params)
    assert resp.status_code == 200
    return [p["name"] for p in resp.json()["data"]]


def test_requires_auth(api):
    assert api.post("/projects/", json=PROJECT).status_code == 401
    assert api.get("/projects/").status_code == 401


def test_crud(owner):
    assert create(owner) == PROJECT

    [item] = owner.get("/projects/").json()["data"]
    project = owner.get(f"/projects/{item['id']}").json()
    assert project["name"] == PROJECT["name"]
    assert project["skills_vector"] == PROJECT["skills_vector"]

    patched = {"name": "Новый", "description": "d", "skills_vector": {"go": 1}}
    resp = owner.patch(f"/projects/{item['id']}", json=patched)
    assert resp.status_code == 200
    assert resp.json() == patched
    assert owner.get(f"/projects/{item['id']}").json()["name"] == "Новый"

    resp = owner.delete(f"/projects/{item['id']}")
    assert resp.json() == {"success": True, "detail": "Проект успешно удален!"}
    assert owner.get(f"/projects/{item['id']}").status_code == 404


def test_search_and_sort(owner):
    for name in ("Бета", "Альфа", "Гамма"):
        create(owner, name=name)
    assert project_ids(owner, sort="name_asc") == ["Альфа", "Бета", "Гамма"]
    assert project_ids(owner, sort="name_desc") == ["Гамма", "Бета", "Альфа"]
    assert project_ids(owner, search="льф") == ["Альфа"]
    assert owner.get("/projects/", params={"sort": "bad"}).status_code == 422


def test_other_user_has_no_access(owner, stranger):
    create(owner)
    project_id = owner.get("/projects/").json()["data"][0]["id"]

    assert stranger.get("/projects/").json()["data"] == []
    assert stranger.get(f"/projects/{project_id}").status_code == 403
    assert stranger.patch(f"/projects/{project_id}", json=PROJECT).status_code == 403
    assert stranger.delete(f"/projects/{project_id}").status_code == 403
    assert owner.get(f"/projects/{project_id}").status_code == 200


@pytest.mark.parametrize(
    "field,value", [("name", "x" * 256), ("description", "x" * 1025)]
)
def test_validation(owner, field, value):
    resp = owner.post("/projects/", json={**PROJECT, field: value})
    assert resp.status_code == 400


def test_unknown_project(owner):
    assert owner.get("/projects/999").status_code == 404
    assert owner.delete("/projects/999").status_code == 404
