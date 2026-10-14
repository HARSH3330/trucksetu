from __future__ import annotations

import pytest

from e2e_database import safe_database_url


def configure(monkeypatch: pytest.MonkeyPatch, url: str = 'postgresql://u:p@127.0.0.1/transivox_e2e') -> None:
    monkeypatch.setenv('E2E_DATABASE_URL', url)
    monkeypatch.setenv('E2E_ALLOWED_DATABASE_HOSTS', '127.0.0.1,localhost')
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('TRANSIVOX_E2E', 'true')
    monkeypatch.delenv('E2E_REAL_AWS', raising=False)


def test_requires_dedicated_url_without_application_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    configure(monkeypatch)
    monkeypatch.delenv('E2E_DATABASE_URL')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://u:p@127.0.0.1/transivox_e2e')
    with pytest.raises(RuntimeError, match='E2E_DATABASE_URL is required'):
        safe_database_url()


@pytest.mark.parametrize('url', [
    'postgresql://u:p@127.0.0.1/transivox_test',
    'postgresql://u:p@127.0.0.1/my_transivox_e2e',
    'postgresql://u:p@127.0.0.1/transivox_e2e%20',
])
def test_requires_exact_database_name(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    configure(monkeypatch, url)
    with pytest.raises(RuntimeError, match='exactly transivox_e2e'):
        safe_database_url()


def test_requires_exact_allowed_host(monkeypatch: pytest.MonkeyPatch) -> None:
    configure(monkeypatch, 'postgresql://u:p@localhost.attacker.test/transivox_e2e')
    with pytest.raises(RuntimeError, match='not explicitly allowed'):
        safe_database_url()


def test_rejects_public_host_even_when_explicitly_listed(monkeypatch: pytest.MonkeyPatch) -> None:
    configure(monkeypatch, 'postgresql://u:p@database.example.com/transivox_e2e')
    monkeypatch.setenv('E2E_ALLOWED_DATABASE_HOSTS', 'database.example.com')
    with pytest.raises(RuntimeError, match='local test host'):
        safe_database_url()


def test_forbids_real_aws_and_non_test_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    configure(monkeypatch)
    monkeypatch.setenv('E2E_REAL_AWS', 'true')
    with pytest.raises(RuntimeError, match='never resets'):
        safe_database_url()
    monkeypatch.setenv('E2E_REAL_AWS', 'false')
    monkeypatch.setenv('APP_ENV', 'production')
    with pytest.raises(RuntimeError, match='local test mode'):
        safe_database_url()


def test_accepts_exact_local_test_database(monkeypatch: pytest.MonkeyPatch) -> None:
    configure(monkeypatch)
    assert safe_database_url() == 'postgresql://u:p@127.0.0.1/transivox_e2e'


@pytest.mark.parametrize('query', ['host=remote.invalid', 'hostaddr=192.0.2.1', 'dbname=production', 'service=production', 'port=6543', '%68ost=remote.invalid'])
def test_rejects_driver_connection_target_overrides(monkeypatch, query):
    configure(monkeypatch, 'postgresql://u:p@127.0.0.1/transivox_e2e?' + query)
    with pytest.raises(RuntimeError, match='connection option'):
        safe_database_url()
