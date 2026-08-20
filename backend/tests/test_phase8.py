import pytest
from app.domain import contains_contact_details,ensure_chat_allowed


def test_chat_requires_confirmed_booking() -> None:
    with pytest.raises(PermissionError):ensure_chat_allowed("advance_pending","customer",{"customer","provider"})
    ensure_chat_allowed("booking_confirmed","customer",{"customer","provider"})


def test_non_participant_cannot_send_message() -> None:
    with pytest.raises(PermissionError):ensure_chat_allowed("booking_confirmed","stranger",{"customer","provider"})


def test_contact_detail_detection() -> None:
    assert contains_contact_details("Call me on +91 9876543210")
    assert contains_contact_details("Email dispatch@example.in")
    assert not contains_contact_details("Truck reaches gate number 12 at 7 AM")
