import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore import SERVER_TIMESTAMP

from ..auth import current_user
from ..firestore_client import persona_ref, user_personas_ref
from ..models import Persona, PersonaCreate
from ..storage import delete_prefix
from ..vectorstore import delete_namespace

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.get("")
def list_personas(user_id: str = Depends(current_user)) -> list[Persona]:
    docs = user_personas_ref(user_id).stream()
    out: list[Persona] = []
    for doc in docs:
        data = doc.to_dict() or {}
        out.append(
            Persona(
                id=doc.id,
                name=data.get("name", ""),
                description=data.get("description", ""),
                style_dna=data.get("style_dna"),
                sample_count=data.get("sample_count", 0),
            )
        )
    return out


@router.post("", status_code=status.HTTP_201_CREATED)
def create_persona(body: PersonaCreate, user_id: str = Depends(current_user)) -> Persona:
    persona_id = uuid.uuid4().hex
    persona_ref(user_id, persona_id).set(
        {
            "name": body.name,
            "description": body.description,
            "style_dna": None,
            "sample_count": 0,
            "created_at": SERVER_TIMESTAMP,
            "updated_at": SERVER_TIMESTAMP,
        }
    )
    return Persona(id=persona_id, name=body.name, description=body.description)


@router.get("/{persona_id}")
def get_persona(persona_id: str, user_id: str = Depends(current_user)) -> Persona:
    snap = persona_ref(user_id, persona_id).get()
    if not snap.exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Persona not found")
    data = snap.to_dict() or {}
    return Persona(
        id=snap.id,
        name=data.get("name", ""),
        description=data.get("description", ""),
        style_dna=data.get("style_dna"),
        sample_count=data.get("sample_count", 0),
    )


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona(persona_id: str, user_id: str = Depends(current_user)) -> None:
    ref = persona_ref(user_id, persona_id)
    if not ref.get().exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Persona not found")

    samples = list(ref.collection("samples").stream())
    for s in samples:
        s.reference.delete()
    ref.delete()

    delete_namespace(persona_id)
    delete_prefix(f"users/{user_id}/personas/{persona_id}/")
