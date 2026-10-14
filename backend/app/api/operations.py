from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import AnalyticsEvent, AuditLog, Booking, BookingAllocation, CarrierVehicle, Dispute, KYCApplication, ProviderProfile, Quote, TransportRequest, Trip
from app.models import User
from app.models import DriverProfile, RefreshSession
from app.schemas import AnalyticsEventCreate
from app.api.auth import require_roles
from app.api.auth import current_user

from app.core.routing import AuthenticationFirstRoute

router=APIRouter(route_class=AuthenticationFirstRoute, prefix="/api/v1",tags=["analytics and operations"])


class AccountStatus(BaseModel):
    status: Literal['active','suspended']
    reason: str=Field(min_length=10,max_length=2000)


@router.get('/admin/users')
async def list_users(q:str=Query(default='',max_length=120),account_status:Literal['active','suspended']|None=None,page:int=Query(default=1,ge=1,le=10000),page_size:int=Query(default=25,ge=1,le=100),db:AsyncSession=Depends(get_db),_:User=Depends(require_roles('admin','superadmin')))->dict[str,object]:
    filters=[]
    if q:filters.append(or_(User.full_name.icontains(q,autoescape=True),User.email.icontains(q,autoescape=True)))
    if account_status:filters.append(User.status==account_status)
    total=int(await db.scalar(select(func.count(User.id)).where(*filters)) or 0)
    items=await db.scalars(select(User).options(selectinload(User.roles)).where(*filters).order_by(User.created_at.desc(),User.id).offset((page-1)*page_size).limit(page_size))
    return {'total':total,'page':page,'page_size':page_size,'items':[{'id':str(item.id),'name':item.full_name,'email':item.email,'roles':sorted(role.role for role in item.roles),'status':item.status,'email_verified':item.email_verified,'created_at':item.created_at.isoformat()} for item in items]}


@router.get('/admin/bookings')
async def list_bookings(q:str=Query(default='',max_length=100),page:int=Query(default=1,ge=1,le=10000),page_size:int=Query(default=25,ge=1,le=100),db:AsyncSession=Depends(get_db),_:User=Depends(require_roles('admin','superadmin')))->dict[str,object]:
    filters=[Booking.public_id.icontains(q,autoescape=True)] if q else []
    total=int(await db.scalar(select(func.count(Booking.id)).where(*filters)) or 0)
    items=(await db.execute(select(Booking,User.full_name).join(User,User.id==Booking.customer_id).where(*filters).order_by(Booking.created_at.desc(),Booking.id).offset((page-1)*page_size).limit(page_size))).all()
    return {'total':total,'page':page,'page_size':page_size,'items':[{'id':str(item.id),'reference':item.public_id,'customer_name':name,'status':item.status,'total_amount':str(item.total_amount),'created_at':item.created_at.isoformat()} for item,name in items]}


@router.post('/admin/users/{user_id}/status')
async def change_account_status(user_id:uuid.UUID,payload:AccountStatus,db:AsyncSession=Depends(get_db),admin:User=Depends(require_roles('admin','superadmin')))->dict[str,str]:
    target=await db.scalar(select(User).options(selectinload(User.roles)).where(User.id==user_id).with_for_update())
    if not target:raise HTTPException(404,'Account not found')
    if target.id==admin.id or {role.role for role in target.roles}.intersection({'admin','superadmin'}):
        raise HTTPException(403,'Privileged and self account changes are not supported here')
    previous=target.status
    target.status=payload.status;target.auth_version=int(target.auth_version or 0)+1
    await db.execute(update(RefreshSession).where(RefreshSession.user_id==target.id,RefreshSession.revoked_at.is_(None)).values(revoked_at=datetime.now(UTC)))
    if payload.status=='suspended':
        await db.execute(update(ProviderProfile).where(ProviderProfile.user_id==target.id).values(active=False))
        await db.execute(update(DriverProfile).where(DriverProfile.user_id==target.id).values(active=False))
    db.add(AuditLog(actor_id=admin.id,action='admin.account_status_changed',entity_type='user',entity_id=target.id,before={'status':previous},after={'status':target.status,'reason':payload.reason,'sessions_revoked':True}))
    await db.commit()
    return {'id':str(target.id),'status':target.status,'supply_reactivation':'Requires separate KYC/driver review; account activation does not restore dispatch eligibility'}


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
