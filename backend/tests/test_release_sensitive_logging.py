import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import OperationsMiddleware


def test_unhandled_errors_log_correlation_not_sensitive_exception_contents(caplog):
    app=FastAPI()
    app.add_middleware(OperationsMiddleware)
    @app.get('/fictional-failure')
    async def fail():
        raise RuntimeError('FICTIONAL_SECRET_MUST_NOT_APPEAR')
    with caplog.at_level(logging.ERROR,logger='transivox.http'):
        with TestClient(app,raise_server_exceptions=False) as client:
            assert client.get('/fictional-failure').status_code==500
    records=[record for record in caplog.records if record.name=='transivox.http']
    assert records
    assert all(record.exc_info is None for record in records)
    assert 'FICTIONAL_SECRET_MUST_NOT_APPEAR' not in caplog.text
    assert 'request_id' in caplog.text and 'RuntimeError' in caplog.text
