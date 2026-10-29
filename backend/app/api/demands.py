"""Customer-led requirements, bidding and separately accounted connection fees."""
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.api.auth import require_roles
from app.api.bookings import assign_driver
from app.api.requests import create_request
from app.api.terms import require_terms
from app.core.config import settings
from app.core.database import acquire_idempotency_lock, get_db
from app.core.rate_limit import enforce_rate_limit
from app.core.routing import AuthenticationFirstRoute
from app.models import (
    Booking, BookingAllocation, ConnectionFeeEvent, DemandDraft, DemandSelection, Quote, QuoteVersion, TransportRequest, Trip,
)
from app.schemas import DriverAssignment
from app.services.demand_policy import public_text, read_policy, reject_contact, require_policy
from app.services.demand_schemas import CancelInput,AssignmentInput, BidInput, DemandInput, DraftInput, SelectionInput
from app.services.demand_marketplace import (
    audit, bid_view, demand_for, demand_view, eligible_driver, eligible_vehicle,
    expire_pending, expire_due, provider_for, reconcile_event, selection_for, selection_view, selection_views,
)
from app.services.payments import RazorpayGateway, SandboxRazorpayGateway, require_razorpay_sandbox, verify_razorpay_signature
from app.services.contact_access import verified_contact, selected_contact

router = APIRouter(prefix='/api/v1', tags=['customer demand marketplace'], route_class=AuthenticationFirstRoute)
customer = require_roles('customer')
provider_role = require_roles('provider','fleet_owner')
participant = require_roles('customer','provider','fleet_owner','admin','superadmin')


def get_connection_gateway():
    if settings.ENABLE_RAZORPAY_SANDBOX:
        try:require_razorpay_sandbox()
        except RuntimeError:raise HTTPException(503,'Sandbox payment configuration is unavailable') from None
        return SandboxRazorpayGateway()
    return RazorpayGateway()


def owner(item, user):
    if item.customer_id != user.id:
        raise HTTPException(404, 'Transport requirement not found')


def require_customer_policy(user):
    require_policy()
    if not (user.email_verified or user.mobile_verified):
        raise HTTPException(403, 'Verify your account before publishing a transport requirement')


async def read_bid(db, identity):
    return await db.scalar(select(Quote).where(Quote.id == identity).options(selectinload(Quote.provider), selectinload(Quote.vehicle_category), selectinload(Quote.versions)))


@router.get('/marketplace')
async def marketplace_config():
    policy, fee = read_policy(), read_policy('fee')
    from app.services.connection_fee_rules import proposed_fee
    proposed=proposed_fee(settings.CONNECTION_FEE_AMOUNT,settings.CONNECTION_FEE_TAX_RATE)
    return {'mode':'customer_demands', 'enabled':settings.ENABLE_CUSTOMER_DEMAND_MARKETPLACE,
            'legacy_provider_operations':settings.ENABLE_LEGACY_PROVIDER_MARKETPLACE,
            'provider_first_publication_available':bool(settings.ENABLE_PROVIDER_FIRST_PUBLICATION and settings.ENABLE_SHARED_CAPACITY),
            'publication_available':bool(policy and settings.ENABLE_CUSTOMER_DEMAND_MARKETPLACE),
            'checkout_available':bool(policy and fee and settings.ENABLE_CUSTOMER_DEMAND_MARKETPLACE and (fee.test_only or (settings.ENABLE_REAL_CONNECTION_CHECKOUT and settings.CONNECTION_FEE_TAX_CONFIRMED))),
            'real_checkout_available':bool(policy and fee and not fee.test_only and settings.ENABLE_REAL_CONNECTION_CHECKOUT and settings.CONNECTION_FEE_TAX_CONFIRMED),
            'fee':dict(fee.model_dump(mode='json'),total=str(fee.total),tax_rate=str(settings.CONNECTION_FEE_TAX_RATE),tax_confirmed=settings.CONNECTION_FEE_TAX_CONFIRMED) if fee else {'amount':str(settings.CONNECTION_FEE_AMOUNT),'total':str(proposed['total']),'currency':settings.CONNECTION_FEE_CURRENCY,'basis':'booking','tax_treatment':'proposed_additional','tax_amount':str(proposed['tax']),'tax_rate':str(settings.CONNECTION_FEE_TAX_RATE),'tax_confirmed':settings.CONNECTION_FEE_TAX_CONFIRMED,'version':None},
            'driver_assignment':policy.driver_assignment if policy else None}


