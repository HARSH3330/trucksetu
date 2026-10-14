from datetime import UTC,datetime

from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_user
from app.core.config import settings
from app.core.database import acquire_idempotency_lock,get_db
from app.core.rate_limit import enforce_rate_limit
from app.core.routing import AuthenticationFirstRoute
from app.core.security import hash_token
from app.models import AccountVerification,AuditLog,User
from app.services.dependencies import get_phone_verifier
from app.services.msg91_widget import InvalidWidgetVerification,Msg91WidgetVerifier,WidgetVerificationUnavailable,canonical_mobile

router=APIRouter(prefix='/api/v1/auth',tags=['phone verification'],route_class=AuthenticationFirstRoute)

class WidgetProof(BaseModel):
    verification_token:str=Field(min_length=20,max_length=4096,repr=False)


@router.post('/mobile/verify-widget')
async def verify_widget(payload:WidgetProof,request:Request,user:User=Depends(current_user),db:AsyncSession=Depends(get_db),verifier:Msg91WidgetVerifier=Depends(get_phone_verifier))->dict[str,bool]:
    await enforce_rate_limit(request,'phone-widget-verify',settings.VERIFICATION_RATE_LIMIT,600,str(user.id))
    try:verified_mobile=await verifier.verify(payload.verification_token)
    except InvalidWidgetVerification as exc:raise HTTPException(400,'Invalid or expired phone verification') from exc
    except WidgetVerificationUnavailable as exc:raise HTTPException(503,'Phone verification is unavailable; try again later') from exc
    record=await db.scalar(select(User).where(User.id==user.id).with_for_update().execution_options(populate_existing=True))
    if record is None or record.status!='active':raise HTTPException(401,'Account is unavailable')
    try:matches=canonical_mobile(record.mobile)==verified_mobile
    except InvalidWidgetVerification:matches=False
    if not matches:raise HTTPException(400,'Verify the mobile number currently saved on your account')
    digest=hash_token(payload.verification_token)
    await acquire_idempotency_lock(db,'phone-widget-mobile:'+verified_mobile)
    await acquire_idempotency_lock(db,'phone-widget-proof:'+digest)
    used=await db.scalar(select(AccountVerification).where(AccountVerification.channel=='msg91_widget',AccountVerification.code_hash==digest))
    if used:raise HTTPException(409,'Phone verification proof was already used; start again')
    variants={verified_mobile,verified_mobile.lstrip('+')}
    if verified_mobile.startswith('+91') and len(verified_mobile)==13:variants.add(verified_mobile[3:])
    duplicate=await db.scalar(select(User.id).where(User.id!=record.id,User.mobile_verified.is_(True),User.mobile.in_(variants)))
    if duplicate:raise HTTPException(409,'This phone cannot be verified on this account')
    now=datetime.now(UTC)
    record.mobile=verified_mobile;record.mobile_verified=True
    db.add(AccountVerification(user_id=record.id,channel='msg91_widget',code_hash=digest,attempts=0,expires_at=now,used_at=now))
    db.add(AuditLog(actor_id=record.id,action='auth.mobile_verified',entity_type='user',entity_id=record.id,after={'method':'msg91_widget','mobile_verified':True},request_id=getattr(request.state,'request_id',None)))
    await db.commit()
    # No session/role elevation: this is phone ownership, not KYC or login.
    return {'mobile_verified':True}
