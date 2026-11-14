"""Both supported deployment roots must install the reviewed API dependencies."""
from pathlib import Path
import tomllib


def test_supported_deployment_roots_use_same_runtime_dependencies():
    root = Path(__file__).resolve().parents[2]
    manifests = [tomllib.loads((root / name).read_text(encoding="utf-8"))
                 for name in ("pyproject.toml", "backend/pyproject.toml")]
    assert set(manifests[0]["project"]["dependencies"]) == set(manifests[1]["project"]["dependencies"])
