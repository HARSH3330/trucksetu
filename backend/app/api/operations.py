from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import AnalyticsEvent, AuditLog
from app.models import User
from app.schemas import AnalyticsEventCreate
from app.api.auth import require_roles

router=APIRouter(prefix="/api/v1",tags=["analytics and operations"])


@router.post("/analytics/events",status_code=status.HTTP_202_ACCEPTED)
async def capture_event(payload:AnalyticsEventCreate,request:Request,db:AsyncSession=Depends(get_db))->dict[str,bool]:
    item=AnalyticsEvent(**payload.model_dump());db.add(item)
    db.add(AuditLog(actor_id=payload.user_id,action="analytics.event_captured",entity_type="analytics_event",entity_id=item.id,after={"event_name":payload.event_name},request_id=getattr(request.state,"request_id",None),ip_address=request.client.host if request.client else None))
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
