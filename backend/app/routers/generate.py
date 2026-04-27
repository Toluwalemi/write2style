import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..auth import current_user
from ..config import settings
from ..embeddings import embed
from ..firestore_client import persona_ref
from ..llm import stream_draft
from ..models import GenerateRequest
from ..vectorstore import query_similar

log = logging.getLogger("app.generate")

router = APIRouter(prefix="/api/personas/{persona_id}", tags=["generate"])


@router.post("/generate")
def generate(
    persona_id: str,
    body: GenerateRequest,
    user_id: str = Depends(current_user),
) -> StreamingResponse:
    snap = persona_ref(user_id, persona_id).get()
    if not snap.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Persona not found")

    data = snap.to_dict() or {}
    style_dna = data.get("style_dna") or {}

    query_vec = embed([body.prompt])[0]
    matches = query_similar(persona_id, query_vec, settings.top_k_few_shot)
    few_shot = [m["text"] for m in matches if m.get("text")]

    log.info(
        "generate_request",
        extra={
            "persona_id": persona_id,
            "prompt_chars": len(body.prompt),
            "few_shot_count": len(few_shot),
            "has_style_dna": bool(style_dna),
        },
    )

    return StreamingResponse(
        stream_draft(style_dna, few_shot, body.prompt),
        media_type="text/plain; charset=utf-8",
    )
