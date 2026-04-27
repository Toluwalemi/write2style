import logging

from openai import OpenAI

from .config import settings
from .logging_config import timed

log = logging.getLogger("app.embeddings")

_client: OpenAI | None = None


def _openai() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    total_chars = sum(len(t) for t in texts)
    with timed(
        log,
        "embed",
        model=settings.embedding_model,
        count=len(texts),
        total_chars=total_chars,
    ):
        resp = _openai().embeddings.create(model=settings.embedding_model, input=texts)
    return [row.embedding for row in resp.data]