@router.get('/demands/drafts')
async def drafts(db=Depends(get_db), user=Depends(customer)):
    items = await db.scalars(select(DemandDraft).where(DemandDraft.customer_id == user.id).order_by(DemandDraft.updated_at.desc()).limit(30))
    return [{'id':str(x.id),'version':x.version,'payload':x.payload,'updated_at':x.updated_at} for x in items]


@router.post('/demands/drafts', status_code=201)
async def save_draft(payload: DraftInput, db=Depends(get_db), user=Depends(customer)):
    item = DemandDraft(customer_id=user.id, payload=payload.payload)
    db.add(item)
    await db.flush()
    await db.commit()
    return {'id':str(item.id),'version':item.version}


@router.put('/demands/drafts/{identity}')
async def update_draft(identity: uuid.UUID, payload: DraftInput, db=Depends(get_db), user=Depends(customer)):
    item = await db.scalar(select(DemandDraft).where(DemandDraft.id == identity).with_for_update())
    if item is None or item.customer_id != user.id:
        raise HTTPException(404, 'Draft not found')
    if payload.expected_version != item.version:
        raise HTTPException(409, 'Draft changed in another session; reopen it before saving')
    item.payload, item.version = payload.payload, item.version+1
    await db.commit()
    return {'id':str(item.id),'version':item.version}


@router.post('/demands', status_code=201)
async def publish_demand(payload: DemandInput, db=Depends(get_db), user=Depends(customer)):
    require_customer_policy(user)
    from app.services.customer_kyc import require_customer_kyc
    await require_customer_kyc(db, user)
    await require_terms(db, user.id)
    reject_contact(payload.cargo.category, payload.cargo.description, payload.special_instructions)
    draft = None
    if payload.draft_id:
        draft = await db.scalar(select(DemandDraft).where(DemandDraft.id == payload.draft_id).with_for_update())
        if not draft or draft.customer_id != user.id:
            raise HTTPException(404, 'Draft not found')
        if payload.expected_draft_version != draft.version:
            raise HTTPException(409,'Draft changed in another session; review it before publishing')
    result = await create_request(payload.model_copy(update={'publish':True}), db, user)
    item = await db.get(TransportRequest, result.id, options=[selectinload(TransportRequest.cargo), selectinload(TransportRequest.stops)])
    item.marketplace_mode = 'customer_demand'
    item.pickup_location = payload.pickup_location.model_dump() if payload.pickup_location else None
    item.destination_location = payload.destination_location.model_dump() if payload.destination_location else None
    if draft:
        await db.delete(draft)
    audit(db, user.id, 'demand.published', 'transport_request', item.id, {'revision':item.revision})
    await db.commit()
    return demand_view(item, True)


@router.get('/demands/mine')
async def own_demands(db=Depends(get_db), user=Depends(customer)):
    items = list(await db.scalars(select(TransportRequest).where(TransportRequest.customer_id == user.id, TransportRequest.marketplace_mode == 'customer_demand').options(selectinload(TransportRequest.cargo), selectinload(TransportRequest.stops)).order_by(TransportRequest.created_at.desc()).limit(100)))
    return [demand_view(item, True) for item in items]


@router.get('/demands')
async def discover_demands(pickup: str = Query('', max_length=100), destination: str = Query('', max_length=100), goods: str = Query('', max_length=100), page: int = Query(1,ge=1,le=10000), db=Depends(get_db), user=Depends(provider_role)):
    require_policy()
    await provider_for(db, user)
    await expire_due(db)
    query = select(TransportRequest).where(TransportRequest.marketplace_mode == 'customer_demand', TransportRequest.status == 'published', TransportRequest.customer_id != user.id, TransportRequest.delivery_deadline_at > datetime.now(UTC)).options(selectinload(TransportRequest.cargo),selectinload(TransportRequest.stops))
    if pickup:
        query = query.where(TransportRequest.pickup_city.ilike('%'+pickup+'%'))
    if destination:
        query = query.where(TransportRequest.destination_city.ilike('%'+destination+'%'))
    if goods:
        from app.models import CargoItem
        query = query.join(CargoItem).where(CargoItem.category.ilike('%'+goods+'%'))
    items = await db.scalars(query.order_by(TransportRequest.pickup_date).offset((page-1)*30).limit(30))
    return [demand_view(item) for item in items]


