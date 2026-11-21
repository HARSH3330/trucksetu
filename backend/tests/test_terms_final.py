"""The published Terms are the lawyer-approved final version with every placeholder filled."""
import asyncio
from pathlib import Path

from app.api.terms import TERMS_CONTENT, TERMS_VERSION, terms

LEGAL = Path(__file__).parents[1] / "app" / "legal"


def test_terms_are_published_as_final():
    body = asyncio.run(terms())
    assert body["status"] == "final"
    assert "draft" not in TERMS_VERSION.lower()


def test_no_placeholder_or_draft_wording_remains():
    assert "[" not in TERMS_CONTENT and "]" not in TERMS_CONTENT
    assert "draft" not in TERMS_CONTENT.lower()
    assert "require confirmation before public launch" not in TERMS_CONTENT
    assert "Registered Address" not in TERMS_CONTENT


def test_owner_confirmed_contact_and_courts_are_present():
    assert "courts located in **Delhi, India**" in TERMS_CONTENT
    for detail in ("harshagarwal244@gmail.com", "+91 75004 00666", "www.transivox.in"):
        assert detail in TERMS_CONTENT


def test_previous_version_is_preserved():
    assert "2026-10-08-draft-v1" in (LEGAL / "terms-v1.txt").read_text(encoding="utf-8")
