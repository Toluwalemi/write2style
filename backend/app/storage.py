import logging

from google.cloud import storage

from .config import settings
from .logging_config import timed

log = logging.getLogger("app.storage")

_client: storage.Client | None = None


def _bucket() -> storage.Bucket:
    global _client
    if _client is None:
        _client = storage.Client(project=settings.gcp_project)
    return _client.bucket(settings.gcs_bucket)


def upload_bytes(path: str, data: bytes, content_type: str) -> str:
    blob = _bucket().blob(path)
    with timed(log, "gcs_upload", path=path, bytes=len(data), content_type=content_type):
        blob.upload_from_string(data, content_type=content_type)
    return f"gs://{settings.gcs_bucket}/{path}"


def delete_prefix(prefix: str) -> None:
    bucket = _bucket()
    blobs = list(bucket.list_blobs(prefix=prefix))
    if blobs:
        with timed(log, "gcs_delete_prefix", prefix=prefix, count=len(blobs)):
            bucket.delete_blobs(blobs)
