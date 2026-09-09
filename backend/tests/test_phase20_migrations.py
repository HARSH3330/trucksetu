from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND = Path(__file__).resolve().parents[1]


def test_migration_history_is_single_complete_chain() -> None:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_heads() == ["20260909_18"]
    revisions = list(scripts.walk_revisions(base="base", head="heads"))
    assert len(revisions) == 18
    assert revisions[-1].down_revision is None


def test_clean_database_upgrade_compiles_as_postgresql_sql() -> None:
    environment = os.environ.copy()
    environment.update({"APP_ENV": "development", "DATABASE_URL": "postgresql://migration:password@localhost:5432/transivox_migration_check"})
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head", "--sql"],
        cwd=BACKEND, env=environment, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "CREATE TABLE alembic_version" in result.stdout
    assert "20260909_18" in result.stdout
    assert "::json" in result.stdout
