import contextlib
import logging
import uuid

from pinecone import Pinecone, ServerlessSpec

from .config import settings
from .logging_config import timed

log = logging.getLogger("app.vectorstore")

_pc: Pinecone | None = None
_index = None


def _client() -> Pinecone:
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=settings.pinecone_api_key)
    return _pc


def ensure_index():
    global _index
    if _index is not None:
        return _index

    pc = _client()
    existing = pc.list_indexes()
    names = existing.names() if hasattr(existing, "names") else [i.get("name") for i in existing]
    if settings.pinecone_index not in names:
        log.info(
            "pinecone_create_index",
            extra={
                "index": settings.pinecone_index,
                "dimension": settings.embedding_dim,
                "cloud": settings.pinecone_cloud,
                "region": settings.pinecone_region,
            },
        )
        pc.create_index(
            name=settings.pinecone_index,
            dimension=settings.embedding_dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
    _index = pc.Index(settings.pinecone_index)
    return _index


def upsert_chunks(
    namespace: str,
    sample_id: str,
    filename: str,
    chunks: list[str],
    vectors: list[list[float]],
) -> list[str]:
    index = ensure_index()
    vector_ids: list[str] = []
    payload = []
    for chunk, vec in zip(chunks, vectors, strict=True):
        vid = f"{sample_id}:{uuid.uuid4().hex[:12]}"
        vector_ids.append(vid)
        payload.append(
            {
                "id": vid,
                "values": vec,
                "metadata": {
                    "sample_id": sample_id,
                    "filename": filename,
                    "text": chunk,
                },
            }
        )
    if payload:
        with timed(
            log,
            "pinecone_upsert",
            namespace=namespace,
            sample_id=sample_id,
            count=len(payload),
        ):
            index.upsert(vectors=payload, namespace=namespace)
    return vector_ids


def query_similar(namespace: str, vector: list[float], top_k: int) -> list[dict]:
    index = ensure_index()
    with timed(log, "pinecone_query", namespace=namespace, top_k=top_k):
        result = index.query(
            namespace=namespace,
            vector=vector,
            top_k=top_k,
            include_metadata=True,
        )
    matches = result.get("matches", []) if isinstance(result, dict) else result.matches
    out = []
    for m in matches:
        meta = m["metadata"] if isinstance(m, dict) else m.metadata
        out.append({"text": meta.get("text", ""), "filename": meta.get("filename", "")})
    log.info("pinecone_query_result", extra={"namespace": namespace, "matches": len(out)})
    return out


def delete_namespace(namespace: str) -> None:
    index = ensure_index()
    with contextlib.suppress(Exception), timed(
        log, "pinecone_delete_namespace", namespace=namespace
    ):
        index.delete(delete_all=True, namespace=namespace)


def delete_sample(namespace: str, vector_ids: list[str]) -> None:
    if not vector_ids:
        return
    index = ensure_index()
    with timed(
        log,
        "pinecone_delete_sample",
        namespace=namespace,
        count=len(vector_ids),
    ):
        index.delete(ids=vector_ids, namespace=namespace)