@router.get('/demands/{identity}')
async def demand_detail(identity: uuid.UUID, db=Depends(get_db), user=Depends(participant)):
    item = await demand_for(db, identity)
    if item.customer_id != user.id:
        await provider_for(db, user)
    return demand_view(item, item.customer_id == user.id)


@router.put('/demands/{identity}')
async def edit_demand(identity: uuid.UUID, payload: DemandInput, db=Depends(get_db), user=Depends(customer)):
    require_customer_policy(user)
    from app.services.customer_kyc import require_customer_kyc
    await require_customer_kyc(db, user)
    item = await demand_for(db, identity, lock=True)
    owner(item,user)
    await expire_pending(db,item)
    if item.status != 'published' or payload.expected_revision != item.revision:
        raise HTTPException(409, 'Only the current open requirement can be edited; accepted agreements stay unchanged')
    reject_contact(payload.cargo.category, payload.cargo.description, payload.special_instructions)
    # Revalidate using the existing creation contract, but keep the original identity.
    for key in ['pickup_address','pickup_city','destination_address','destination_city','pickup_date','pickup_time','flexible_schedule','earliest_pickup_at','latest_pickup_at','delivery_deadline_at','budget_amount','special_instructions']:
        setattr(item,key,getattr(payload,key))
    for key,value in payload.cargo.model_dump().items():
        setattr(item.cargo,key,value)
    item.pickup_location = payload.pickup_location.model_dump() if payload.pickup_location else None
    item.destination_location = payload.destination_location.model_dump() if payload.destination_location else None
    item.revision += 1
    await db.execute(update(Quote).where(Quote.request_id == item.id,Quote.status == 'active').values(status='expired'))
    audit(db,user.id,'demand.edited_bids_expired','transport_request',item.id,{'revision':item.revision})
    await db.commit()
    return demand_view(item,True)


@router.post('/demands/{identity}/bids',status_code=201)
async def submit_bid(identity: uuid.UUID, payload: BidInput, db=Depends(get_db), user=Depends(provider_role)):
    require_policy()
    item = await demand_for(db,identity,lock=True)
    await expire_pending(db,item)
    provider = await provider_for(db,user)
    if item.customer_id == user.id:
        raise HTTPException(403,'You cannot bid on your own transport requirement')
    if item.status != 'published' or item.revision != payload.expected_request_revision:
        raise HTTPException(409,'Requirement changed or is no longer open')
    if payload.currency != item.currency or payload.pickup_at < item.earliest_pickup_at or payload.pickup_at > item.latest_pickup_at or payload.delivery_at > item.delivery_deadline_at:
        raise HTTPException(422,'Bid currency and availability must match the requirement')
    reject_contact(payload.inclusions,payload.exclusions,payload.notes)
    vehicle = await eligible_vehicle(db,payload.vehicle_id,provider.id,item,payload.pickup_at,payload.delivery_at)
    await verified_contact(db,provider.id,payload.contact_kind,payload.driver_id,payload.delivery_at.date())
    quote = await db.scalar(select(Quote).where(Quote.request_id == identity,Quote.provider_id == provider.id).with_for_update())
    if quote:
        if quote.status not in {'active','withdrawn','expired'} or quote.version != payload.expected_version:
            raise HTTPException(409,'Only your current unselected bid can be revised')
        quote.version += 1
    else:
        quote = Quote(id=uuid.uuid4(),request_id=identity,provider_id=provider.id,vehicle_category_id=vehicle.vehicle_category_id,vehicles_offered=1,version=1)
        db.add(quote)
    quote.status,quote.final_price,quote.currency = 'active',payload.amount,payload.currency
    quote.vehicle_category_id = vehicle.vehicle_category_id
    quote.estimated_pickup,quote.estimated_delivery,quote.expires_at = payload.pickup_at,payload.delivery_at,payload.expires_at
    quote.inclusions,quote.exclusions,quote.notes = payload.inclusions,payload.exclusions,payload.notes
    snapshot = {'request_revision':item.revision,'vehicle_id':str(vehicle.id),'vehicle':{'body_type':vehicle.body_type,'payload_tonnes':str(vehicle.maximum_payload_tonnes),'volume_m3':str(vehicle.maximum_volume_m3)},**payload.model_dump(mode='json')}
    db.add(QuoteVersion(quote_id=quote.id,version=quote.version,final_price=payload.amount,vehicles_offered=1,notes=payload.notes,snapshot=snapshot))
    await db.flush()
    audit(db,user.id,'bid.submitted_or_revised','quote',quote.id,{'version':quote.version})
    await db.commit()
    return bid_view(await read_bid(db,quote.id))


