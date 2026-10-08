from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_user
from app.core.database import get_db
from app.models import AuditLog, TermsAcceptance, User

TERMS_VERSION = "2026-10-08-draft-v1"
TERMS_CONTENT = (Path(__file__).parents[1] / "legal" / "terms-v1.txt").read_text(encoding="utf-8")
TERMS_HASH = hashlib.sha256(TERMS_CONTENT.encode()).hexdigest()
router = APIRouter(prefix="/api/v1/legal", tags=["legal consent"])


class AcceptanceInput(BaseModel):
    version: str = Field(min_length=1, max_length=80)
    accepted: Literal[True]


async def require_terms(db: AsyncSession, user_id: uuid.UUID) -> TermsAcceptance:
    acceptance = await db.scalar(select(TermsAcceptance).where(
        TermsAcceptance.user_id == user_id, TermsAcceptance.version == TERMS_VERSION,
        TermsAcceptance.content_sha256 == TERMS_HASH,
    ))
    if acceptance is None:
        raise HTTPException(409, {"code": "terms_acceptance_required", "message": "Accept the current Terms & Conditions before booking."})
    return acceptance


@router.get("/terms")
async def terms() -> dict[str, str]:
    return {"version": TERMS_VERSION, "content": TERMS_CONTENT, "status": "draft_pending_legal_review"}


@router.get("/terms/acceptance")
async def acceptance_status(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)) -> dict[str, object]:
    try:
        item = await require_terms(db, user.id)
    except HTTPException:
        return {"version": TERMS_VERSION, "accepted": False}
    return {"version": TERMS_VERSION, "accepted": True, "accepted_at": item.accepted_at}


@router.post("/terms/acceptance")
async def accept_terms(payload: AcceptanceInput, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)) -> dict[str, object]:
    if payload.version != TERMS_VERSION:
        raise HTTPException(409, "The Terms have changed. Please review the current version.")
    # Serialize acceptance for this account to make duplicate submissions idempotent.
    await db.scalar(select(User).where(User.id == user.id).with_for_update())
    existing = await db.scalar(select(TermsAcceptance).where(TermsAcceptance.user_id == user.id, TermsAcceptance.version == TERMS_VERSION))
    if existing is None:
        item = TermsAcceptance(user_id=user.id, version=TERMS_VERSION, content_sha256=TERMS_HASH)
        db.add(item)
        await db.flush()
        db.add(AuditLog(actor_id=user.id, action="legal.terms_accepted", entity_type="terms_acceptance", entity_id=item.id, after={"version": TERMS_VERSION, "content_sha256": TERMS_HASH}))
    elif existing.content_sha256 != TERMS_HASH:
        raise HTTPException(409, "Terms content changed without a new version. Contact support.")
    return {"version": TERMS_VERSION, "accepted": True}
