from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest

from app.services import vehicle_review_rollout
from vehicle_review_rollout import configured_url


def vehicle():
    return SimpleNamespace(id=uuid.uuid4(), status='approved', review_reason='Original harmless review')


@pytest.mark.asyncio
async def test_backfill_refuses_any_bookings_before_mutating_eligibility():
    db = SimpleNamespace(execute=AsyncMock(), scalar=AsyncMock(return_value=1), add=Mock())
    with pytest.raises(RuntimeError, match='bookings exist'):
        await vehicle_review_rollout.apply_backfill(db)
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_backfill_preserves_records_and_audit_and_is_repeatable():
    item = vehicle()
    db = SimpleNamespace(execute=AsyncMock(), scalar=AsyncMock(return_value=0), scalars=AsyncMock(side_effect=[[item],[]]), add=Mock())
    assert await vehicle_review_rollout.apply_backfill(db) == {'bookings':0,'changed':1}
    assert item.status == 'pending' and item.review_reason.startswith('Original harmless review')
    event = db.add.call_args.args[0]
    assert event.action == 'vehicle.document_review_required' and event.before['status'] == 'approved'
    db.scalars = AsyncMock(side_effect=[[],[]])
    assert await vehicle_review_rollout.apply_backfill(db) == {'bookings':0,'changed':0}
    assert db.add.call_count == 1


def test_qualifying_files_preserve_approval_and_unaccepted_files_do_not():
    item = vehicle()
    files = [SimpleNamespace(vehicle_id=item.id, document_type=kind, status='accepted', storage_version_id='fictional-v1', expires_on=date.today()+timedelta(days=30)) for kind in ['rc','insurance','fitness','pollution','permit']]
    assert vehicle_review_rollout.candidates([item], files) == []
    files[0].status = 'uploaded'
    assert vehicle_review_rollout.candidates([item], files) == [item]


def test_production_rollout_has_no_application_url_fallback_or_apply(monkeypatch):
    monkeypatch.delenv('VEHICLE_REVIEW_AUDIT_DATABASE_URL', raising=False)
    monkeypatch.setenv('DATABASE_URL','postgresql://fictional:unused@production.invalid/production')
    with pytest.raises(RuntimeError, match='no fallback'):
        configured_url('production','production.invalid','production',False)
    with pytest.raises(RuntimeError, match='apply is disabled'):
        configured_url('production','production.invalid','production',True)


@pytest.mark.parametrize('query', ['host=other.invalid', 'dbname=other', 'service=other'])
def test_audit_target_cannot_be_overridden_by_driver_query(monkeypatch, query):
    monkeypatch.setenv('VEHICLE_REVIEW_AUDIT_DATABASE_URL', 'postgresql://fictional:unused@production.invalid/production?' + query)
    with pytest.raises(RuntimeError, match='connection option'):
        configured_url('production', 'production.invalid', 'production', False)


def test_remote_audit_requires_explicit_tls(monkeypatch):
    base = 'postgresql://fictional:unused@production.invalid/production'
    monkeypatch.setenv('VEHICLE_REVIEW_AUDIT_DATABASE_URL', base)
    with pytest.raises(RuntimeError, match='TLS'):
        configured_url('production', 'production.invalid', 'production', False)
    monkeypatch.setenv('VEHICLE_REVIEW_AUDIT_DATABASE_URL', base+'?sslmode=require')
    assert configured_url('production', 'production.invalid', 'production', False) == base+'?sslmode=require'
