from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.vehicles import update_vehicle
from app.models import ProviderProfile, VehicleCategory
from app.schemas import CarrierVehicleUpdate


def vehicle(status="approved", **overrides):
    today = date.today() + timedelta(days=90)
    values = dict(
        id=uuid.uuid4(), provider_id=uuid.uuid4(), vehicle_category_id=uuid.uuid4(), registration_number="KA01AB1234",
        body_type="closed", maximum_payload_tonnes=Decimal("9.000"), internal_length_m=Decimal("6.000"),
        internal_width_m=Decimal("2.400"), internal_height_m=Decimal("2.400"), maximum_volume_m3=Decimal("34.560"),
        permit_territories=["KA"], service_areas=["Bengaluru"], rc_expires_on=today, insurance_expires_on=today,
        fitness_expires_on=today, pollution_expires_on=today, permit_expires_on=today, status=status,
        reviewed_by=uuid.uuid4(), reviewed_at=date.today(), review_reason="approved earlier",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def fake_db(item, owner_id, *, in_use_trip=None, in_use_route=None, category_max="10.000", category_active=True):
    provider = SimpleNamespace(id=item.provider_id, user_id=owner_id)
    category = SimpleNamespace(id=item.vehicle_category_id, active=category_active, max_capacity_tonnes=Decimal(category_max))
    async def get(model, ident):
        return provider if model is ProviderProfile else category if model is VehicleCategory else None
    db = SimpleNamespace(scalar=AsyncMock(side_effect=[item, in_use_trip, in_use_route]), get=AsyncMock(side_effect=get),
                         add=lambda obj: db.added.append(obj), commit=AsyncMock(), added=[])
    return db


def actor(user_id, role="provider"):
    return SimpleNamespace(id=user_id, roles=[SimpleNamespace(role=role)])


@pytest.mark.asyncio
async def test_safety_edit_returns_an_approved_vehicle_to_review_and_audits_changed_fields():
    owner = uuid.uuid4(); item = vehicle(); db = fake_db(item, owner)
    result = await update_vehicle(item.id, CarrierVehicleUpdate(maximum_payload_tonnes=Decimal("8.500")), db, actor(owner))
    assert result["status"] == "pending" and item.reviewed_by is None and item.review_reason is None
    assert item.maximum_payload_tonnes == Decimal("8.500")
    audit = db.added[0]
    assert audit.action == "vehicle.updated" and audit.after["changed_fields"] == ["maximum_payload_tonnes"]
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_unchanged_values_do_not_reset_review_or_write_audit():
    owner = uuid.uuid4(); item = vehicle(); db = fake_db(item, owner)
    result = await update_vehicle(item.id, CarrierVehicleUpdate(body_type="closed", service_areas=["Bengaluru"]), db, actor(owner))
    assert result["status"] == "approved" and db.added == []
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_other_provider_receives_not_found_not_forbidden():
    item = vehicle(); db = fake_db(item, uuid.uuid4())
    with pytest.raises(HTTPException) as failure:
        await update_vehicle(item.id, CarrierVehicleUpdate(body_type="open"), db, actor(uuid.uuid4()))
    assert failure.value.status_code == 404 and item.body_type == "closed"


@pytest.mark.asyncio
@pytest.mark.parametrize("kwargs", [{"in_use_trip": uuid.uuid4()}, {"in_use_route": uuid.uuid4()}])
async def test_vehicle_with_active_trip_or_published_route_cannot_change(kwargs):
    owner = uuid.uuid4(); item = vehicle(); db = fake_db(item, owner, **kwargs)
    with pytest.raises(HTTPException) as failure:
        await update_vehicle(item.id, CarrierVehicleUpdate(maximum_payload_tonnes=Decimal("5")), db, actor(owner))
    assert failure.value.status_code == 409 and item.status == "approved"


@pytest.mark.asyncio
async def test_suspended_vehicle_cannot_be_self_reinstated_by_editing():
    owner = uuid.uuid4(); item = vehicle(status="suspended"); db = fake_db(item, owner)
    with pytest.raises(HTTPException) as failure:
        await update_vehicle(item.id, CarrierVehicleUpdate(body_type="open"), db, actor(owner))
    assert failure.value.status_code == 409 and item.status == "suspended"


@pytest.mark.asyncio
async def test_payload_above_category_limit_and_inactive_category_are_rejected():
    owner = uuid.uuid4(); item = vehicle()
    with pytest.raises(HTTPException) as failure:
        await update_vehicle(item.id, CarrierVehicleUpdate(maximum_payload_tonnes=Decimal("10.5")), fake_db(item, owner), actor(owner))
    assert failure.value.status_code == 422
    with pytest.raises(HTTPException) as failure:
        await update_vehicle(item.id, CarrierVehicleUpdate(body_type="open"), fake_db(item, owner, category_active=False), actor(owner))
    assert failure.value.status_code == 422


@pytest.mark.asyncio
async def test_shrinking_body_clamps_volume_and_oversized_volume_is_rejected():
    owner = uuid.uuid4(); item = vehicle(); db = fake_db(item, owner)
    await update_vehicle(item.id, CarrierVehicleUpdate(internal_length_m=Decimal("3.000")), db, actor(owner))
    assert item.maximum_volume_m3 == Decimal("17.280")
    item2 = vehicle()
    with pytest.raises(HTTPException) as failure:
        await update_vehicle(item2.id, CarrierVehicleUpdate(maximum_volume_m3=Decimal("40")), fake_db(item2, owner), actor(owner))
    assert failure.value.status_code == 422 and item2.maximum_volume_m3 == Decimal("34.560")


def test_identity_and_expiry_fields_are_not_editable_and_empty_patch_is_rejected():
    for forbidden in ({"registration_number": "KA01ZZ9999"}, {"provider_id": str(uuid.uuid4())}, {"rc_expires_on": "2030-01-01"}, {"status": "approved"}):
        with pytest.raises(ValidationError):
            CarrierVehicleUpdate(**forbidden)
    with pytest.raises(ValidationError):
        CarrierVehicleUpdate()
