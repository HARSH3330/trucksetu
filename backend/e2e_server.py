import argparse
import asyncio
import os
import selectors
import sys

import uvicorn


async def serve(port: int) -> None:
    from e2e_database import safe_database_url
    # Bind the served app before importing settings: never inherit application
    # or Neon credentials, even when this launcher is run manually.
    raw=safe_database_url()
    os.environ['DATABASE_URL']=raw
    os.environ['MIGRATION_DATABASE_URL']=raw
    config = uvicorn.Config(
        "e2e_support:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        workers=1,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    if (
        os.environ.get("APP_ENV", "").lower() != "test"
        or os.environ.get("TRANSIVOX_E2E", "").lower() != "true"
    ):
        raise SystemExit("This launcher requires explicit E2E test mode.")

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if sys.platform == "win32":
        asyncio.run(
            serve(args.port),
            loop_factory=lambda: asyncio.SelectorEventLoop(
                selectors.SelectSelector()
            ),
        )
    else:
        asyncio.run(serve(args.port))
