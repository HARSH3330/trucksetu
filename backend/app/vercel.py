"""Vercel entrypoint for the repository-root deployment.

Vercel imports this file from the repository root. Add the backend directory to
Python's module search path before loading the application, whose package is
named ``app`` in local, container, and migration environments.
"""

from __future__ import annotations

import sys
from pathlib import Path

backend_directory = str(Path(__file__).resolve().parents[1])
if backend_directory not in sys.path:
    sys.path.insert(0, backend_directory)

from app.main import app  # noqa: E402,F401