@router.get('/demands/{identity}/bids')
async def compare_bids(identity: uuid.UUID, db=Depends(get_db), user=Depends(customer)):
    item = await demand_for(db,identity)
    owner(item,user)
    items = await db.scalars(select(Quote).where(Quote.request_id == identity).options(selectinload(Quote.provider),selectinload(Quote.vehicle_category),selectinload(Quote.versions)).order_by(Quote.final_price))
    return [bid_view(x) for x in items]


@router.get('/demand-bids/mine')
async def my_bids(db=Depends(get_db),user=Depends(provider_role)):
    provider = await provider_for(db,user)
    items = await db.scalars(select(Quote).join(TransportRequest).where(Quote.provider_id == provider.id,TransportRequest.marketplace_mode == 'customer_demand').options(selectinload(Quote.provider),selectinload(Quote.vehicle_category),selectinload(Quote.versions)).order_by(Quote.created_at.desc()).limit(100))
    return [bid_view(x) for x in items]


@router.post('/demand-bids/{identity}/withdraw')
async def withdraw_bid(identity: uuid.UUID,db=Depends(get_db),user=Depends(provider_role)):
    located = await db.get(Quote,identity)
    if not located:
        raise HTTPException(404,'Bid not found')
    item = await demand_for(db,located.request_id,lock=True)
    await expire_pending(db,item)
    provider = await provider_for(db,user)
    quote = await db.scalar(select(Quote).where(Quote.id == identity).with_for_update().execution_options(populate_existing=True))
    if quote.provider_id != provider.id:
        raise HTTPException(404,'Bid not found')
    if quote.status not in {'active','withdrawn'}:
        raise HTTPException(409,'Selected bids cannot be silently withdrawn; contact operations to resolve the commitment')
    quote.status = 'withdrawn'
    audit(db,user.id,'bid.withdrawn','quote',quote.id)
    await db.commit()
    return {'status':'withdrawn'}


