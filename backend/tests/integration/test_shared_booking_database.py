"""Actual HTTP/auth/SQL transactions, real migrations, no AWS or payment calls.

Each scenario owns a fresh schema on transivox_e2e. Approved document rows below
are fictional local fixtures, not evidence of actual scanning/identity review.
"""
import asyncio
import uuid
from datetime import UTC,datetime,timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func,select,update

from app.api.terms import TERMS_HASH,TERMS_VERSION
from app.core import database
from app.core.security import create_access_token
from app.main import app
from app.models import AvailableRoute,Booking,BookingAllocation,Cancellation,CapacityReservation,CarrierVehicle,DriverProfile,Payment,ProviderProfile,Quote,QuoteVersion,TermsAcceptance,TransportRequest,User,UserRole,VehicleCategory,VehicleDocument,CargoItem
from app.services.capacity import release_expired_capacity_holds
from _local_release_db import migrated_schema,run_local


async def seed(factory):
    now=datetime.now(UTC);expires=(now+timedelta(days=10)).date();marker=uuid.uuid4().hex[:12]
    actors=[User(id=uuid.uuid4(),full_name='Fictional local actor',email=f'{role}-{index}-{marker}@example.com',password_hash='unused',roles=[UserRole(role=role)]) for index,role in enumerate(['customer','customer','provider','driver','admin'])]
    a,b,owner,driver_user,admin=actors
    provider=ProviderProfile(id=uuid.uuid4(),user_id=owner.id,display_name='NOT REAL TRANSPORT',provider_type='owner',kyc_status='verified')
    category=VehicleCategory(id=uuid.uuid4(),name='Fictional '+marker,body_type='closed',min_capacity_tonnes=Decimal('0.1'),max_capacity_tonnes=Decimal('5'))
    vehicle=CarrierVehicle(id=uuid.uuid4(),provider_id=provider.id,vehicle_category_id=category.id,registration_number='TEST-'+marker,body_type='closed',maximum_payload_tonnes=5,internal_length_m=3,internal_width_m=2,internal_height_m=2,maximum_volume_m3=12,permit_territories=['Delhi','Noida'],rc_expires_on=expires,insurance_expires_on=expires,fitness_expires_on=expires,pollution_expires_on=expires,permit_expires_on=expires,status='approved')
    driver=DriverProfile(id=uuid.uuid4(),provider_id=provider.id,user_id=driver_user.id,full_name='NOT REAL DRIVER',masked_mobile='NOT REAL',licence_number='TEST-'+marker,licence_expires_on=expires,kyc_status='verified')
    route=AvailableRoute(id=uuid.uuid4(),provider_id=provider.id,vehicle_category_id=category.id,carrier_vehicle_id=vehicle.id,driver_id=driver.id,vehicle_registration=vehicle.registration_number,origin_address='Fictional Delhi depot',origin_city='Delhi',destination_address='Fictional Noida depot',destination_city='Noida',ordered_route_cities=['Delhi','Noida'],departure_at=now+timedelta(days=1),departure_window_end=now+timedelta(days=1,hours=1),expected_arrival_at=now+timedelta(days=1,hours=3),total_capacity_tonnes=Decimal('1.1'),remaining_capacity_tonnes=Decimal('1.1'),total_volume_m3=Decimal('1.1'),remaining_volume_m3=Decimal('1.1'),minimum_booking_tonnes=Decimal('0.1'),allowed_cargo_types=['Furniture'],price_amount=123,price_basis='per_tonne',maximum_added_time_minutes=60,maximum_deviation_km=10)
    requests=[];quotes=[]
    async with factory() as db:
        db.add_all(actors);await db.flush()
        db.add_all([provider,category,ProviderProfile(user_id=driver_user.id,display_name='NOT REAL DRIVER',provider_type='driver',kyc_status='verified')]);await db.flush()
        db.add_all([vehicle,driver]);await db.flush();db.add(route);await db.flush()
        for kind in ['rc','insurance','fitness','pollution','permit']:
            db.add(VehicleDocument(vehicle_id=vehicle.id,document_type=kind,storage_key=f'kyc/test/{marker}/{kind}',storage_version_id='fictional-local-version',original_filename='NOT-A-REAL-ID.pdf',content_type='application/pdf',size_bytes=100,expires_on=expires,status='accepted'))
        for customer in [a,b]:
            shipment=TransportRequest(id=uuid.uuid4(),customer_id=customer.id,available_route_id=route.id,public_id='TEST-'+uuid.uuid4().hex[:12],status='published',booking_mode='SHARED_CAPACITY',vehicle_category_id=category.id,pickup_address=route.origin_address,pickup_city='Delhi',destination_address=route.destination_address,destination_city='Noida',pickup_date=route.departure_at.date(),earliest_pickup_at=route.departure_at,latest_pickup_at=route.departure_window_end,delivery_deadline_at=now+timedelta(days=1,hours=5),maximum_added_time_minutes=60,stops=[],cargo=CargoItem(category='Furniture',description='NOT A REAL SHIPMENT',weight_tonnes=1,volume_m3=1))
            db.add(shipment);db.add(TermsAcceptance(user_id=customer.id,version=TERMS_VERSION,content_sha256=TERMS_HASH));await db.flush()
            quote=Quote(id=uuid.uuid4(),request_id=shipment.id,available_route_id=route.id,provider_id=provider.id,vehicle_category_id=category.id,service_mode='SHARED_CAPACITY',final_price=750,currency='INR',vehicles_offered=1,estimated_pickup=route.departure_at,estimated_delivery=route.expected_arrival_at,expires_at=now+timedelta(hours=1),price_breakdown=[{'label':'Transport','amount':'750'}],inclusions='Transport',exclusions='None',versions=[QuoteVersion(version=1,final_price=750,vehicles_offered=1,snapshot={'fixture':True})])
            db.add(quote);requests.append(shipment.id);quotes.append(quote.id)
        await db.commit()
    return actors,route.id,requests,quotes


