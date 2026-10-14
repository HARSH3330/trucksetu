"""Read-only production inspection; LOCAL guarded apply only.

Production apply is intentionally not enabled. Reuse the reviewed service only
after explicit release authorization and a verified impact/backup review.
"""
import argparse
import asyncio
import json
import os
import selectors
import sys
from urllib.parse import parse_qsl, unquote, urlparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.services.vehicle_review_rollout import apply_backfill, inspect_rollout
from e2e_database import safe_database_url, validate_connection_options


def configured_url(environment: str, expected_host: str | None, expected_database: str | None, apply: bool) -> str:
    if environment == 'local':
        return safe_database_url()
    if apply:
        raise RuntimeError('Production/staging apply is disabled; separate impact and release authorization required')
    raw = os.getenv('VEHICLE_REVIEW_AUDIT_DATABASE_URL', '').strip()
    parsed = urlparse(raw.replace('postgresql+psycopg://', 'postgresql://', 1))
    if not raw or parsed.scheme not in {'postgresql','postgres'} or not expected_host or not expected_database:
        raise RuntimeError('Explicit audit URL, expected host and database are required; no fallback')
    if parsed.hostname != expected_host or unquote(parsed.path.lstrip('/')) != expected_database:
        raise RuntimeError('Audit database target does not match the explicitly expected target')
    validate_connection_options(parsed)
    tls_modes = [value for key, value in parse_qsl(parsed.query) if key == 'sslmode']
    if not tls_modes or any(value not in {'require','verify-ca','verify-full'} for value in tls_modes):
        raise RuntimeError('Remote audit requires explicit TLS')
    return raw


async def run(args) -> dict:
    raw = configured_url(args.environment, args.expected_host, args.expected_database, args.apply)
    engine = create_async_engine(raw.replace('postgresql://', 'postgresql+psycopg://', 1).replace('postgres://', 'postgresql+psycopg://', 1))
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            if not args.apply:
                await db.execute(text('SET TRANSACTION READ ONLY'))
                report = await inspect_rollout(db)
                await db.rollback()
            else:
                try:
                    report = await apply_backfill(db)
                    await db.commit()
                except Exception:
                    await db.rollback()
                    raise
            return {'environment':args.environment, 'mode':'apply' if args.apply else 'dry_run', **report}
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', choices=['local','staging','production'], required=True)
    parser.add_argument('--expected-host')
    parser.add_argument('--expected-database')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        if sys.platform == 'win32':
            report = asyncio.run(run(args), loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
        else:
            report = asyncio.run(run(args))
    except Exception:
        # Never echo URLs/passwords, SQL, identifiers or driver exceptions.
        print('Rollout inspection/apply refused or failed. Verify explicit target, permissions, schema and zero-booking prerequisite privately.', file=sys.stderr)
        return 1
    print(json.dumps(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