@router.post('/demands/{identity}/select',status_code=201)
async def select_bid(identity: uuid.UUID,payload: SelectionInput,db=Depends(get_db),user=Depends(customer)):
    policy,fee = require_policy(),require_policy('fee')
    await require_terms(db,user.id)
    item = await demand_for(db,identity,lock=True)
    owner(item,user)
    await expire_pending(db,item)
    await acquire_idempotency_lock(db,'connection-select:'+payload.idempotency_key)
    existing = await db.scalar(select(DemandSelection).where(DemandSelection.idempotency_key == payload.idempotency_key))
    if existing:
        if existing.customer_id != user.id or existing.request_id != identity or existing.quote_id != payload.quote_id or existing.quote_version != payload.expected_quote_version:
            raise HTTPException(409,'Idempotency key belongs to another selection')
        return selection_view(existing)
    if item.status != 'published' or item.revision != payload.expected_request_revision:
        raise HTTPException(409,'Requirement already selected or changed')
    prior_checkout = await db.scalar(select(DemandSelection.id).where(DemandSelection.request_id == identity, (DemandSelection.gateway_order_id.is_not(None) | DemandSelection.order_state.in_(['creating','unknown']))).limit(1))
    if prior_checkout:
        raise HTTPException(409,'A previous checkout needs payment reconciliation before another connection fee can be created')
    if not payload.accept_terms or payload.accepted_fee_policy_version != fee.version:
        raise HTTPException(422,'Review and accept the current connection-fee terms')
    quote = await db.scalar(select(Quote).where(Quote.id == payload.quote_id,Quote.request_id == identity).with_for_update().options(selectinload(Quote.provider),selectinload(Quote.vehicle_category),selectinload(Quote.versions)))
    if not quote or quote.status != 'active' or quote.version != payload.expected_quote_version or not quote.expires_at or quote.expires_at <= datetime.now(UTC):
        raise HTTPException(409,'Bid expired, changed or is no longer available')
    if not quote.provider.active or quote.provider.kyc_status != 'verified':
        raise HTTPException(409,'Provider verification is no longer current')
    snapshot = next((v.snapshot for v in quote.versions if v.version == quote.version),None)
    if not snapshot or snapshot.get('request_revision') != item.revision:
        raise HTTPException(409,'Bid does not match the current requirement')
    vehicle = await eligible_vehicle(db,uuid.UUID(snapshot['vehicle_id']),quote.provider_id,item,quote.estimated_pickup,quote.estimated_delivery)
    contact_kind = snapshot.get('contact_kind','provider')
    driver_id = uuid.UUID(snapshot['driver_id']) if snapshot.get('driver_id') else None
    proof = await verified_contact(db,quote.provider_id,contact_kind,driver_id,quote.estimated_delivery.date())
    driver = await eligible_driver(db,driver_id,quote.provider_id,quote.estimated_pickup,quote.estimated_delivery) if driver_id else None
    selection_id = uuid.uuid4()
    booking = Booking(id=uuid.uuid4(),public_id='TX-'+uuid.uuid4().hex[:16],request_id=item.id,customer_id=user.id,acceptance_key='connection:'+str(selection_id),status='connection_fee_pending',total_amount=quote.final_price,currency=quote.currency,customer_snapshot={'name':public_text(user.full_name)},route_snapshot={'pickup_city':item.pickup_city,'destination_city':item.destination_city,'marketplace_mode':'customer_demand'},cargo_snapshot={'category':public_text(item.cargo.category),'weight_tonnes':str(item.cargo.weight_tonnes),'volume_m3':str(item.cargo.volume_m3)})
    allocation = BookingAllocation(id=uuid.uuid4(),quote_id=quote.id,provider_id=quote.provider_id,trucks_allocated=1,agreed_amount=quote.final_price,quote_snapshot=bid_view(quote))
    # JSON snapshots must contain portable values, never raw datetime/Decimal.
    from fastapi.encoders import jsonable_encoder
    allocation.quote_snapshot = jsonable_encoder(allocation.quote_snapshot)
    allocation.trips = [Trip(status='driver_assigned' if driver else 'booking_confirmed',driver_id=driver.id if driver else None,carrier_vehicle_id=vehicle.id if driver else None,vehicle_registration=vehicle.registration_number if driver else None)]
    booking.allocations = [allocation]
    db.add(booking)
    await db.flush()
    fee_snapshot = dict(fee.model_dump(mode='json'),total=str(fee.total),freight_payment_separate=True,tax_rate=str(settings.CONNECTION_FEE_TAX_RATE),tax_confirmed=settings.CONNECTION_FEE_TAX_CONFIRMED)
    selected = DemandSelection(id=selection_id,request_id=item.id,quote_id=quote.id,booking_id=booking.id,customer_id=user.id,vehicle_id=vehicle.id,driver_id=driver.id if driver else None,contact_kind=proof.kind,contact_user_id=proof.user_id,contact_phone_hash=proof.phone_hash,idempotency_key=payload.idempotency_key,request_revision=item.revision,quote_version=quote.version,quote_snapshot=allocation.quote_snapshot,fee_snapshot=fee_snapshot,fee_amount=fee.total,fee_tax=fee.tax_amount,currency=fee.currency,expires_at=min(datetime.now(UTC)+timedelta(minutes=policy.selection_minutes),quote.expires_at))
    db.add(selected)
    item.status,quote.status = 'selection_pending','selected'
    audit(db,user.id,'connection.bid_selected','demand_selection',selection_id,{'booking_id':str(booking.id),'quote_version':quote.version})
    await db.commit()
    return selection_view(selected)


