from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import AnalyticsEvent, AuditLog, Booking, BookingAllocation, CarrierVehicle, Dispute, KYCApplication, ProviderProfile, Quote, TransportRequest, Trip
from app.models import User
from app.schemas import AnalyticsEventCreate
from app.api.auth import require_roles
from app.api.auth import current_user

router=APIRouter(prefix="/api/v1",tags=["analytics and operations"])


@router.get("/dashboard/summary")
async def dashboard_summary(db:AsyncSession=Depends(get_db),user:User=Depends(current_user))->dict[str,object]:
    roles={role.role for role in user.roles}
    provider=await db.scalar(select(ProviderProfile).where(ProviderProfile.user_id==user.id))
    if provider and roles.intersection({"provider","fleet_owner"}):
        booking_ids=select(BookingAllocation.booking_id).where(BookingAllocation.provider_id==provider.id)
        request_count=0
        quote_count=int(await db.scalar(select(func.count(Quote.id)).where(Quote.provider_id==provider.id)) or 0)
    else:
        booking_ids=select(Booking.id).where(Booking.customer_id==user.id)
        request_count=int(await db.scalar(select(func.count(TransportRequest.id)).where(TransportRequest.customer_id==user.id,TransportRequest.status.in_({"draft","published"}))) or 0)
        quote_count=int(await db.scalar(select(func.count(Quote.id)).join(TransportRequest,TransportRequest.id==Quote.request_id).where(TransportRequest.customer_id==user.id,Quote.status=="active")) or 0)
    active_bookings=int(await db.scalar(select(func.count(Booking.id)).where(Booking.id.in_(booking_ids),Booking.status.not_in({"completed","cancelled"}))) or 0)
    completed_bookings=int(await db.scalar(select(func.count(Booking.id)).where(Booking.id.in_(booking_ids),Booking.status=="completed")) or 0)
    total_value=await db.scalar(select(func.coalesce(func.sum(Booking.total_amount),0)).where(Booking.id.in_(booking_ids),Booking.status!="cancelled"))
    active_trips=int(await db.scalar(select(func.count(Trip.id)).join(BookingAllocation).where(BookingAllocation.booking_id.in_(booking_ids),Trip.status.not_in({"completed","cancelled"}))) or 0)
    return {"roles":sorted(roles),"open_requests":request_count,"active_quotes":quote_count,"active_bookings":active_bookings,"active_trips":active_trips,"completed_bookings":completed_bookings,"total_booking_value":str(total_value),"provider_rating":str(provider.rating) if provider else None,"provider_kyc_status":provider.kyc_status if provider else None}


@router.get("/admin/marketplace-health")
async def marketplace_health(db:AsyncSession=Depends(get_db),_:User=Depends(require_roles("admin","superadmin")))->dict[str,object]:
    total_bookings=int(await db.scalar(select(func.count(Booking.id))) or 0)
    completed=int(await db.scalar(select(func.count(Booking.id)).where(Booking.status=="completed")) or 0)
    gmv=await db.scalar(select(func.coalesce(func.sum(Booking.total_amount),0)).where(Booking.status!="cancelled"))
    return {
        "verified_providers":int(await db.scalar(select(func.count(ProviderProfile.id)).where(ProviderProfile.kyc_status=="verified",ProviderProfile.active.is_(True))) or 0),
        "approved_vehicles":int(await db.scalar(select(func.count(CarrierVehicle.id)).where(CarrierVehicle.status=="approved")) or 0),
        "open_requests":int(await db.scalar(select(func.count(TransportRequest.id)).where(TransportRequest.status=="published")) or 0),
        "active_quotes":int(await db.scalar(select(func.count(Quote.id)).where(Quote.status=="active")) or 0),
        "active_bookings":int(await db.scalar(select(func.count(Booking.id)).where(Booking.status.not_in({"completed","cancelled"}))) or 0),
        "open_disputes":int(await db.scalar(select(func.count(Dispute.id)).where(Dispute.status.in_({"open","under_review"}))) or 0),
        "pending_kyc":int(await db.scalar(select(func.count(KYCApplication.id)).where(KYCApplication.status.in_({"documents_submitted","under_review"}))) or 0),
        "gmv":str(gmv),"total_bookings":total_bookings,"completed_bookings":completed,
        "completion_rate":round(completed*100/total_bookings,1) if total_bookings else 0,
    }


@router.post("/analytics/events",status_code=status.HTTP_202_ACCEPTED)
async def capture_event(payload:AnalyticsEventCreate,request:Request,db:AsyncSession=Depends(get_db))->dict[str,bool]:
    item=AnalyticsEvent(user_id=None,**payload.model_dump());db.add(item)
    db.add(AuditLog(actor_id=None,action="analytics.event_captured",entity_type="analytics_event",entity_id=item.id,after={"event_name":payload.event_name},request_id=getattr(request.state,"request_id",None),ip_address=request.client.host if request.client else None))
    return {"accepted":True}


@router.get("/admin/analytics/funnel")
async def funnel(days:int=Query(default=30,ge=1,le=365),db:AsyncSession=Depends(get_db),_:User=Depends(require_roles("admin","superadmin")))->dict[str,object]:
    since=datetime.now(UTC)-timedelta(days=days)
    rows=await db.execute(select(AnalyticsEvent.event_name,func.count(AnalyticsEvent.id)).where(AnalyticsEvent.occurred_at>=since).group_by(AnalyticsEvent.event_name))
    counts={name:int(count) for name,count in rows}
    order=["visitor","signup","request_posted","quote_submitted","booking_created","trip_completed"]
    return {"period_days":days,"funnel":[{"stage":stage,"count":counts.get(stage,0)} for stage in order]}


@router.get("/admin/audit-logs")
async def audit_logs(limit:int=Query(default=100,ge=1,le=500),db:AsyncSession=Depends(get_db),_:User=Depends(require_roles("admin","superadmin")))->list[dict[str,object]]:
    items=list(await db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)))
    return [{"id":str(x.id),"actor_id":str(x.actor_id) if x.actor_id else None,"action":x.action,"entity_type":x.entity_type,"entity_id":str(x.entity_id) if x.entity_id else None,"request_id":x.request_id,"created_at":x.created_at.isoformat()} for x in items]
