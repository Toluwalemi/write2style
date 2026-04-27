import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from google.cloud.firestore import SERVER_TIMESTAMP

from ..auth import current_user
from ..config import settings
from ..embeddings import embed
from ..extraction import chunk_text, extract_text
from ..firestore_client import persona_ref, persona_samples_ref
from ..llm import refine_style_dna
from ..models import Sample
from ..storage import upload_bytes
from ..vectorstore import upsert_chunks

log = logging.getLogger("app.samples")

router = APIRouter(prefix="/api/personas/{persona_id}/samples", tags=["samples"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get("")
def list_samples(persona_id: str, user_id: str = Depends(current_user)) -> list[Sample]:
    if not persona_ref(user_id, persona_id).get().exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Persona not found")
    out: list[Sample] = []
    for doc in persona_samples_ref(user_id, persona_id).stream():
        d = doc.to_dict() or {}
        out.append(
            Sample(
                id=doc.id,
                filename=d.get("filename", ""),
                content_type=d.get("content_type", ""),
                chunk_count=d.get("chunk_count", 0),
                char_count=d.get("char_count", 0),
            )
        )
    return out


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_sample(
    persona_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(current_user),
) -> Sample:
    pref = persona_ref(user_id, persona_id)
    snap = pref.get()
    if not snap.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Persona not found")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")

    text = extract_text(file.filename or "upload", file.content_type or "", data)
    if not text.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Could not extract text")

    sample_id = uuid.uuid4().hex
    gcs_path = f"users/{user_id}/personas/{persona_id}/samples/{sample_id}-{file.filename}"
    upload_bytes(gcs_path, data, file.content_type or "application/octet-stream")

    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    vectors = embed(chunks) if chunks else []
    upsert_chunks(persona_id, sample_id, file.filename or "sample", chunks, vectors)

    current_dna = (snap.to_dict() or {}).get("style_dna")
    new_dna = refine_style_dna(current_dna, text)

    persona_samples_ref(user_id, persona_id).document(sample_id).set(
        {
            "filename": file.filename or "sample",
            "content_type": file.content_type or "",
            "gcs_path": gcs_path,
            "chunk_count": len(chunks),
            "char_count": len(text),
            "created_at": SERVER_TIMESTAMP,
        }
    )
    pref.update(
        {
            "style_dna": new_dna,
            "sample_count": (snap.to_dict() or {}).get("sample_count", 0) + 1,
            "updated_at": SERVER_TIMESTAMP,
        }
    )

    log.info(
        "sample_uploaded",
        extra={
            "persona_id": persona_id,
            "sample_id": sample_id,
            "chunks": len(chunks),
            "chars": len(text),
            "bytes": len(data),
        },
    )
    return Sample(
        id=sample_id,
        filename=file.filename or "sample",
        content_type=file.content_type or "",
        chunk_count=len(chunks),
        char_count=len(text),
    )