@router.get('/demand-selections/mine')
async def my_selections(db=Depends(get_db),user=Depends(participant)):
    await expire_due(db)
    query = select(DemandSelection).order_by(DemandSelection.created_at.desc()).limit(100)
    roles = {r.role for r in user.roles}
    if not roles.intersection({'admin','superadmin'}):
        if roles.intersection({'provider','fleet_owner'}):
            provider = await provider_for(db,user)
            query = query.join(Quote).where(Quote.provider_id == provider.id)
        else:
            query = query.where(DemandSelection.customer_id == user.id)
    rows=list(await db.scalars(query))
    return await selection_views(db,rows,include_refunds=bool(roles.intersection({"customer","admin","superadmin"})))


@router.get('/demand-selections/{identity}')
async def selection_status(identity: uuid.UUID,db=Depends(get_db),user=Depends(customer)):
    item,demand = await selection_for(db,identity)
    owner(demand,user)
    result=(await selection_views(db,[item]))[0]
    await db.commit()
    return result


@router.post('/demand-selections/{identity}/order')
async def checkout_order(identity: uuid.UUID,request: Request,db=Depends(get_db),user=Depends(customer),gateway=Depends(get_connection_gateway)):
    fee_policy = require_policy('fee')
    sandbox_gateway=isinstance(gateway,SandboxRazorpayGateway)
    if sandbox_gateway:
        require_razorpay_sandbox()
        if not fee_policy.test_only:raise HTTPException(503,'Sandbox requires a clearly marked test fee policy')
    if fee_policy.test_only and isinstance(gateway,RazorpayGateway) and not sandbox_gateway:
        raise HTTPException(503,'Sandbox checkout requires an isolated simulated gateway')
    if not fee_policy.test_only and (not settings.ENABLE_REAL_CONNECTION_CHECKOUT or not settings.CONNECTION_FEE_TAX_CONFIRMED):
        raise HTTPException(503,'Real connection checkout remains disabled pending commercial policy approval')
    await enforce_rate_limit(request,'connection-checkout',10,60,str(user.id))
    item,demand = await selection_for(db,identity)
    owner(demand,user)
    if item.payment_status == 'captured':
        return {'already_paid':True,'selection_id':str(item.id)}
    if item.status != 'pending':
        raise HTTPException(409,'Selection is no longer awaiting payment')
    if not await selected_contact(db,item):
        raise HTTPException(409,'The promised verified contact is unavailable; checkout is blocked')
    if item.gateway_order_id:
        return {'order_id':item.gateway_order_id,'amount':int(item.fee_amount*100),'currency':item.currency,'key_id':settings.RAZORPAY_KEY_ID,'status':'pending','local_simulation':bool(getattr(gateway,'is_simulated',False) and settings.APP_ENV=='test')}
    if item.order_state != 'not_created':
        raise HTTPException(409,'Checkout creation is in progress or needs reconciliation; do not create another charge')
    if item.credit_id:
        raise HTTPException(503,'Platform connection fee waived. Checkout is blocked pending tax and accounting confirmation')
    item.order_state = 'creating'
    amount,currency = item.fee_amount,item.currency
    await db.commit()  # No database transaction while calling the gateway.
    try:
        order = await gateway.create_order(amount,currency,'connect-'+identity.hex[:24])
        if not isinstance(order.get('id'),str) or len(order['id'])>100 or order.get('amount') != int(amount*100) or order.get('currency') != currency:
            raise RuntimeError('Unexpected gateway order')
    except Exception:
        item,_ = await selection_for(db,identity)
        item.order_state = 'unknown'
        audit(db,user.id,'connection.order_needs_reconciliation','demand_selection',identity)
        await db.commit()
        raise HTTPException(503,'Checkout could not be confirmed. No contact has been unlocked; contact support before retrying') from None
    item,_ = await selection_for(db,identity)
    item.gateway_order_id,item.order_state = order['id'],'created'
    await db.commit()
    return {'order_id':order['id'],'amount':int(amount*100),'currency':currency,'key_id':settings.RAZORPAY_KEY_ID,'status':'pending',
            'local_simulation':bool(order.get('local_simulation') and settings.APP_ENV == 'test')}


