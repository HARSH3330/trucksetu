"""Public account recovery and verification delivery; privileged recovery stays separate."""
import secrets
from datetime import UTC,datetime,timedelta
from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,EmailStr,Field,field_validator
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import SignupInput,current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import enforce_rate_limit
from app.core.routing import AuthenticationFirstRoute
from app.core.security import generate_otp,get_password_hash,hash_otp,hash_token,token_hash_matches,verify_password
from app.models import AccountVerification,AuditLog,RefreshSession,User
from app.services.communications import ChannelProvider
from app.services.dependencies import get_account_email_delivery
from app.services.msg91_widget import InvalidWidgetVerification,canonical_mobile

router=APIRouter(route_class=AuthenticationFirstRoute,prefix='/api/v1/auth',tags=['account recovery'])
REQUESTED={'status':'requested','message':'If the account is eligible and email delivery is available, check your inbox. Delivery is not confirmed.'}


class EmailInput(BaseModel):
    email:EmailStr


class PasswordResetInput(EmailInput):
    token:str=Field(min_length=32,max_length=128,pattern=r'^[A-Za-z0-9_-]+$')
    password:str=Field(min_length=10,max_length=72)
    @field_validator('password')
    @classmethod
    def strength(cls,value:str)->str:
        return SignupInput.validate_password_strength(value)


class MobileInput(BaseModel):
    mobile:str=Field(max_length=20,pattern=r'^\+?[1-9]\d{7,14}$')
    password:str=Field(min_length=1,max_length=72)
    @field_validator('mobile')
    @classmethod
    def normalize_mobile(cls,value:str)->str:
        return canonical_mobile(value)


@router.patch('/mobile')
async def update_mobile(payload:MobileInput,request:Request,user:User=Depends(current_user),db:AsyncSession=Depends(get_db))->dict[str,bool]:
    await enforce_rate_limit(request,'account-mobile',settings.VERIFICATION_RATE_LIMIT,600,str(user.id))
    record=await db.scalar(select(User).where(User.id==user.id).with_for_update().execution_options(populate_existing=True))
    if record is None or record.status!='active' or not verify_password(payload.password,record.password_hash):
        raise HTTPException(401,'Account update authorization failed')
    try:changed=canonical_mobile(record.mobile)!=payload.mobile
    except InvalidWidgetVerification:changed=True
    record.mobile=payload.mobile
    if changed:record.mobile_verified=False
    db.add(AuditLog(actor_id=record.id,action='auth.mobile_updated',entity_type='user',entity_id=record.id,after={'mobile_changed':changed,'mobile_verified':bool(record.mobile_verified)}))
    await db.commit()
    return {'updated':True,'mobile_verified':bool(record.mobile_verified)}


def eligible(user:User|None)->bool:
    return bool(user and user.status=='active' and not any(role.role in {'admin','superadmin'} for role in user.roles))


async def request_code(email:str,channel:str,db:AsyncSession,sender:ChannelProvider)->dict[str,str]:
    user=await db.scalar(select(User).options(selectinload(User.roles)).where(User.email==email.lower()).with_for_update())
    if not eligible(user) or (channel=='email' and user.email_verified):
        return REQUESTED
    code=generate_otp() if channel=='email' else secrets.token_urlsafe(32)
    purpose='email verification code' if channel=='email' else 'password reset token'
    try:
        receipt=await sender.send(user.email,f'TransivoX {purpose}: {code}\nExpires in {settings.OTP_EXPIRE_MINUTES} minutes. Do not share this with anyone. If you did not request this, ignore this email.')
        if not receipt:raise RuntimeError('No account delivery acknowledgement')
    except Exception:
        # Preserve the same public response for unknown/eligible/delivery-error
        # accounts. No raw provider diagnostics, email body or token is logged.
        db.add(AuditLog(actor_id=user.id,action='auth.account_email_unacknowledged',entity_type='user',entity_id=user.id,after={'channel':channel}))
        await db.commit()
        return REQUESTED
    now=datetime.now(UTC)
    await db.execute(update(AccountVerification).where(AccountVerification.user_id==user.id,AccountVerification.channel==channel,AccountVerification.used_at.is_(None)).values(expires_at=now))
    db.add(AccountVerification(user_id=user.id,channel=channel,code_hash=hash_otp(code) if channel=='email' else hash_token(code),expires_at=now+timedelta(minutes=settings.OTP_EXPIRE_MINUTES)))
    db.add(AuditLog(actor_id=user.id,action='auth.account_email_accepted',entity_type='user',entity_id=user.id,after={'channel':channel}))
    await db.commit()
    return REQUESTED


@router.post('/password-reset/request',status_code=202)
async def request_reset(payload:EmailInput,request:Request,db:AsyncSession=Depends(get_db),sender:Annotated[ChannelProvider,Depends(get_account_email_delivery)]=None)->dict[str,str]:
    await enforce_rate_limit(request,'password-reset-request',settings.VERIFICATION_RATE_LIMIT,600,str(payload.email))
    return await request_code(str(payload.email),'password_reset',db,sender)


@router.post('/verification/resend',status_code=202)
async def resend_verification(payload:EmailInput,request:Request,db:AsyncSession=Depends(get_db),sender:Annotated[ChannelProvider,Depends(get_account_email_delivery)]=None)->dict[str,str]:
    await enforce_rate_limit(request,'verification-resend',settings.VERIFICATION_RATE_LIMIT,600,str(payload.email))
    return await request_code(str(payload.email),'email',db,sender)


@router.post('/password-reset/confirm')
async def confirm_reset(payload:PasswordResetInput,request:Request,db:AsyncSession=Depends(get_db))->dict[str,str]:
    await enforce_rate_limit(request,'password-reset-confirm',settings.VERIFICATION_RATE_LIMIT,600,str(payload.email))
    user=await db.scalar(select(User).options(selectinload(User.roles)).where(User.email==str(payload.email).lower()).with_for_update())
    if not eligible(user):raise HTTPException(400,'Invalid or expired password reset token')
    item=await db.scalar(select(AccountVerification).where(AccountVerification.user_id==user.id,AccountVerification.channel=='password_reset',AccountVerification.used_at.is_(None)).order_by(AccountVerification.created_at.desc()).limit(1).with_for_update())
    now=datetime.now(UTC)
    if item is None or item.used_at is not None or item.expires_at<=now or item.attempts>=settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(400,'Invalid or expired password reset token')
    item.attempts+=1
    if not token_hash_matches(payload.token,item.code_hash):
        await db.commit()
        raise HTTPException(400,'Invalid or expired password reset token')
    item.used_at=now
    user.password_hash=get_password_hash(payload.password)
    user.auth_version=(user.auth_version or 0)+1
    user.failed_login_attempts=0;user.locked_until=None
    await db.execute(update(RefreshSession).where(RefreshSession.user_id==user.id,RefreshSession.revoked_at.is_(None)).values(revoked_at=now))
    db.add(AuditLog(actor_id=user.id,action='auth.password_reset',entity_type='user',entity_id=user.id,after={'sessions_revoked':True}))
    await db.commit()
    return {'status':'password_reset'}
