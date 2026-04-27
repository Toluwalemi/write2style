"""End-to-end integration test of the full user flow:
create persona → upload sample → list samples → generate → delete persona.

External services (Firestore, GCS, OpenAI, OpenRouter, Pinecone, Clerk auth) are
all replaced with in-process fakes. The test verifies the routes wire together
correctly, request/response shapes match what the frontend expects, and the
streaming generate endpoint actually streams.
"""
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class FakeFirestore:
    """Minimal in-memory store keyed by (user_id, persona_id, sample_id?)."""

    def __init__(self):
        # personas: dict[(user_id, persona_id)] -> dict
        self.personas: dict[tuple[str, str], dict] = {}
        # samples: dict[(user_id, persona_id, sample_id)] -> dict
        self.samples: dict[tuple[str, str, str], dict] = {}

    def list_personas(self, user_id):
        return [
            (pid, data) for (uid, pid), data in self.personas.items() if uid == user_id
        ]

    def list_samples(self, user_id, persona_id):
        return [
            (sid, data)
            for (uid, pid, sid), data in self.samples.items()
            if uid == user_id and pid == persona_id
        ]


def _resolve(value):
    return "ts" if value is _SERVER_TS else value


_SERVER_TS = object()


def _make_doc(store_get, store_set, store_delete, doc_id):
    """Builds a Firestore-like document reference."""
    snap = MagicMock()

    def refresh_snap():
        data = store_get()
        snap.exists = data is not None
        snap.id = doc_id
        snap.to_dict = lambda d=data: dict(d) if d else {}

    refresh_snap()

    def _set(data):
        store_set({k: _resolve(v) for k, v in data.items()})
        refresh_snap()

    def _update(data):
        existing = store_get() or {}
        merged = {**existing, **{k: _resolve(v) for k, v in data.items()}}
        store_set(merged)
        refresh_snap()

    def _delete():
        store_delete()
        refresh_snap()

    def _get():
        refresh_snap()
        return snap

    ref = MagicMock()
    ref.set = _set
    ref.update = _update
    ref.delete = _delete
    ref.get = _get
    ref.id = doc_id
    return ref, snap


def _persona_ref_factory(fake: FakeFirestore):
    def persona_ref(user_id, persona_id):
        key = (user_id, persona_id)
        ref, _snap = _make_doc(
            store_get=lambda: fake.personas.get(key),
            store_set=lambda d: fake.personas.__setitem__(key, d),
            store_delete=lambda: fake.personas.pop(key, None),
            doc_id=persona_id,
        )

        def collection(name):
            assert name == "samples"
            sub = MagicMock()

            def stream():
                for sid, data in fake.list_samples(user_id, persona_id):
                    sample_snap = MagicMock()
                    sample_snap.id = sid
                    sample_snap.to_dict = lambda d=data: dict(d)
                    sample_ref = MagicMock()
                    sample_ref.delete = lambda u=user_id, p=persona_id, s=sid: fake.samples.pop(
                        (u, p, s), None
                    )
                    sample_snap.reference = sample_ref
                    yield sample_snap

            sub.stream = stream
            return sub

        ref.collection = collection
        return ref

    return persona_ref


def _user_personas_ref_factory(fake: FakeFirestore):
    def user_personas_ref(user_id):
        m = MagicMock()

        def stream():
            for pid, data in fake.list_personas(user_id):
                snap = MagicMock()
                snap.id = pid
                snap.to_dict = lambda d=data: dict(d)
                yield snap

        m.stream = stream
        return m

    return user_personas_ref


def _persona_samples_ref_factory(fake: FakeFirestore):
    def persona_samples_ref(user_id, persona_id):
        m = MagicMock()

        def stream():
            for sid, data in fake.list_samples(user_id, persona_id):
                snap = MagicMock()
                snap.id = sid
                snap.to_dict = lambda d=data: dict(d)
                yield snap

        def document(sample_id):
            key = (user_id, persona_id, sample_id)
            ref, _ = _make_doc(
                store_get=lambda: fake.samples.get(key),
                store_set=lambda d: fake.samples.__setitem__(key, d),
                store_delete=lambda: fake.samples.pop(key, None),
                doc_id=sample_id,
            )
            return ref

        m.stream = stream
        m.document = document
        return m

    return persona_samples_ref


@contextmanager
def _patched_app():
    fake = FakeFirestore()

    persona_ref_fn = _persona_ref_factory(fake)
    user_personas_fn = _user_personas_ref_factory(fake)
    persona_samples_fn = _persona_samples_ref_factory(fake)

    fake_dna = {
        "tone": "terse and observational",
        "sentence_structure": "short, declarative",
        "vocabulary": "plain, technical",
        "punctuation": "em dashes for asides",
        "idioms": ["death by a thousand cuts"],
        "do_not": ["hedge words"],
    }

    def fake_stream_draft(style_dna, few_shot, prompt):
        yield "Hello "
        yield "from "
        yield "the test."

    patches = [
        patch("app.main.ensure_index"),
        patch("google.cloud.firestore.SERVER_TIMESTAMP", _SERVER_TS),
        patch("app.routers.personas.persona_ref", persona_ref_fn),
        patch("app.routers.personas.user_personas_ref", user_personas_fn),
        patch("app.routers.samples.persona_ref", persona_ref_fn),
        patch("app.routers.samples.persona_samples_ref", persona_samples_fn),
        patch("app.routers.generate.persona_ref", persona_ref_fn),
        patch("app.routers.personas.delete_namespace"),
        patch("app.routers.personas.delete_prefix"),
        patch("app.routers.samples.upload_bytes"),
        patch("app.routers.samples.upsert_chunks"),
        patch("app.routers.samples.refine_style_dna", return_value=fake_dna),
        patch("app.routers.samples.embed", return_value=[[0.1] * 1536]),
        patch("app.routers.generate.embed", return_value=[[0.1] * 1536]),
        patch(
            "app.routers.generate.query_similar",
            return_value=[{"text": "past excerpt 1", "filename": "a.md"}],
        ),
        patch("app.routers.generate.stream_draft", side_effect=fake_stream_draft),
    ]
    for p in patches:
        p.start()
    try:
        from app.auth import current_user
        from app.main import app

        app.dependency_overrides[current_user] = lambda: "test-user"
        try:
            yield TestClient(app), fake
        finally:
            app.dependency_overrides.clear()
    finally:
        for p in reversed(patches):
            p.stop()


