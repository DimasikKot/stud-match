import pytest

from app.api.v1.routers.students import router as students_router

STUDENT = {"name": "Иван", "description": "3 курс", "skills_vector": {"python": 4}}


@pytest.fixture()
def client(make_client, admin):
    return make_client(students_router, user=admin)


def test_requires_admin(make_client, teacher):
    assert make_client(students_router).get("/students/").status_code == 401
    resp = make_client(students_router, user=teacher).get("/students/")
    assert resp.status_code == 403


def create(client, **overrides):
    resp = client.post("/students/", json={**STUDENT, **overrides})
    assert resp.status_code == 200, resp.text
    return resp.json()


def names(client, **params):
    return [s["name"] for s in client.get("/students/", params=params).json()["data"]]


def test_crud(client):
    assert create(client) == STUDENT
    [item] = client.get("/students/").json()["data"]

    student = client.get(f"/students/{item['id']}").json()
    assert student["description"] == "3 курс"
    assert student["skills_vector"] == {"python": 4}

    patched = {"name": "Пётр", "description": "4 курс", "skills_vector": {}}
    assert client.patch(f"/students/{item['id']}", json=patched).json() == patched

    resp = client.delete(f"/students/{item['id']}")
    assert resp.json() == {"success": True, "detail": "Студент успешно удален!"}
    assert client.get("/students/").json()["data"] == []


def test_search_and_sort(client):
    for name in ("Вера", "Анна", "Борис"):
        create(client, name=name)
    assert names(client, sort="name_asc") == ["Анна", "Борис", "Вера"]
    assert names(client, sort="name_desc") == ["Вера", "Борис", "Анна"]
    assert names(client, search="ори") == ["Борис"]


@pytest.mark.parametrize(
    "field,value", [("name", "x" * 256), ("description", "x" * 1025)]
)
def test_validation(client, field, value):
    assert client.post("/students/", json={**STUDENT, field: value}).status_code == 400


def test_unknown_student(client):
    assert client.get("/students/999").status_code == 404
    assert client.patch("/students/999", json=STUDENT).status_code == 404
    assert client.delete("/students/999").status_code == 404
