from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DriverProfile, ProviderProfile


async def require_verified_driver_identity(db: AsyncSession, driver: DriverProfile) -> None:
    """New operations use authoritative KYC, not stale linked-profile flags.

    Do not call this for existing trip updates; a re-verification rollout must
    not strand cargo already in transit.
    """
    identity = await db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == driver.user_id, ProviderProfile.provider_type == 'driver').with_for_update()) if driver.user_id else None
    if identity is None or not identity.active or identity.kyc_status != 'verified':
        raise HTTPException(409, 'Driver identity re-verification is required before new operations')