@pytest.fixture
def client_and_store():
    with _patched_app() as (client, fake):
        yield client, fake


def test_full_user_flow(client_and_store):
    client, fake = client_and_store

    # 1. List is empty initially
    r = client.get("/api/personas")
    assert r.status_code == 200
    assert r.json() == []

    # 2. Create a persona
    r = client.post(
        "/api/personas",
        json={"name": "Tech Blog", "description": "casual technical voice"},
    )
    assert r.status_code == 201
    persona = r.json()
    assert persona["name"] == "Tech Blog"
    assert persona["description"] == "casual technical voice"
    assert persona["sample_count"] == 0
    assert persona["style_dna"] is None
    persona_id = persona["id"]
    assert persona_id

    # 3. Persona shows up in list
    r = client.get("/api/personas")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == persona_id

    # 4. Get persona by id
    r = client.get(f"/api/personas/{persona_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Tech Blog"

    # 5. Samples list is empty
    r = client.get(f"/api/personas/{persona_id}/samples")
    assert r.status_code == 200
    assert r.json() == []

    # 6. Upload a sample
    files = {"file": ("notes.md", b"# Hello\n\nThis is some sample text.", "text/markdown")}
    r = client.post(f"/api/personas/{persona_id}/samples", files=files)
    assert r.status_code == 201, r.text
    sample = r.json()
    assert sample["filename"] == "notes.md"
    assert sample["chunk_count"] >= 1
    assert sample["char_count"] > 0

    # 7. Persona now has a style_dna and sample_count=1
    r = client.get(f"/api/personas/{persona_id}")
    assert r.status_code == 200
    fresh = r.json()
    assert fresh["sample_count"] == 1
    assert fresh["style_dna"] is not None
    assert "tone" in fresh["style_dna"]

    # 8. Samples list now shows it
    r = client.get(f"/api/personas/{persona_id}/samples")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # 9. Generate streams a draft
    with client.stream(
        "POST",
        f"/api/personas/{persona_id}/generate",
        json={"prompt": "write a short opener for a debugging post"},
    ) as r:
        assert r.status_code == 200
        chunks = list(r.iter_text())
    body = "".join(chunks)
    assert body == "Hello from the test."

    # 10. Delete persona
    r = client.delete(f"/api/personas/{persona_id}")
    assert r.status_code == 204

    # 11. Confirm gone
    r = client.get(f"/api/personas/{persona_id}")
    assert r.status_code == 404
    assert "request_id" in r.json()


def test_unsupported_file_type_returns_415(client_and_store):
    client, _ = client_and_store
    r = client.post(
        "/api/personas",
        json={"name": "P", "description": ""},
    )
    persona_id = r.json()["id"]

    files = {"file": ("img.png", b"\x89PNG fake", "image/png")}
    r = client.post(f"/api/personas/{persona_id}/samples", files=files)
    assert r.status_code == 415
    body = r.json()
    assert "error" in body
    assert "request_id" in body


def test_oversized_file_rejected(client_and_store):
    client, _ = client_and_store
    r = client.post("/api/personas", json={"name": "P", "description": ""})
    persona_id = r.json()["id"]

    big_data = b"x" * (10 * 1024 * 1024 + 1)
    files = {"file": ("big.txt", big_data, "text/plain")}
    r = client.post(f"/api/personas/{persona_id}/samples", files=files)
    assert r.status_code == 413


def test_empty_text_extraction_rejected(client_and_store):
    client, _ = client_and_store
    r = client.post("/api/personas", json={"name": "P", "description": ""})
    persona_id = r.json()["id"]

    files = {"file": ("empty.txt", b"   \n\n  ", "text/plain")}
    r = client.post(f"/api/personas/{persona_id}/samples", files=files)
    assert r.status_code == 422


def test_generate_404_for_unknown_persona(client_and_store):
    client, _ = client_and_store
    r = client.post(
        "/api/personas/does-not-exist/generate",
        json={"prompt": "anything"},
    )
    assert r.status_code == 404


def test_create_persona_validation_error(client_and_store):
    client, _ = client_and_store
    r = client.post("/api/personas", json={"name": "", "description": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "Validation error"
    assert "details" in body
    assert "request_id" in body


def test_generate_validation_error_empty_prompt(client_and_store):
    client, _ = client_and_store
    r = client.post("/api/personas", json={"name": "P", "description": ""})
    persona_id = r.json()["id"]

    r = client.post(f"/api/personas/{persona_id}/generate", json={"prompt": ""})
    assert r.status_code == 422
