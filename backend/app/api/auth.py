from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import acquire_idempotency_lock, get_db
from app.core.rate_limit import enforce_rate_limit
from app.core.security import create_access_token, create_refresh_token, generate_otp, get_password_hash, hash_otp, hash_token, token_hash_matches, verify_otp, verify_password, verify_token
from app.models import AccountVerification, AuditLog, RefreshSession, User, UserRole

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
PUBLIC_ROLES = {"customer", "provider", "fleet_owner", "driver"}


class SignupInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    mobile: str | None = Field(default=None, pattern=r"^\+?[1-9]\d{7,14}$")
    password: str = Field(min_length=10, max_length=72)
    role: str = "customer"

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(c.islower() for c in value) or not any(c.isupper() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must include uppercase, lowercase, and numeric characters")
        return value


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class RefreshInput(BaseModel):
    refresh_token: str


class VerifyInput(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")


class BootstrapAdminInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=14, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(c.islower() for c in value) or not any(c.isupper() for c in value) or not any(c.isdigit() for c in value) or not any(not c.isalnum() for c in value):
            raise ValueError("Admin password must include uppercase, lowercase, numeric, and special characters")
        return value


def public_user(user: User) -> dict[str, object]:
    return {"id": str(user.id), "full_name": user.full_name, "email": user.email, "mobile": user.mobile, "status": user.status, "email_verified": user.email_verified, "roles": [r.role for r in user.roles]}


async def issue_session(user: User, request: Request, db: AsyncSession, family_id: str | None = None) -> dict[str, object]:
    jti, family = str(uuid.uuid4()), family_id or str(uuid.uuid4())
    refresh = create_refresh_token(str(user.id), jti, family)
    db.add(RefreshSession(user_id=user.id, jti=jti, family_id=family, token_hash=hash_token(refresh), user_agent=request.headers.get("user-agent", "")[:300], ip_address=request.client.host if request.client else None, expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)))
    roles = [r.role for r in user.roles]
    return {"access_token": create_access_token({"sub": str(user.id), "roles": roles}), "refresh_token": refresh, "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "user": public_user(user)}


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupInput, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    await enforce_rate_limit(request, "signup", settings.SIGNUP_RATE_LIMIT, 3600, payload.email)
    role = payload.role.lower()
    if role not in PUBLIC_ROLES:
        raise HTTPException(400, "This role cannot be self-assigned")
    email = payload.email.lower()
    if await db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, "An account already exists for this email")
    user = User(full_name=payload.full_name.strip(), email=email, mobile=payload.mobile, password_hash=get_password_hash(payload.password))
    user.roles.append(UserRole(role=role)); db.add(user); await db.flush()
    code = generate_otp()
    db.add(AccountVerification(user_id=user.id, channel="email", code_hash=hash_otp(code), expires_at=datetime.now(UTC) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)))
    result = await issue_session(user, request, db)
    result["verification_required"] = True
    if settings.is_development:
        result["development_verification_code"] = code
    return result


