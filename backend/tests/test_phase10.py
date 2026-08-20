import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_production_rejects_default_secret() -> None:
    with pytest.raises(ValidationError):Settings(APP_ENV="production",DEBUG=False)


def test_production_rejects_debug() -> None:
    with pytest.raises(ValidationError):Settings(APP_ENV="production",DEBUG=True,SECRET_KEY="a-secure-production-secret")


def test_non_production_can_use_local_defaults() -> None:
    assert Settings(APP_ENV="test",DEBUG=False).APP_ENV=="test"
