"""Vehicle editing against real PostgreSQL (guarded, migrated, unique schema)."""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.api.vehicles import update_vehicle
from app.models import AuditLog, CarrierVehicle, ProviderProfile, User, VehicleCategory
from app.schemas import CarrierVehicleUpdate
from _local_release_db import migrated_schema, run_local


def test_vehicle_edit_persists_review_reset_audit_and_conceals_other_providers():
    async def exercise():
        async with migrated_schema() as (_, factory):
            soon = date.today() + timedelta(days=120)
            async with factory() as db:
                owner = User(email=f"owner-{uuid.uuid4().hex}@example.com", full_name="Fictional Owner", password_hash="x")
                other = User(email=f"other-{uuid.uuid4().hex}@example.com", full_name="Fictional Other", password_hash="x")
                category = VehicleCategory(name=f"Fictional {uuid.uuid4().hex[:6]}", body_type="closed", min_capacity_tonnes=1, max_capacity_tonnes=Decimal("10"))
                db.add_all([owner, other, category]); await db.flush()
                provider = ProviderProfile(user_id=owner.id, display_name="Fictional Provider")
                db.add(provider); await db.flush()
                vehicle = CarrierVehicle(provider_id=provider.id, vehicle_category_id=category.id, registration_number="KA01AB1234", body_type="closed",
                    maximum_payload_tonnes=Decimal("9"), internal_length_m=Decimal("6"), internal_width_m=Decimal("2.4"), internal_height_m=Decimal("2.4"),
                    maximum_volume_m3=Decimal("34.56"), permit_territories=["KA"], service_areas=["Bengaluru"], rc_expires_on=soon,
                    insurance_expires_on=soon, fitness_expires_on=soon, pollution_expires_on=soon, permit_expires_on=soon, status="approved",
                    reviewed_by=owner.id, review_reason="fictional approval")
                db.add(vehicle); await db.commit()
                vehicle_id, owner_id, other_id = vehicle.id, owner.id, other.id
            owner_actor = SimpleNamespace(id=owner_id, roles=[SimpleNamespace(role="provider")])
            other_actor = SimpleNamespace(id=other_id, roles=[SimpleNamespace(role="provider")])
            async with factory() as db:
                with pytest.raises(HTTPException) as denied:
                    await update_vehicle(vehicle_id, CarrierVehicleUpdate(service_areas=["Mysuru"]), db, other_actor)
                assert denied.value.status_code == 404
            async with factory() as db:
                result = await update_vehicle(vehicle_id, CarrierVehicleUpdate(service_areas=["Mysuru", "Bengaluru"]), db, owner_actor)
                assert result["status"] == "pending"
            async with factory() as db:
                stored = await db.get(CarrierVehicle, vehicle_id)
                assert stored.status == "pending" and stored.reviewed_by is None and stored.service_areas == ["Mysuru", "Bengaluru"]
                audits = list(await db.scalars(select(AuditLog).where(AuditLog.entity_id == vehicle_id, AuditLog.action == "vehicle.updated")))
                assert len(audits) == 1 and audits[0].after["changed_fields"] == ["service_areas"]
    run_local(exercise())
