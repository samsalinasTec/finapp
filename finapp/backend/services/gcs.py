import os, mimetypes, uuid
from google.cloud import storage
from ..settings import GCS_BUCKET

def upload_to_gcs(local_path: str) -> str:
    if not GCS_BUCKET:
        raise RuntimeError("GCS_BUCKET no configurado")
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    key = f"uploads/{uuid.uuid4().hex}{os.path.splitext(local_path)[1]}"
    blob = bucket.blob(key)
    content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    blob.upload_from_filename(local_path, content_type=content_type)
    return f"gs://{GCS_BUCKET}/{key}", content_type
