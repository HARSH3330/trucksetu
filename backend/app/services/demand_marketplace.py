"""Customer demand state transitions. Caller owns the request-first transaction."""
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.vehicles import vehicle_is_document_eligible
from app.api.vehicle_documents import require_accepted_documents
from app.models import (
    AuditLog, AvailableRoute, Booking, BookingAllocation, CarrierVehicle,
    ConnectionFeeEvent, DemandSelection, DriverProfile, ProviderProfile, Quote,
    TransportRequest, Trip, User,
)
from app.services.demand_policy import capture_error, public_text
from app.services.driver_eligibility import require_verified_driver_identity


def audit(db, actor, action, entity, identity, details=None):
    db.add(AuditLog(actor_id=actor, action=action, entity_type=entity, entity_id=identity, after=details or {}))


async def provider_for(db, user):
    provider = await db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user.id))
    if not provider or not provider.active or provider.kyc_status != 'verified':
        raise HTTPException(403, 'Complete provider verification before browsing demands or bidding')
    return provider


async def demand_for(db, identity, *, lock=False):
    query = select(TransportRequest).where(TransportRequest.id == identity, TransportRequest.marketplace_mode == 'customer_demand').options(selectinload(TransportRequest.cargo), selectinload(TransportRequest.stops))
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    item = await db.scalar(query)
    if item is None:
        raise HTTPException(404, 'Transport requirement not found')
    return item


async def expire_pending(db, demand):
    items = list(await db.scalars(select(DemandSelection).where(DemandSelection.request_id == demand.id, DemandSelection.status == 'pending').with_for_update()))
    for item in items:
        if item.expires_at <= datetime.now(UTC):
            from app.services.connection_fee_rules import release_unused_credit
            await release_unused_credit(db,item)
            item.status = 'expired'
            booking = await db.get(Booking, item.booking_id)
            booking.status = 'cancelled'
            trips = list(await db.scalars(select(Trip).join(BookingAllocation).where(BookingAllocation.booking_id == booking.id).with_for_update(of=Trip)))
            for trip in trips:
                trip.status = 'cancelled'
            quote = await db.get(Quote, item.quote_id)
            if quote.status == 'selected':
                quote.status = 'active' if quote.expires_at and quote.expires_at > datetime.now(UTC) else 'expired'
            if demand.status == 'selection_pending':
                demand.status = 'published'
            audit(db, None, 'connection.selection_expired', 'demand_selection', item.id)
    await db.flush()


async def selection_for(db, identity, *, lock=True):
    located = await db.get(DemandSelection, identity)
    if located is None:
        raise HTTPException(404, 'Selection not found')
    demand = await demand_for(db, located.request_id, lock=lock)
    await expire_pending(db, demand)
    query = select(DemandSelection).where(DemandSelection.id == identity).execution_options(populate_existing=True)
    if lock:
        query = query.with_for_update()
    return await db.scalar(query), demand


async def eligible_vehicle(db, identity, provider_id, demand, pickup, delivery, *, own_selection=None):
    vehicle = await db.scalar(select(CarrierVehicle).where(CarrierVehicle.id == identity).with_for_update().execution_options(populate_existing=True))
    if not vehicle or vehicle.provider_id != provider_id or not vehicle_is_document_eligible(vehicle, delivery.date()):
        raise HTTPException(409, 'Choose your approved vehicle with documents current through delivery')
    await require_accepted_documents(db, vehicle.id, delivery.date())
    cargo = demand.cargo
    if vehicle.maximum_payload_tonnes < cargo.weight_tonnes or vehicle.maximum_volume_m3 < cargo.volume_m3:
        raise HTTPException(422, 'This vehicle does not have enough load capacity')
    if cargo.length_m > vehicle.internal_length_m or cargo.width_m > vehicle.internal_width_m or cargo.height_m > vehicle.internal_height_m:
        raise HTTPException(422, 'Load dimensions exceed this vehicle; arrange a suitable vehicle')
    # Vehicle row serializes both new selections and existing assignment checks.
    busy = select(DemandSelection.id).join(Quote, Quote.id == DemandSelection.quote_id).where(
        DemandSelection.vehicle_id == identity,
        ((DemandSelection.status == 'paid') | ((DemandSelection.status == 'pending') & (DemandSelection.expires_at > datetime.now(UTC)))),
        Quote.estimated_pickup < delivery, Quote.estimated_delivery > pickup,
    )
    if own_selection:
        busy = busy.where(DemandSelection.id != own_selection)
    if await db.scalar(busy.limit(1)):
        raise HTTPException(409, 'Vehicle is already reserved for an overlapping job')
    trips = select(Trip.id).join(BookingAllocation, BookingAllocation.id == Trip.allocation_id).join(Quote, Quote.id == BookingAllocation.quote_id).where(
        Trip.carrier_vehicle_id == identity, Trip.status.not_in(['completed','delivered','cancelled']),
        Quote.estimated_pickup < delivery, Quote.estimated_delivery > pickup,
    )
    if own_selection:
        owner = await db.get(DemandSelection, own_selection)
        trips = trips.where(BookingAllocation.booking_id != owner.booking_id)
    if await db.scalar(trips.limit(1)):
        raise HTTPException(409, 'Vehicle has an overlapping active trip')
    routes = select(AvailableRoute.id).where(AvailableRoute.carrier_vehicle_id == identity, AvailableRoute.status == 'active', AvailableRoute.departure_at < delivery, AvailableRoute.expected_arrival_at > pickup)
    if await db.scalar(routes.limit(1)):
        raise HTTPException(409, 'Vehicle has an existing shared-route commitment')
    return vehicle


