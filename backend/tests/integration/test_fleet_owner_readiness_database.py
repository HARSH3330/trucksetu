"""Isolated migrated PostgreSQL; fictional fleet-owner records only, no payment, SMS or storage call."""
import uuid
from datetime import date, timedelta

import httpx
from sqlalchemy import select

from app.api.demands import get_connection_gateway
from app.core import database
from app.main import app
from app.models import CarrierVehicle, DriverProfile, ProviderProfile, User, VehicleDocument
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import LocalGateway, actors_and_payload, configure, event, prepare_selection

STOPS=[{'address':'PRIVATE stop lane 1, Okhla','activity':'drop','instructions':None},
       {'address':'PRIVATE stop lane 2, Saket','activity':'drop','instructions':None}]


def test_fleet_owner_sees_driver_readiness_trip_stops_and_files_waiting_for_review(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,driver_id=await actors_and_payload(factory)
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,order=await prepare_selection(client,headers,{**payload,'stops':STOPS},bid)
                    assert (await event(client,order,'valid')).status_code==200
                    async with factory() as db:
                        driver=await db.get(DriverProfile,driver_id)
                        provider_id=driver.provider_id
                        vehicle_id=selected['vehicle_id']
                        for old in await db.scalars(select(VehicleDocument).where(VehicleDocument.vehicle_id==uuid.UUID(vehicle_id),VehicleDocument.document_type=='fitness')):
                            old.status='rejected'
                        db.add(VehicleDocument(vehicle_id=uuid.UUID(vehicle_id),document_type='fitness',storage_key='local/'+uuid.uuid4().hex,storage_version_id='v1',original_filename='fitness.pdf',content_type='application/pdf',size_bytes=10,expires_on=date.today()+timedelta(days=200),status='uploaded'))
                        await db.commit()

                    drivers=(await client.get(f'/api/v1/providers/{provider_id}/drivers',headers=headers[2])).json()
                    assert next(x for x in drivers if x['id']==str(driver_id))['contact_ready'] is True

                    booking=next(x for x in (await client.get('/api/v1/bookings',headers=headers[2])).json() if x['id']==selected['booking_id'])
                    assert booking['stop_count']==2

                    vehicle=next(x for x in (await client.get('/api/v1/carrier-vehicles',headers=headers[2])).json() if x['id']==vehicle_id)
                    assert vehicle['awaiting_review_documents']==['fitness']
                    assert 'fitness' in vehicle['missing_accepted_documents']

                    async with factory() as db:
                        account=await db.get(User,driver.user_id)
                        account.mobile_verified=False
                        account.email_verified=False
                        await db.commit()
                    drivers=(await client.get(f'/api/v1/providers/{provider_id}/drivers',headers=headers[2])).json()
                    assert next(x for x in drivers if x['id']==str(driver_id))['contact_ready'] is False
                    async with factory() as db:
                        assert await db.scalar(select(ProviderProfile.id).where(ProviderProfile.id==provider_id))
                        assert await db.get(CarrierVehicle,uuid.UUID(vehicle_id))
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())
