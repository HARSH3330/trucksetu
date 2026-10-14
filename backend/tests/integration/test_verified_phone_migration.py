"""Migration behaviour in rollback-only schemas on the dedicated local database."""
import asyncio
import importlib.util
import selectors
import sys
import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import DBAPIError,IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from e2e_database import safe_database_url


@pytest.mark.parametrize('scenario',['valid','conflicting','invalid'])
def test_verified_phone_migration_normalizes_or_refuses_without_losing_data(monkeypatch,scenario):
    async def exercise():
        raw=safe_database_url()
        engine=create_async_engine(raw.replace('postgresql://','postgresql+psycopg://',1).replace('postgres://','postgresql+psycopg://',1))
        try:
            async with engine.connect() as connection:
                outer=await connection.begin()
                try:
                    def run(sync):
                        schema='phone_migration_'+uuid.uuid4().hex
                        sync.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
                        sync.execute(sa.text(f'SET LOCAL search_path TO "{schema}", pg_catalog'))
                        sync.execute(sa.text('CREATE TABLE users (id integer PRIMARY KEY, mobile varchar(20), mobile_verified boolean NOT NULL, CONSTRAINT users_mobile_key UNIQUE(mobile))'))
                        rows=[{'id':1,'mobile':'9999999999','verified':True},{'id':2,'mobile':'+919999999999','verified':scenario=='conflicting'}]
                        if scenario=='invalid':rows[0]['mobile']=None
                        sync.execute(sa.text('INSERT INTO users(id,mobile,mobile_verified) VALUES (:id,:mobile,:verified)'),rows)
                        original=sync.execute(sa.text('SELECT id,mobile,mobile_verified FROM users ORDER BY id')).all()
                        path=Path(__file__).resolve().parents[2]/'migrations/versions/20261014_22_verified_phone_ownership.py'
                        spec=importlib.util.spec_from_file_location('phone_ownership_migration',path)
                        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                        monkeypatch.setattr(module,'op',Operations(MigrationContext.configure(sync)))
                        if scenario!='valid':
                            expected='conflicting verified claims' if scenario=='conflicting' else 'invalid verified phone'
                            with pytest.raises(DBAPIError,match=expected):
                                with sync.begin_nested():module.upgrade()
                            assert sync.execute(sa.text('SELECT id,mobile,mobile_verified FROM users ORDER BY id')).all()==original
                            return
                        module.upgrade()
                        assert sync.execute(sa.text('SELECT mobile,mobile_verified FROM users ORDER BY id')).all()==[('+919999999999',True),('+919999999999',False)]
                        with pytest.raises(IntegrityError):
                            with sync.begin_nested():sync.execute(sa.text('UPDATE users SET mobile_verified=true WHERE id=2'))
                        with pytest.raises(DBAPIError,match='duplicate claims'):
                            with sync.begin_nested():module.downgrade()
                        assert sync.execute(sa.text('SELECT count(*) FROM users')).scalar_one()==2
                    await connection.run_sync(run)
                finally:await outer.rollback() # schema and every row/DDL are test-local and rollback-only
        finally:await engine.dispose()
    if sys.platform=='win32':asyncio.run(exercise(),loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:asyncio.run(exercise())
