from urllib.parse import parse_qs, urlsplit

import pytest

from app.services.account_email import account_email_message


@pytest.mark.parametrize("channel,route,secret", [("email", "account-verify", "123456"), ("password_reset", "account-reset", "a" * 43)])
def test_links_use_configured_frontend_fragment(monkeypatch, channel, route, secret):
    from app.core.config import settings
    monkeypatch.setattr(settings, "PUBLIC_FRONTEND_URL", "http://127.0.0.1:5173")
    message = account_email_message("fictional+customer@example.com", channel, secret)
    link = next(line for line in message.splitlines() if line.startswith("http"))
    parsed = urlsplit(link)
    assert parsed.netloc == "127.0.0.1:5173"
    assert not parsed.query
    view, query = parsed.fragment.split("?", 1)
    assert view == route
    assert parse_qs(query)["email"] == ["fictional+customer@example.com"]
    assert parse_qs(query)["code" if channel == "email" else "token"] == [secret]


@pytest.mark.parametrize("url", ["https://user:pass@example.com", "https://example.com/?next=evil", "javascript:alert(1)", "http://example.com", "https://example.com/#bad"])
def test_unsafe_frontend_urls_are_rejected(url):
    from pydantic import ValidationError
    from app.core.config import Settings
    with pytest.raises(ValidationError):
        Settings(_env_file=None, PUBLIC_FRONTEND_URL=url)
