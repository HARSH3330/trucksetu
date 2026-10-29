from types import SimpleNamespace
from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.services.demand_schemas import DemandLocation
from app.services.demand_marketplace import demand_view

def test_optional_location_bounds_and_no_nan():
    assert DemandLocation(lat=0,lng=0).model_dump()=={'lat':0.0,'lng':0.0}
    for value in [{'lat':91,'lng':1},{'lat':1,'lng':181},{'lat':float('nan'),'lng':0},{'lat':0},{'lat':True,'lng':0}]:
        with pytest.raises(ValidationError):DemandLocation.model_validate(value)

def test_discovery_hides_coordinates_and_owner_edit_restores_them():
    import uuid
    from datetime import datetime,UTC
    cargo=SimpleNamespace(**{k:None for k in ['category','description','weight_tonnes','length_m','width_m','height_m','packages','packaging_type','dimensions_are_per_package','loading_assistance','unloading_assistance','fragile','volume_m3']})
    item=SimpleNamespace(id=uuid.uuid4(),public_id='synthetic',revision=1,status='published',pickup_city='Delhi',destination_city='Noida',pickup_date=datetime.now(UTC).date(),earliest_pickup_at=None,latest_pickup_at=None,delivery_deadline_at=None,flexible_schedule=False,budget_amount=Decimal('1'),cargo=cargo,pickup_address='Private pickup',destination_address='Private delivery',special_instructions=None,pickup_location={'lat':28.6,'lng':77.2},destination_location=None)
    public=demand_view(item);assert 'pickup_location' not in public and 'destination_location' not in public
    assert demand_view(item,True)['pickup_location']==item.pickup_location