@router.post('/connection-fees/webhook')
async def connection_webhook(request: Request,x_razorpay_signature: str=Header(),x_razorpay_event_id: str=Header(min_length=8,max_length=200),db=Depends(get_db)):
    await enforce_rate_limit(request,'connection-webhook',settings.RATE_LIMIT_PER_MINUTE,60)
    body = await request.body()
    if not verify_razorpay_signature(body,x_razorpay_signature):
        raise HTTPException(401,'Invalid webhook signature')
    try:
        payload = await request.json()
        kind = payload['event']
        key = 'refund' if isinstance(kind,str) and kind.startswith('refund.') else 'dispute' if kind == 'payment.dispute.created' else 'payment'
        entity = payload['payload'][key]['entity']
        if not isinstance(entity,dict) or not isinstance(kind,str):
            raise ValueError()
    except (KeyError,TypeError,ValueError):
        raise HTTPException(400,'Invalid payment event') from None
    reference = entity.get('order_id' if kind.startswith('payment.') and kind != 'payment.dispute.created' else 'payment_id')
    if not isinstance(reference,str) or not reference or len(reference)>100:
        raise HTTPException(400,'Payment event needs a valid gateway reference')
    if kind in {'payment.captured','payment.failed'} and (not isinstance(entity.get('id'),str) or not entity['id'] or len(entity['id'])>100):
        raise HTTPException(400,'Payment event needs a valid payment identifier')
    if kind in {'payment.captured','payment.failed','refund.created','refund.processed','refund.failed','payment.dispute.created'}:
        await reconcile_event(db,x_razorpay_event_id,kind,entity)
        await db.commit()
    return {'received':True}


@router.post('/demand-selections/{identity}/assignment')
async def confirm_assignment(identity: uuid.UUID,payload: AssignmentInput,db=Depends(get_db),user=Depends(provider_role)):
    item,demand = await selection_for(db,identity)
    provider = await provider_for(db,user)
    quote = await db.get(Quote,item.quote_id)
    if quote.provider_id != provider.id:
        raise HTTPException(404,'Selection not found')
    if item.status != 'paid' or item.payment_status != 'captured':
        raise HTTPException(409,'Captured connection fee is required before fulfillment assignment')
    if item.driver_id and item.driver_id != payload.driver_id:
        raise HTTPException(409,'Replacing an assigned driver requires an operations review; previously viewed contact cannot be unseen')
    if payload.vehicle_id != item.vehicle_id:
        raise HTTPException(409,'Use the selected bid vehicle; do not silently replace the accepted agreement')
    await eligible_vehicle(db,item.vehicle_id,provider.id,demand,quote.estimated_pickup,quote.estimated_delivery,own_selection=item.id)
    driver = await eligible_driver(db,payload.driver_id,provider.id,quote.estimated_pickup,quote.estimated_delivery,item.booking_id)
    trip = await db.scalar(select(Trip).join(BookingAllocation).where(BookingAllocation.booking_id == item.booking_id))
    item.driver_id = driver.id
    audit(db,user.id,'connection.assignment_confirmed','demand_selection',item.id,{'trip_id':str(trip.id),'driver_id':str(driver.id)})
    if trip.status == 'booking_confirmed':
        await assign_driver(trip.id,DriverAssignment(driver_id=driver.id,carrier_vehicle_id=item.vehicle_id),db,user)
    else:
        await db.commit()
    return selection_view(item)


@router.get('/demand-selections/{identity}/contact')
async def driver_contact(identity: uuid.UUID,response: Response,db=Depends(get_db),user=Depends(customer)):
    return await read_contact(identity,response,db,user,reveal=False)