async def eligible_driver(db, identity, provider_id, pickup, delivery, own_booking=None):
    driver = await db.scalar(select(DriverProfile).where(DriverProfile.id == identity).with_for_update().execution_options(populate_existing=True))
    if not driver or driver.provider_id != provider_id or not driver.active or driver.kyc_status != 'verified' or not driver.licence_expires_on or driver.licence_expires_on < delivery.date():
        raise HTTPException(409, 'A verified provider driver with a current licence is required')
    await require_verified_driver_identity(db, driver)
    account = await db.get(User, driver.user_id) if driver.user_id else None
    if not account or account.status != 'active' or not account.mobile_verified or not account.mobile:
        raise HTTPException(409, 'Driver needs an active linked account with a verified phone number')
    busy = select(Trip.id).join(BookingAllocation, BookingAllocation.id == Trip.allocation_id).join(Quote, Quote.id == BookingAllocation.quote_id).where(Trip.driver_id == identity, Trip.status.not_in(['completed','delivered','cancelled']), Quote.estimated_pickup < delivery, Quote.estimated_delivery > pickup)
    if own_booking:
        busy = busy.where(BookingAllocation.booking_id != own_booking)
    if await db.scalar(busy.limit(1)):
        raise HTTPException(409, 'Driver has an overlapping active trip')
    return driver


def demand_view(item, private=False):
    cargo = item.cargo
    result = {'id':str(item.id), 'public_id':item.public_id, 'revision':item.revision, 'status':item.status,
              'pickup_city':public_text(item.pickup_city), 'destination_city':public_text(item.destination_city),
              'pickup_date':str(item.pickup_date), 'earliest_pickup_at':item.earliest_pickup_at, 'latest_pickup_at':item.latest_pickup_at,
              'delivery_deadline_at':item.delivery_deadline_at, 'flexible_schedule':item.flexible_schedule,
              'budget_amount':str(item.budget_amount) if item.budget_amount is not None else None,
              'cargo':{key:getattr(cargo,key) for key in ['category','description','weight_tonnes','length_m','width_m','height_m','packages','packaging_type','dimensions_are_per_package','loading_assistance','unloading_assistance','fragile','volume_m3']}}
    for key in ['category','description','packaging_type']:
        result['cargo'][key] = public_text(result['cargo'][key])
    if private:
        result.update(pickup_address=item.pickup_address, destination_address=item.destination_address, special_instructions=item.special_instructions, pickup_location=item.pickup_location, destination_location=item.destination_location)
    return result


def bid_view(quote):
    snapshot = next((v.snapshot or {} for v in quote.versions if v.version == quote.version), {})
    return {'id':str(quote.id), 'request_id':str(quote.request_id), 'version':quote.version, 'status':quote.status,
            'provider_name':public_text(quote.provider.display_name), 'provider_verified':quote.provider.active and quote.provider.kyc_status == 'verified',
            'amount':str(quote.final_price), 'currency':quote.currency, 'pickup_at':quote.estimated_pickup, 'delivery_at':quote.estimated_delivery,
            'expires_at':quote.expires_at, 'inclusions':public_text(quote.inclusions), 'exclusions':public_text(quote.exclusions), 'notes':public_text(quote.notes),
            'vehicle':snapshot.get('vehicle', {}), 'contact_kind':snapshot.get('contact_kind','provider'), 'request_revision':snapshot.get('request_revision')}


