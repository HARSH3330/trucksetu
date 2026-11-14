"""Unique, migrated schemas on ONLY the explicitly configured local E2E DB."""
import asyncio
import os
import re
import selectors
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine

from e2e_database import safe_database_url


def run_local(coroutine):
    if sys.platform=='win32':return asyncio.run(coroutine,loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    return asyncio.run(coroutine)


@asynccontextmanager
async def migrated_schema(before_23=None):
    raw=safe_database_url()  # MUST happen before any connection; no DB fallback.
    if os.getenv('APP_ENV')!='test' or os.getenv('E2E_REAL_AWS','').lower()!='false':
        raise RuntimeError('Release regressions require APP_ENV=test and E2E_REAL_AWS=false')
    schema='tx_e2e_'+uuid.uuid4().hex
    engine=create_async_engine(raw.replace('postgresql://','postgresql+psycopg://',1).replace('postgres://','postgresql+psycopg://',1),connect_args={'options':f'-c search_path={schema},pg_catalog -c statement_timeout=15000 -c lock_timeout=10000'})
    created=False
    try:
        async with engine.begin() as db:
            await db.execute(text(f'CREATE SCHEMA "{schema}"'))
        created=True
        async with engine.begin() as db:
            def migrate(sync):
                config=Config()
                config.set_main_option('script_location',str(Path(__file__).resolve().parents[2]/'migrations'))
                revisions=reversed(list(ScriptDirectory.from_config(config).walk_revisions()))
                with Operations.context(MigrationContext.configure(sync)):
                    for revision in revisions:
                        if revision.revision=='20261014_23' and before_23:before_23(sync)
                        revision.module.upgrade()
            await db.run_sync(migrate)
        yield engine,async_sessionmaker(engine,expire_on_commit=False)
    finally:
        if created:
            # Only this generated schema, only after safe_database_url passed.
            assert re.fullmatch(r'tx_e2e_[0-9a-f]{32}',schema)
            async with engine.begin() as db:
                await db.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await engine.dispose()
