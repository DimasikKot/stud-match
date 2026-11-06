import io

import docx
import pytest
from fastapi import HTTPException

from app.models.db import FileDB
from app.services import file as file_service
from app.services import llm as llm_service


def make_pdf(text: str) -> bytes:
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % number + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1))
    for offset in offsets:
        out.write(b"%010d 00000 n \n" % offset)
    out.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, xref)
    )
    return out.getvalue()


def make_docx() -> bytes:
    document = docx.Document()
    document.add_paragraph("Задание 4")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Вариант"
    table.cell(0, 1).text = "7"
    out = io.BytesIO()
    document.save(out)
    return out.getvalue()


@pytest.fixture()
def stored(monkeypatch):
    def _store(name: str, data: bytes) -> FileDB:
        monkeypatch.setattr(
            file_service, "get_file_object", lambda file_db: {"Body": io.BytesIO(data)}
        )
        return FileDB(name=name, object_key="k", path=f"/{name}", size=len(data))

    return _store


def test_pdf_text(stored):
    text = llm_service.read_file_text(stored("doc.PDF", make_pdf("Hello PDF")), 1000)
    assert "Hello PDF" in text


def test_docx_text(stored):
    text = llm_service.read_file_text(stored("Задание 4.docx", make_docx()), 1000)
    assert "Задание 4" in text
    assert "Вариант | 7" in text


def test_document_text_is_truncated(stored):
    assert llm_service.read_file_text(stored("a.docx", make_docx()), 5) == "Задан"


@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("broken.pdf", b"not a pdf"),
        ("old.doc", b"\xd0\xcf\x11\xe0"),
        ("img.png", b"\x89PNG\x00"),
    ],
)
def test_unsupported_files(stored, name, data):
    with pytest.raises(HTTPException) as exc:
        llm_service.read_file_text(stored(name, data), 1000)
    assert exc.value.status_code == 415
