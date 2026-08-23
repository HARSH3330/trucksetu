from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain import VehicleOption, recommend_vehicle
from app.schemas import CargoCreate, TransportRequestCreate


def test_hazardous_cargo_requires_instructions() -> None:
    with pytest.raises(ValidationError):
        TransportRequestCreate(
            customer_id="b9c443c2-9dfa-4e29-8da7-a091a0929317",
            pickup_address="Rohini, Delhi",
            pickup_city="Delhi",
            destination_address="Jaipur, Rajasthan",
            destination_city="Jaipur",
            booking_mode="FULL_VEHICLE",
            schedule_mode="NOW",
            pickup_date="2026-08-22",
            cargo=CargoCreate(category="Chemicals", description="Industrial solvent", weight_tonnes=Decimal("3"), length_m=1, width_m=1, height_m=1, hazardous=True),
        )


def test_inactive_vehicle_is_never_recommended() -> None:
    catalogue = [
        VehicleOption("inactive", "Inactive large truck", Decimal("0"), Decimal("20"), "closed", False),
        VehicleOption("active", "Safe active truck", Decimal("0"), Decimal("9"), "closed", True),
    ]
    result = recommend_vehicle(Decimal("7"), True, catalogue)
    assert result is not None and result.id == "active"
