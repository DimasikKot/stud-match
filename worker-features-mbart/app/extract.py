import io
import re

from docx import Document
from pypdf import PdfReader


class SkippedFile(Exception):
    """Файл не подлежит анализу, причина передаётся в тексте исключения."""


def extract_text(extension: str, content: bytes) -> str:
    """Достаёт текст из pdf или docx, остальные форматы пропускаются."""
    ext = (extension or "").lower()
    if ext == ".pdf":
        text = _pdf_text(content)
    elif ext == ".docx":
        text = _docx_text(content)
    else:
        raise SkippedFile(f"расширение {ext or 'отсутствует'} не поддерживается")

    text = _normalize(text)
    if not text:
        raise SkippedFile("в файле не найден текст")
    return text


def _pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _docx_text(content: bytes) -> str:
    document = Document(io.BytesIO(content))
    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _normalize(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def split_chunks(text: str, size: int, overlap: int) -> list[str]:
    """Режет текст на куски по size символов с перекрытием overlap,
    по возможности обрывая кусок на границе строки или слова."""
    chunks: list[str] = []
    length = len(text)
    start = 0
    while start < length:
        end = min(start + size, length)
        if end < length:
            cut = text.rfind("\n", start + size // 2, end)
            if cut == -1:
                cut = text.rfind(" ", start + size // 2, end)
            if cut != -1:
                end = cut
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks


def limit_chunks(chunks: list[str], max_chunks: int) -> list[str]:
    """Если кусков больше лимита, равномерно выбирает max_chunks из всего файла."""
    if len(chunks) <= max_chunks:
        return chunks
    if max_chunks <= 1:
        return chunks[:1]
    step = (len(chunks) - 1) / (max_chunks - 1)
    indexes = sorted({round(i * step) for i in range(max_chunks)})
    return [chunks[i] for i in indexes]
