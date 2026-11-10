"""Verify a promised contact before checkout; numbers never enter public snapshots."""
import hashlib
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select

from app.models import DriverProfile, ProviderProfile, Quote, User
from app.services.driver_eligibility import require_verified_driver_identity


@dataclass(frozen=True)
class ContactProof:
    kind: str
    user_id: object
    phone: str
    name: str
    email: str = ''
    phone_verified: bool = False

    @property
    def phone_hash(self):
        return hashlib.sha256(self.phone.encode()).hexdigest()


async def verified_contact(db, provider_id, kind, driver_id=None, through=None):
    provider = await db.get(ProviderProfile,provider_id)
    if not provider or not provider.active or provider.kyc_status != 'verified':
        raise HTTPException(409,'Provider verification must be current before checkout')
    account_id,name = provider.user_id,provider.display_name
    if kind == 'driver':
        driver = await db.get(DriverProfile,driver_id) if driver_id else None
        if not driver or driver.provider_id != provider_id or not driver.active or driver.kyc_status != 'verified' or not driver.licence_expires_on or (through and driver.licence_expires_on < through):
            raise HTTPException(409,'The promised verified driver must be available before checkout')
        await require_verified_driver_identity(db,driver)
        account_id,name = driver.user_id,driver.full_name
    elif kind != 'provider':
        raise HTTPException(409,'Choose a verified provider or assigned-driver contact')
    account = await db.scalar(select(User).where(User.id == account_id).with_for_update()) if account_id else None
    if not account or account.status != 'active':
        raise HTTPException(409,'The promised contact account is unavailable')
    if not account.mobile:
        raise HTTPException(409,'Add a phone number to the promised contact account before bidding')
    # Owner decision 2026-11-10: a verified email is enough until SMS verification is live;
    # the customer is told whether the phone itself was verified.
    if not (account.mobile_verified or account.email_verified):
        raise HTTPException(409,'Verify your email or phone on the promised contact account before bidding')
    return ContactProof(kind,account.id,account.mobile,name,account.email if account.email_verified else '',bool(account.mobile_verified))


async def selected_contact(db,selection):
    quote = await db.get(Quote,selection.quote_id)
    try:
        proof = await verified_contact(db,quote.provider_id,selection.contact_kind,selection.driver_id,quote.estimated_delivery.date())
        if proof.user_id != selection.contact_user_id or proof.phone_hash != selection.contact_phone_hash:
            return None
        return proof
    except HTTPException:
        return None
