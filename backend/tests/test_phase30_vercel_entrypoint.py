from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.core.config import Settings


ROOT = Path(__file__).resolve().parents[2]


def test_vercel_entrypoint_imports_from_repository_root() -> None:
    environment = os.environ.copy()
    environment.update({"APP_ENV": "test", "DEBUG": "false"})
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from backend.app.vercel import app; assert app.title == 'TransivoX'",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_root_vercel_configuration_uses_wrapper() -> None:
    configuration = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'entrypoint = "backend.app.vercel:app"' in configuration


def test_empty_vercel_values_do_not_override_safe_defaults(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "")
    monkeypatch.setenv("SMTP_PORT", "")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "")
    monkeypatch.setenv("ENABLE_LIVE_GPS", "")

    configuration = Settings(_env_file=None)

    assert configuration.APP_NAME == "TransivoX"
    assert configuration.SMTP_PORT == 587
    assert configuration.RATE_LIMIT_PER_MINUTE == 120
    assert configuration.ENABLE_LIVE_GPS is False