def selection_view(item):
    return {'id':str(item.id), 'vehicle_id':str(item.vehicle_id), 'request_id':str(item.request_id), 'quote_id':str(item.quote_id), 'booking_id':str(item.booking_id),
            'status':item.status, 'payment_status':item.payment_status, 'order_state':item.order_state, 'expires_at':item.expires_at,
            'quote':item.quote_snapshot, 'fee':item.fee_snapshot,
            'contact_state':'eligible' if item.status == 'paid' and item.payment_status == 'captured' else 'locked',
            'contact_revealed_at':item.contact_revealed_at,'credit_id':str(item.credit_id) if item.credit_id else None,
            'contact_kind':item.contact_kind, 'contact_label':'Unlock '+item.contact_kind+' contact',
            'assignment_state':'assigned' if item.driver_id else 'pending', 'freight_payment_separate':True}


async def selection_views(db,items,include_refunds=True):
    values=[selection_view(item) for item in items]
    if include_refunds and items:
        from app.models import ConnectionFeeRefundRequest
        rows=await db.scalars(select(ConnectionFeeRefundRequest).where(ConnectionFeeRefundRequest.selection_id.in_([item.id for item in items])))
        refunds={str(row.selection_id):{'id':str(row.id),'status':row.status,'amount':str(row.amount),'tax_amount':str(row.tax_amount) if row.tax_amount is not None else None,'currency':row.currency} for row in rows}
        for value in values:value['refund']=refunds.get(value['id'])
    return values


