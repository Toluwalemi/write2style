import io

from fastapi import HTTPException, status
from pypdf import PdfReader

SUPPORTED = {"text/plain", "text/markdown", "application/pdf"}


def extract_text(filename: str, content_type: str, data: bytes) -> str:
    ct = (content_type or "").lower()
    name = filename.lower()

    if name.endswith(".pdf") or ct == "application/pdf":
        return _extract_pdf(data)
    if name.endswith((".txt", ".md")) or ct in {"text/plain", "text/markdown"}:
        return data.decode("utf-8", errors="replace")

    raise HTTPException(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Unsupported file type: {content_type or name}",
    )


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    step = max(size - overlap, 1)
    for start in range(0, len(text), step):
        chunk = text[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= len(text):
            break
    return chunks
