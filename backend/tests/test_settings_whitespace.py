"""A stray tab or space pasted into a dashboard setting must not stop the API from starting."""
import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize('raw,expected', [('\ttrue', True), (' true\n', True), ('  false ', False)])
def test_on_off_settings_ignore_surrounding_whitespace(monkeypatch, raw, expected):
    monkeypatch.setenv('MSG91_WIDGET_ENABLED', raw)
    assert Settings().MSG91_WIDGET_ENABLED is expected


def test_real_nonsense_is_still_refused(monkeypatch):
    monkeypatch.setenv('MSG91_WIDGET_ENABLED', 'maybe')
    with pytest.raises(ValidationError):
        Settings()
