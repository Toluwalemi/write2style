import io
import logging

from fastapi import HTTPException, status
from pypdf import PdfReader

log = logging.getLogger("app.extraction")

SUPPORTED = {"text/plain", "text/markdown", "application/pdf"}


def extract_text(filename: str, content_type: str, data: bytes) -> str:
    ct = (content_type or "").lower()
    name = filename.lower()

    if name.endswith(".pdf") or ct == "application/pdf":
        text = _extract_pdf(data)
        log.info(
            "extract_text",
            extra={"kind": "pdf", "file": filename, "bytes": len(data), "chars": len(text)},
        )
        return text
    if name.endswith((".txt", ".md")) or ct in {"text/plain", "text/markdown"}:
        text = data.decode("utf-8", errors="replace")
        log.info(
            "extract_text",
            extra={"kind": "text", "file": filename, "bytes": len(data), "chars": len(text)},
        )
        return text

    log.warning(
        "extract_text_unsupported",
        extra={"file": filename, "content_type": content_type},
    )
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
