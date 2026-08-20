"""Package compatibility for repository-root ASGI hosts such as Vercel."""

from importlib import import_module
import sys

# The backend normally runs with ``backend`` as its working directory, where
# ``app`` is a top-level package. Vercel imports ``backend.app.main`` from the
# repository root, so expose the same package name before that module loads.
sys.modules.setdefault("app", import_module(".app", __name__))
