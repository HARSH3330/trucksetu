import pytest
from fastapi import HTTPException
from app.core.config import settings
from app.services.dependencies import get_private_document_storage

def test_missing_private_storage_fails_closed_with_controlled_unavailability(monkeypatch):
    monkeypatch.setattr(settings,'AWS_S3_BUCKET','')
    with pytest.raises(HTTPException) as failure:
        get_private_document_storage()
    assert failure.value.status_code==503
