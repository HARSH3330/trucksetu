from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.api.matching import HARD_SAFETY_REJECTIONS
from app.api.vehicles import vehicle_is_document_eligible
from app.schemas import CarrierVehicleCreate, SharedMatchMetrics
from app.services.capacity import restore_capacity


def vehicle_input(**changes: object) -> CarrierVehicleCreate:
    future = date.today() + timedelta(days=365)
    values: dict[str, object] = {
        "provider_id": "cb1b5ea6-fb65-4078-8619-987a3902eaf2",
        "vehicle_category_id": "81f1bb64-ec48-4a3d-b0f8-590e9fe30e2b",
        "registration_number": "DL01AB1234",
        "body_type": "closed",
        "maximum_payload_tonnes": Decimal("1.5"),
        "internal_length_m": Decimal("3"),
        "internal_width_m": Decimal("1.5"),
        "internal_height_m": Decimal("1.5"),
        "permit_territories": ["Delhi", "Gurugram"],
        "service_areas": ["Delhi NCR"],
        "rc_expires_on": future,
        "insurance_expires_on": future,
        "fitness_expires_on": future,
        "pollution_expires_on": future,
        "permit_expires_on": future,
    }
    values.update(changes)
    return CarrierVehicleCreate(**values)


def test_vehicle_internal_volume_is_computed() -> None:
    assert vehicle_input().maximum_volume_m3 == Decimal("6.750")


def test_declared_vehicle_volume_cannot_exceed_body() -> None:
    with pytest.raises(ValidationError, match="internal body volume"):
        vehicle_input(maximum_volume_m3=Decimal("7"))


def test_vehicle_documents_must_cover_trip_date() -> None:
    future = date.today() + timedelta(days=30)
    item = SimpleNamespace(status="approved", rc_expires_on=future, insurance_expires_on=future, fitness_expires_on=future, pollution_expires_on=future, permit_expires_on=future)
    assert vehicle_is_document_eligible(item, future) is True
    item.insurance_expires_on = date.today() - timedelta(days=1)
    assert vehicle_is_document_eligible(item, date.today()) is False


def test_capacity_restoration_is_idempotently_capped() -> None:
    route = SimpleNamespace(total_capacity_tonnes=Decimal("1"), remaining_capacity_tonnes=Decimal("0.8"), total_volume_m3=Decimal("4"), remaining_volume_m3=Decimal("3.7"), status="full")
    reservation = SimpleNamespace(weight_tonnes=Decimal("0.4"), volume_m3=Decimal("0.8"))
    restore_capacity(route, reservation)
    assert route.remaining_capacity_tonnes == Decimal("1")
    assert route.remaining_volume_m3 == Decimal("4")
    assert route.status == "active"


def test_safety_rejections_cannot_be_commercial_overrides() -> None:
    assert "documents_expired_or_expiring_before_trip" in HARD_SAFETY_REJECTIONS
    assert "insufficient_safe_volume" in HARD_SAFETY_REJECTIONS
    assert "minimum_customer_saving_not_met" not in HARD_SAFETY_REJECTIONS


def test_route_metrics_have_bounded_manual_inputs() -> None:
    with pytest.raises(ValidationError):
        SharedMatchMetrics(added_distance_km=Decimal("501"), added_time_minutes=10, pickup_window_feasible=True, delivery_deadline_feasible=True, existing_commitments_feasible=True, route_fit_percent=Decimal("80"), dedicated_comparable_price=Decimal("2000"), proposed_shared_price=Decimal("1500"))
