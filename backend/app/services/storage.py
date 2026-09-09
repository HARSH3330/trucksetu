from __future__ import annotations

import re
import uuid
from pathlib import PurePath

import boto3

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}


class PrivateDocumentStorage:
    def __init__(self) -> None:
        if not settings.AWS_S3_BUCKET:
            raise RuntimeError("Private document storage is not configured")
        self.bucket = settings.AWS_S3_BUCKET
        self.client = boto3.client("s3", region_name=settings.AWS_REGION, aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None)

    def upload_url(self, provider_id: uuid.UUID, document_type: str, filename: str, content_type: str) -> tuple[str, str]:
        if content_type not in ALLOWED_CONTENT_TYPES: raise ValueError("Only PDF, JPEG and PNG documents are accepted")
        suffix = PurePath(filename).suffix.lower()
        if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}: raise ValueError("Unsupported document filename")
        safe = re.sub(r"[^a-zA-Z0-9._-]", "_", PurePath(filename).name)
        key = f"kyc/{provider_id}/{document_type}/{uuid.uuid4()}-{safe}"
        url = self.client.generate_presigned_url("put_object", Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type, "ServerSideEncryption": "AES256"}, ExpiresIn=600)
        return key, url

    def confirm(self, key: str) -> dict[str, object]:
        return self.client.head_object(Bucket=self.bucket, Key=key)

    def detected_content_type(self, key: str) -> str | None:
        response = self.client.get_object(Bucket=self.bucket, Key=key, Range="bytes=0-4095")
        content = response["Body"].read(4096)
        if content.startswith(b"%PDF-"):
            return "application/pdf"
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        return None

    def download_url(self, key: str) -> str:
        return self.client.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": key, "ResponseContentDisposition": "attachment"}, ExpiresIn=300)