async def reconcile_event(db, event_id, event_type, entity):
    from app.core.database import acquire_idempotency_lock
    await acquire_idempotency_lock(db, 'connection-event:'+event_id)
    if await db.scalar(select(ConnectionFeeEvent.id).where(ConnectionFeeEvent.gateway_event_id == event_id)):
        return
    payment_reference = entity.get('id') if event_type in {'payment.captured','payment.failed'} else entity.get('payment_id')
    if isinstance(payment_reference,str) and payment_reference:
        await acquire_idempotency_lock(db,'connection-payment:'+payment_reference)
    details = {key:entity[key] for key in ('id','payment_id','order_id','amount','currency') if key in entity and isinstance(entity[key],(str,int))}
    if event_type in {'payment.captured','payment.failed'}:
        query = select(DemandSelection).where(DemandSelection.gateway_order_id == entity.get('order_id'))
    else:
        query = select(DemandSelection).where(DemandSelection.gateway_payment_id == entity.get('payment_id'))
    located = await db.scalar(query)
    if not located:
        db.add(ConnectionFeeEvent(selection_id=None,gateway_event_id=event_id,event_type=event_type,outcome='unmatched_reference',details=details))
        audit(db, None, 'connection.unknown_payment_event', 'connection_fee', None, {'event_type':event_type})
        return
    item, demand = await selection_for(db, located.id)
    booking = await db.scalar(select(Booking).where(Booking.id == item.booking_id).with_for_update())
    outcome = 'ignored'
    if event_type == 'payment.captured':
        payment_reference = entity.get('id')
        if isinstance(payment_reference,str):
            await acquire_idempotency_lock(db,'connection-payment:'+payment_reference)
        reused = await db.scalar(select(DemandSelection.id).where(DemandSelection.gateway_payment_id == payment_reference, DemandSelection.id != item.id)) if payment_reference else None
        rejection = 'payment_reference_already_used' if reused else capture_error(entity, item.fee_amount, item.currency)
        if rejection:
            outcome = rejection
        elif item.gateway_payment_id and item.gateway_payment_id != entity['id']:
            item.status = 'review_required'
            outcome = 'second_capture_requires_review'
        elif item.payment_status == 'captured':
            outcome = 'duplicate_capture'
        elif item.payment_status in {'refunded','disputed','refund_review'}:
            outcome = 'out_of_order_capture_requires_review'
        else:
            item.gateway_payment_id = entity['id']
            item.payment_status = 'captured'
            item.captured_at = datetime.now(UTC)
            prior_adverse = list(await db.scalars(select(ConnectionFeeEvent).where(
                ConnectionFeeEvent.event_type.in_(['refund.created','refund.processed','refund.failed','payment.dispute.created']),
                ConnectionFeeEvent.details['payment_id'].as_string() == payment_reference)))
            quote = await db.scalar(select(Quote).where(Quote.id == item.quote_id).with_for_update().execution_options(populate_existing=True))
            provider = await db.get(ProviderProfile, quote.provider_id)
            valid = (not prior_adverse and item.status == 'pending' and demand.status == 'selection_pending' and item.expires_at > datetime.now(UTC)
                     and quote.status == 'selected' and quote.version == item.quote_version and demand.revision == item.request_revision
                     and provider.active and provider.kyc_status == 'verified' and booking.status == 'connection_fee_pending')
            from app.services.contact_access import selected_contact
            if valid and not await selected_contact(db,item):
                valid = False
            if valid:
                try:
                    await eligible_vehicle(db,item.vehicle_id,quote.provider_id,demand,quote.estimated_pickup,quote.estimated_delivery,own_selection=item.id)
                except HTTPException:
                    valid = False
            if valid:
                from app.api.connection_fee_policy import redeem_captured_credit
                valid=await redeem_captured_credit(db,item)
            if valid:
                item.status, demand.status, quote.status, booking.status = 'paid','allocated','accepted','booking_confirmed'
                outcome = 'captured_contact_eligible'
            else:
                item.status = 'review_required'
                outcome = 'late_or_invalid_capture_requires_review'
                if prior_adverse:
                    item.payment_status = 'disputed' if any(event.event_type == 'payment.dispute.created' for event in prior_adverse) else 'refund_review'
                    outcome = 'prior_refund_or_dispute_contact_locked'
                    for event in prior_adverse:
                        event.selection_id = item.id
                        event.outcome = 'matched_after_capture_contact_locked'
    elif event_type == 'payment.failed' and item.payment_status == 'pending':
        item.payment_status = 'failed'
        outcome = 'failed_no_unlock'
    elif event_type in {'refund.created','refund.processed','refund.failed'} and item.gateway_payment_id == entity.get('payment_id'):
        from app.models import ConnectionFeeRefundRequest
        from app.services.connection_refunds import apply_refund_entity
        refund=await db.scalar(select(ConnectionFeeRefundRequest).where(ConnectionFeeRefundRequest.selection_id==item.id).with_for_update())
        # Every refund event locks contact. Only a bound exact obligation can
        # become complete; a signed event is not permission to infer its identity.
        item.status='review_required'
        if refund:
            if not refund.gateway_payment_id:refund.gateway_payment_id=item.gateway_payment_id
            expected={'refund.created':'pending','refund.processed':'processed','refund.failed':'failed'}[event_type]
            if entity.get('status')!=expected:
                outcome='refund_event_status_mismatch'
            else:outcome=apply_refund_entity(db,item,refund,entity)
        else:
            item.payment_status='refund_review'
            outcome='unmatched_refund_obligation_contact_locked'
    elif event_type == 'payment.dispute.created':
        item.payment_status, item.status = 'disputed','review_required'
        outcome = 'dispute_contact_locked'
    if event_type=='payment.captured' and item.cancelled_at and item.contact_revealed_at is None and item.payment_status=='captured':
        from app.services.connection_fee_rules import record_full_refund
        await record_full_refund(db,item,'Verified capture received after pre-reveal cancellation')
        item.status='refund_requested'
    db.add(ConnectionFeeEvent(selection_id=item.id, gateway_event_id=event_id, event_type=event_type, outcome=outcome, details=details))
    audit(db, None, 'connection.payment_reconciled', 'demand_selection', item.id, {'outcome':outcome, 'event_id':event_id})


async def expire_due(db):
    due = list(await db.scalars(select(DemandSelection.request_id).where(DemandSelection.status == 'pending',DemandSelection.expires_at <= datetime.now(UTC)).order_by(DemandSelection.request_id).limit(100)))
    for identity in sorted(set(due),key=str):
        demand = await demand_for(db,identity,lock=True)
        await expire_pending(db,demand)
    if due:
        await db.commit()
