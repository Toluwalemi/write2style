from google.cloud import firestore

from .config import settings

_db: firestore.Client | None = None


def db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=settings.gcp_project)
    return _db


def user_personas_ref(user_id: str):
    return db().collection("users").document(user_id).collection("personas")


def persona_ref(user_id: str, persona_id: str):
    return user_personas_ref(user_id).document(persona_id)


def persona_samples_ref(user_id: str, persona_id: str):
    return persona_ref(user_id, persona_id).collection("samples")
