from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pytest

from app.api.kyc import ALLOWED_BY_TYPE, REQUIRED
from app.services.storage import PrivateDocumentStorage


@pytest.mark.parametrize(
    ("content", "expected"),
    [(b"%PDF-1.7 content", "application/pdf"), (b"\xff\xd8\xffjpeg", "image/jpeg"), (b"\x89PNG\r\n\x1a\nimage", "image/png"), (b"<script>alert(1)</script>", None)],
)
def test_uploaded_document_type_is_detected_from_bytes(content: bytes, expected: str | None) -> None:
    storage = object.__new__(PrivateDocumentStorage)
    storage.bucket = "private-test"
    storage.client = SimpleNamespace(get_object=lambda **_: {"Body": BytesIO(content)})
    assert storage.detected_content_type("private-key") == expected


def test_driver_cannot_upload_vehicle_or_company_documents() -> None:
    assert REQUIRED["driver"].issubset(ALLOWED_BY_TYPE["driver"])
    assert "vehicle_rc" not in ALLOWED_BY_TYPE["driver"]
    assert "gst_certificate" not in ALLOWED_BY_TYPE["driver"]


def test_owner_document_policy_includes_requested_pilot_documents() -> None:
    assert {"aadhaar", "pan", "driving_licence", "vehicle_rc"}.issubset(ALLOWED_BY_TYPE["owner"])