@router.post("/bootstrap-admin", status_code=status.HTTP_201_CREATED)
async def bootstrap_admin(
    payload: BootstrapAdminInput,
    request: Request,
    bootstrap_token: Annotated[str | None, Header(alias="X-Bootstrap-Token")] = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Create exactly one initial superadmin using a temporary deployment secret."""
    await enforce_rate_limit(request, "bootstrap-admin", 5, 3600)
    configured_token = settings.ADMIN_BOOTSTRAP_TOKEN
    if not configured_token:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Admin bootstrap is disabled")
    if not settings.admin_bootstrap_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Admin bootstrap token must contain at least 32 characters")
    if not bootstrap_token or not secrets.compare_digest(bootstrap_token, configured_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin bootstrap authorization failed")

    # The transaction-level lock makes the check-and-create operation safe when
    # two serverless instances receive a bootstrap request simultaneously.
    await acquire_idempotency_lock(db, "transivox:first-superadmin")
    privileged_user_id = await db.scalar(
        select(UserRole.user_id).where(UserRole.role.in_({"admin", "superadmin"})).limit(1)
    )
    if privileged_user_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "The first administrator has already been created")

    email = payload.email.lower()
    if await db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Use an email address that is not registered")

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=get_password_hash(payload.password),
        email_verified=True,
    )
    user.roles.append(UserRole(role="superadmin"))
    db.add(user)
    await db.flush()
    db.add(AuditLog(
        action="auth.first_superadmin_created",
        entity_type="user",
        entity_id=user.id,
        after={"email": email, "role": "superadmin"},
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
    ))
    return {"created": True, "email": email, "role": "superadmin", "next_step": "Remove ADMIN_BOOTSTRAP_TOKEN and redeploy the API"}


@router.post("/login")
async def login(payload: LoginInput, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    await enforce_rate_limit(request, "login", settings.LOGIN_RATE_LIMIT, 900, payload.email)
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    now = datetime.now(UTC)
    if not user or not verify_password(payload.password, user.password_hash):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5: user.locked_until = now + timedelta(minutes=15)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user.status != "active" or (user.locked_until and user.locked_until > now):
        raise HTTPException(status.HTTP_423_LOCKED, "Account is temporarily unavailable")
    user.failed_login_attempts = 0; user.locked_until = None; user.last_login_at = now
    return await issue_session(user, request, db)


@router.post("/refresh")
async def refresh(payload: RefreshInput, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    await enforce_rate_limit(request, "refresh", settings.REFRESH_RATE_LIMIT, 60)
    try: claims = verify_token(payload.refresh_token, "refresh")
    except JWTError as exc: raise HTTPException(401, "Invalid refresh token") from exc
    session = await db.scalar(select(RefreshSession).where(RefreshSession.jti == claims.get("jti")).with_for_update())
    now = datetime.now(UTC)
    claims_match = bool(session and claims.get("sub") == str(session.user_id) and claims.get("family") == session.family_id)
    if not session or session.revoked_at or session.expires_at <= now or not claims_match or not token_hash_matches(payload.refresh_token, session.token_hash):
        if session: await db.execute(update(RefreshSession).where(RefreshSession.family_id == session.family_id).values(revoked_at=now))
        raise HTTPException(401, "Refresh session is no longer valid")
    user = await db.get(User, session.user_id)
    if not user or user.status != "active": raise HTTPException(401, "Account is unavailable")
    session.revoked_at = now
    result = await issue_session(user, request, db, session.family_id)
    session.replaced_by_jti = verify_token(str(result["refresh_token"]), "refresh")["jti"]
    return result


@router.post("/verify-email")
async def verify_email(payload: VerifyInput, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    await enforce_rate_limit(request, "verify-email", settings.VERIFICATION_RATE_LIMIT, 600, payload.email)
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user: raise HTTPException(400, "Invalid or expired verification code")
    item = await db.scalar(select(AccountVerification).where(AccountVerification.user_id == user.id, AccountVerification.channel == "email", AccountVerification.used_at.is_(None)).order_by(AccountVerification.created_at.desc()).with_for_update())
    if not item or item.expires_at <= datetime.now(UTC) or item.attempts >= settings.OTP_MAX_ATTEMPTS: raise HTTPException(400, "Invalid or expired verification code")
    item.attempts += 1
    if not verify_otp(payload.code, item.code_hash): raise HTTPException(400, "Invalid or expired verification code")
    item.used_at = datetime.now(UTC); user.email_verified = True
    return {"verified": True}


async def current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)) -> User:
    try: claims = verify_token(token, "access"); user_id = uuid.UUID(claims["sub"])
    except (JWTError, KeyError, ValueError) as exc: raise HTTPException(401, "Invalid access token", headers={"WWW-Authenticate": "Bearer"}) from exc
    user = await db.get(User, user_id)
    if not user or user.status != "active": raise HTTPException(401, "Account is unavailable")
    return user


def require_roles(*allowed: str):
    async def dependency(user: Annotated[User, Depends(current_user)]) -> User:
        if not ({r.role for r in user.roles} & set(allowed)): raise HTTPException(403, "Insufficient permissions")
        return user
    return dependency


@router.get("/me")
async def me(user: Annotated[User, Depends(current_user)]) -> dict[str, object]: return public_user(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshInput, db: AsyncSession = Depends(get_db)) -> None:
    try: claims = verify_token(payload.refresh_token, "refresh")
    except JWTError: return
    session = await db.scalar(select(RefreshSession).where(RefreshSession.jti == claims.get("jti")).with_for_update())
    if session and not session.revoked_at and claims.get("sub") == str(session.user_id) and claims.get("family") == session.family_id and token_hash_matches(payload.refresh_token, session.token_hash):
        session.revoked_at = datetime.now(UTC)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(user: Annotated[User, Depends(current_user)], db: AsyncSession = Depends(get_db)) -> None:
    await db.execute(update(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None)).values(revoked_at=datetime.now(UTC)))
