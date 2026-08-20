import pytest

from app.domain import ensure_provider_can_quote, next_quote_version


def test_unverified_provider_cannot_quote() -> None:
    with pytest.raises(PermissionError):
        ensure_provider_can_quote("under_review", True, "published")


def test_closed_request_cannot_receive_quote() -> None:
    with pytest.raises(ValueError):
        ensure_provider_can_quote("verified", True, "closed")


def test_quote_edit_increments_version() -> None:
    assert next_quote_version(2, "active") == 3


def test_accepted_quote_cannot_be_edited() -> None:
    with pytest.raises(ValueError):
        next_quote_version(2, "accepted")