@router.post('/demand-selections/{identity}/reveal')
async def reveal_contact(identity: uuid.UUID,response: Response,db=Depends(get_db),user=Depends(customer)):
    return await read_contact(identity,response,db,user,reveal=True)


async def read_contact(identity,response,db,user,*,reveal):
    response.headers['Cache-Control'] = 'private, no-store'
    item,demand = await selection_for(db,identity)
    owner(demand,user)
    booking = await db.get(Booking,item.booking_id)
    if item.status != 'paid' or item.payment_status != 'captured' or booking.status in {'cancelled','disputed'}:
        await db.commit()
        if reveal:raise HTTPException(409,'Contact reveal is unavailable for this booking')
        return {'state':'locked'}
    if not item.contact_revealed_at and not reveal:
        await db.commit()
        return {'state':'eligible','notice':'Payment verified. Choose Reveal contact to access the number. A full refund is available before reveal.'}
    proof = await selected_contact(db,item)
    if proof is None:
        return {'state':'unavailable','notice':'Purchased contact needs operations review; do not pay again.'}
    if not item.contact_revealed_at:
        item.contact_revealed_at=datetime.now(UTC)
        audit(db,user.id,'connection.contact_revealed','demand_selection',item.id,{'basis':'backend_verified_captured_payment'})
    result = {'state':'unlocked','contact_kind':proof.kind,'contact_name':public_text(proof.name),'phone':proof.phone,
              'notice':'Purchased for this booking. Revisit without paying again. Previously viewed contact cannot be made unseen.'}
    trip = await db.scalar(select(Trip).join(BookingAllocation).where(BookingAllocation.booking_id == item.booking_id))
    if trip and trip.driver_id:
        try:
            driver_proof = await verified_contact(db,(await db.get(Quote,item.quote_id)).provider_id,'driver',trip.driver_id)
            result.update(driver_name=public_text(driver_proof.name),driver_phone=driver_proof.phone)
        except HTTPException:
            pass
    audit(db,user.id,'connection.contact_accessed','demand_selection',item.id,{'contact_kind':proof.kind,'contact_user_id':str(proof.user_id),'basis':'verified_matching_captured_fee'})
    await db.commit()
    return result



@router.post('/demands/{identity}/cancel')
async def cancel_demand(identity: uuid.UUID,payload: CancelInput,db=Depends(get_db),user=Depends(customer)):
    item = await demand_for(db,identity,lock=True)
    owner(item,user)
    if item.status in {'completed','cancelled'}:
        raise HTTPException(409,'Requirement is already terminal')
    selections = list(await db.scalars(select(DemandSelection).where(DemandSelection.request_id==identity).with_for_update()))
    if any(selection.contact_revealed_at for selection in selections) and not payload.confirm_after_reveal:
        raise HTTPException(409,'Contact was revealed. Confirm ordinary cancellation without a refund')
    from app.services.connection_fee_rules import cancel_connection
    outcomes=[await cancel_connection(db,selection,item,user.id,payload.reason) for selection in selections if selection.status in {'pending','paid','refund_requested','cancelled'}]
    item.status='cancelled'
    audit(db,user.id,'demand.cancelled','transport_request',item.id,{'reason':public_text(payload.reason)})
    await db.commit()
    return {'status':'cancelled','connections':outcomes}



@router.get('/admin/connection-fees')
async def connection_fee_review(db=Depends(get_db),user=Depends(require_roles('admin','superadmin')),page: int=Query(default=1,ge=1,le=10000)):
    # Read-only operations visibility. No manual unlock, refund or new charge.
    offset=(page-1)*50
    selections=list(await db.scalars(select(DemandSelection).order_by(DemandSelection.created_at.desc()).offset(offset).limit(50)))
    events=list(await db.scalars(select(ConnectionFeeEvent).order_by(ConnectionFeeEvent.created_at.desc()).offset(offset).limit(50)))
    return {'page':page,'selections':await selection_views(db,selections),
            'events':[{'id':str(event.id),'selection_id':str(event.selection_id) if event.selection_id else None,'type':event.event_type,'outcome':event.outcome,'created_at':event.created_at} for event in events]}
