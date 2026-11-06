import io
from urllib.parse import quote

import pytest
from botocore.exceptions import ClientError

from app.api.v1.routers.files import router as files_router
from app.models.db import FileDB
from app.services import file as file_service


class FakeS3:
    def __init__(self):
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.fail_upload = False

    def upload_fileobj(self, fileobj, bucket, key, ExtraArgs=None):
        if self.fail_upload:
            raise ClientError({"Error": {"Code": "500", "Message": "boom"}}, "Put")
        self.objects[key] = (fileobj.read(), ExtraArgs["ContentType"])

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        data = self.objects[Key][0]
        return {"Body": io.BytesIO(data), "ContentLength": len(data)}

    def delete_object(self, Bucket, Key):
        self.objects.pop(Key, None)


@pytest.fixture()
def s3(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(file_service, "s3_client", fake)
    return fake


@pytest.fixture()
def client(make_client, s3):
    return make_client(files_router)


def upload(client, *files):
    return client.post(
        "/files/",
        files=[("files", (name, data, "text/plain")) for name, data in files],
    )


def test_upload_and_list(client, s3, db_session):
    resp = upload(client, ("a.txt", b"hello"), ("Отчёт.pdf", b"%PDF"))
    assert resp.status_code == 200
    uploaded = resp.json()
    assert [f["name"] for f in uploaded] == ["a.txt", "Отчёт.pdf"]
    assert [f["size"] for f in uploaded] == [5, 4]
    assert uploaded[1]["object_key"].endswith(".pdf")
    assert set(s3.objects) == {f["object_key"] for f in uploaded}
    assert db_session.query(FileDB).count() == 2

    listed = client.get("/files/").json()["data"]
    assert {f["id"] for f in listed} == {f["id"] for f in uploaded}


def test_upload_requires_files(client):
    assert client.post("/files/").status_code == 422


def test_upload_s3_error(client, s3, db_session):
    s3.fail_upload = True
    resp = upload(client, ("a.txt", b"hello"))
    assert resp.status_code == 502
    assert db_session.query(FileDB).count() == 0


@pytest.mark.parametrize(
    "action,disposition", [("view", "inline"), ("download", "attachment")]
)
def test_view_and_download(client, action, disposition):
    file_id = upload(client, ("Задание.txt", b"text body")).json()[0]["id"]

    resp = client.get(f"/files/{file_id}/{action}")
    assert resp.status_code == 200
    assert resp.content == b"text body"
    assert resp.headers["content-type"].startswith("text/plain")
    assert resp.headers["content-length"] == "9"
    assert resp.headers["content-disposition"] == (
        f"{disposition}; filename*=UTF-8''{quote('Задание.txt')}"
    )


def test_missing_in_storage(client, s3):
    file_id = upload(client, ("a.txt", b"x")).json()[0]["id"]
    s3.objects.clear()
    assert client.get(f"/files/{file_id}/view").status_code == 404


def test_delete(client, s3, db_session):
    file_id = upload(client, ("a.txt", b"x")).json()[0]["id"]

    resp = client.delete(f"/files/{file_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert s3.objects == {}
    assert db_session.query(FileDB).count() == 0


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/files/999/view"),
        ("get", "/files/999/download"),
        ("delete", "/files/999"),
    ],
)
def test_unknown_file(client, method, path):
    assert getattr(client, method)(path).status_code == 404


@pytest.mark.parametrize(
    "name,expected",
    [
        ("a.pdf", "application/pdf"),
        ("a.TXT", "text/plain"),
        ("noext", "application/octet-stream"),
    ],
)
def test_guess_content_type(name, expected):
    file_db = FileDB(name=name, object_key="k", path="/", size=0)
    assert file_service.guess_content_type(file_db) == expected