@pytest.mark.parametrize('scenario',['duplicate','concurrent_accept','concurrent_hold','hold_accept_cancel','expired_quote','superseded_quote','unauthorized','expiry_accept_race','cancel_expiry_race'])
def test_shared_quote_capacity_transactions(monkeypatch,scenario):
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            actors,route_id,requests,quotes=await seed(factory)
            headers=[{'Authorization':'Bearer '+create_access_token({'sub':str(actor.id),'sv':0})} for actor in actors]
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                matches=[]
                for request_id in requests:
                    response=await client.post(f'/api/v1/admin/requests/{request_id}/routes/{route_id}/evaluate-shared-match',headers=headers[4],json={'added_distance_km':'0','added_time_minutes':0,'pickup_window_feasible':True,'delivery_deadline_feasible':True,'existing_commitments_feasible':True,'route_fit_percent':'100','dedicated_comparable_price':'1000','proposed_shared_price':'750'})
                    assert response.status_code==201, f'Match HTTP {response.status_code}'
                    assert response.json()['eligible'] is True
                    matches.append(response.json()['id'])
                async def accept(index=0,key=None,hold=None):
                    return await client.post(f'/api/v1/quotes/{quotes[index]}/accept-shared',headers=headers[index],json={'expected_version':1,'idempotency_key':key or f'fictional-accept-{index}','accept_final_price':True,'capacity_reservation_id':hold})
                async def reserve(index=0):
                    return await client.post(f'/api/v1/available-routes/{route_id}/reservations',headers=headers[index],json={'match_evaluation_id':matches[index],'cargo_type':'Furniture','weight_tonnes':'1','volume_m3':'1','idempotency_key':f'fictional-hold-{index}'})
                async def expire():
                    async with factory() as db:
                        await release_expired_capacity_holds(db);await db.commit()
                async def cancel(booking):
                    return await client.post(f'/api/v1/bookings/{booking}/cancel',headers=headers[0],json={'reason_code':'fictional-test'})
                expected_bookings=1;expected_remaining=Decimal('0.1')
                if scenario=='duplicate':
                    first,second=await asyncio.wait_for(asyncio.gather(accept(),accept()),20)
                    assert first.status_code==second.status_code==201
                    assert first.json()['id']==second.json()['id']
                elif scenario=='concurrent_accept':
                    responses=await asyncio.wait_for(asyncio.gather(accept(0),accept(1)),20)
                    assert sorted(item.status_code for item in responses)==[201,409]
                elif scenario=='concurrent_hold':
                    responses=await asyncio.wait_for(asyncio.gather(reserve(0),reserve(1)),20)
                    assert sorted(item.status_code for item in responses)==[201,409]
                    expected_bookings=0
                elif scenario in {'expired_quote','superseded_quote','unauthorized'}:
                    if scenario!='unauthorized':
                        async with factory() as db:
                            await db.execute(update(Quote).where(Quote.id==quotes[0]).values(**({'expires_at':datetime.now(UTC)-timedelta(seconds=1)} if scenario=='expired_quote' else {'version':2})));await db.commit()
                        response=await accept()
                        assert response.status_code==409
                    else:
                        response=await client.post(f'/api/v1/quotes/{quotes[0]}/accept-shared',headers=headers[1],json={'expected_version':1,'idempotency_key':'fictional-foreign','accept_final_price':True})
                        assert response.status_code==404
                    expected_bookings=0;expected_remaining=Decimal('1.1')
                else:
                    hold=await reserve();assert hold.status_code==201
                    hold_id=hold.json()['reservation_id']
                    if scenario=='expiry_accept_race':
                        async with factory() as db:
                            await db.execute(update(CapacityReservation).where(CapacityReservation.id==uuid.UUID(hold_id)).values(expires_at=datetime.now(UTC)-timedelta(seconds=1)));await db.commit()
                        response,_=await asyncio.wait_for(asyncio.gather(accept(hold=hold_id),expire()),20)
                        assert response.status_code==409
                        expected_bookings=0;expected_remaining=Decimal('1.1')
                    else:
                        response=await accept(hold=hold_id);assert response.status_code==201
                        booking=response.json()['id']
                        if scenario=='cancel_expiry_race':
                            first,_,second=await asyncio.wait_for(asyncio.gather(cancel(booking),expire(),cancel(booking)),20)
                            assert sorted([first.status_code,second.status_code])==[201,409]
                        else:
                            assert (await cancel(booking)).status_code==201
                            assert (await cancel(booking)).status_code==409
                        expected_remaining=Decimal('1.1')
                async with factory() as db:
                    assert await db.scalar(select(func.count(Booking.id)))==expected_bookings
                    route=await db.get(AvailableRoute,route_id)
                    assert route.remaining_capacity_tonnes==expected_remaining and route.remaining_volume_m3==expected_remaining
                    assert await db.scalar(select(func.count(Payment.id)))==0
                    if expected_bookings:
                        booking=await db.scalar(select(Booking))
                        assert booking.total_amount==750
                        allocation=await db.scalar(select(BookingAllocation).where(BookingAllocation.booking_id==booking.id))
                        assert allocation.agreed_amount==750
                        assert Decimal(allocation.quote_snapshot['final_price'])==750
                        assert allocation.quote_snapshot['version']==1
                        assert booking.route_snapshot['carrier_vehicle_id'] and booking.route_snapshot['driver_id']
                        assert booking.status==('cancelled' if scenario in {'hold_accept_cancel','cancel_expiry_race'} else 'advance_pending')
                    if scenario in {'hold_accept_cancel','cancel_expiry_race'}:
                        assert await db.scalar(select(func.count(Cancellation.id)))==1
    run_local(exercise())
