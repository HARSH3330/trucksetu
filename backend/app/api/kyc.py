from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.auth import current_user, require_roles
from app.core.database import get_db
from app.models import AuditLog, KYCApplication, KYCDocument, KYCReviewEvent, ProviderProfile, User
from app.services.storage import PrivateDocumentStorage

router = APIRouter(prefix="/api/v1/kyc", tags=["provider verification"])
DOCUMENT_TYPES = {"aadhaar", "pan", "driving_licence", "vehicle_rc", "vehicle_insurance", "fitness_certificate", "commercial_permit", "pollution_certificate", "bank_proof", "gst_certificate"}
REQUIRED = {
    "driver": {"aadhaar", "pan", "driving_licence"},
    "owner": {"aadhaar", "pan", "vehicle_rc"},
    "fleet": {"pan", "vehicle_rc", "gst_certificate"},
    "company": {"pan", "vehicle_rc", "gst_certificate"},
}
ALLOWED_BY_TYPE = {
    "driver": {"aadhaar", "pan", "driving_licence", "bank_proof"},
    "owner": {"aadhaar", "pan", "driving_licence", "vehicle_rc", "vehicle_insurance", "fitness_certificate", "commercial_permit", "pollution_certificate", "bank_proof"},
    "fleet": DOCUMENT_TYPES,
    "company": DOCUMENT_TYPES,
}


class ApplicationInput(BaseModel):
    legal_name: str = Field(min_length=2, max_length=160)
    provider_type: Literal["driver", "owner", "fleet", "company"] = "driver"
    pan_last_four: str | None = Field(default=None, pattern=r"^[A-Z0-9]{4}$")
    gstin: str | None = Field(default=None, pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$")


class UploadRequest(BaseModel):
    document_type: str
    filename: str = Field(min_length=1, max_length=255)
    content_type: str


class CompleteUpload(BaseModel):
    document_type: str
    storage_key: str = Field(max_length=500)
    original_filename: str = Field(max_length=255)
    content_type: str
    expires_on: date | None = None


class ReviewInput(BaseModel):
    decision: Literal["verified", "rejected", "resubmit_required", "suspended"]
    reason: str = Field(min_length=5, max_length=2000)
    document_decisions: dict[str, Literal["accepted", "rejected"]] = Field(default_factory=dict)


async def own_application(user: User, db: AsyncSession) -> tuple[ProviderProfile, KYCApplication | None]:
    provider = await db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user.id))
    if not provider: raise HTTPException(404, "Provider profile not found")
    return provider, await db.scalar(select(KYCApplication).where(KYCApplication.provider_id == provider.id).order_by(KYCApplication.created_at.desc()))


def view(item: KYCApplication, provider: ProviderProfile | None = None) -> dict[str, object]:
    return {"id": str(item.id), "provider_id": str(item.provider_id), "provider_name": provider.display_name if provider else None,
            "provider_type": provider.provider_type if provider else None, "status": item.status,
            "legal_name": item.legal_name, "submitted_at": item.submitted_at,
            "decision_reason": item.decision_reason,
            "documents": [{"id": str(d.id), "type": d.document_type, "filename": d.original_filename,
                           "status": d.status, "expires_on": d.expires_on} for d in item.documents]}


@router.post("/applications", status_code=status.HTTP_201_CREATED)
async def create_application(payload: ApplicationInput, user: Annotated[User, Depends(require_roles("provider", "fleet_owner", "driver"))], db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    roles = {role.role for role in user.roles}
    allowed_types = {"driver"} if "driver" in roles else {"owner", "fleet", "company"} if "fleet_owner" in roles else {"owner", "company"}
    if payload.provider_type not in allowed_types:
        raise HTTPException(403, "This verification type does not match your account role")
    provider = await db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user.id))
    if not provider:
        provider = ProviderProfile(user_id=user.id, display_name=user.full_name, provider_type=payload.provider_type); db.add(provider); await db.flush()
    else:
        provider.provider_type = payload.provider_type
    existing = await db.scalar(select(KYCApplication).where(KYCApplication.provider_id == provider.id, KYCApplication.status.in_({"registered", "documents_submitted", "under_review", "resubmit_required"})))
    if existing: raise HTTPException(409, "An active verification application already exists")
    item = KYCApplication(provider_id=provider.id, legal_name=payload.legal_name, pan_last_four=payload.pan_last_four, gstin=payload.gstin); db.add(item); await db.flush()
    return view(item, provider)


@router.get("/applications/me")
async def my_application(user: Annotated[User, Depends(current_user)], db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    provider, item = await own_application(user, db)
    if not item: raise HTTPException(404, "Verification application not found")
    return view(item, provider)


@router.post("/uploads")
async def prepare_upload(payload: UploadRequest, user: Annotated[User, Depends(current_user)], db: AsyncSession = Depends(get_db)) -> dict[str, str | int]:
    provider, item = await own_application(user, db)
    if not item or item.status not in {"registered", "resubmit_required"}: raise HTTPException(409, "Documents cannot be changed at this stage")
    if payload.document_type not in ALLOWED_BY_TYPE.get(provider.provider_type, set()): raise HTTPException(422, "Document type is not allowed for this verification profile")
    try: key, url = await run_in_threadpool(PrivateDocumentStorage().upload_url, provider.id, payload.document_type, payload.filename, payload.content_type)
    except (RuntimeError, ValueError) as exc: raise HTTPException(503 if isinstance(exc, RuntimeError) else 422, str(exc)) from exc
    return {"storage_key": key, "upload_url": url, "expires_in": 600}


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def complete_upload(payload: CompleteUpload, user: Annotated[User, Depends(current_user)], db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    provider, item = await own_application(user, db)
    if not item or item.status not in {"registered", "resubmit_required"}: raise HTTPException(409, "Documents cannot be changed at this stage")
    expected_prefix = f"kyc/{provider.id}/{payload.document_type}/"
    if payload.document_type not in ALLOWED_BY_TYPE.get(provider.provider_type, set()) or not payload.storage_key.startswith(expected_prefix): raise HTTPException(422, "Invalid document reference")
    try:
        storage = PrivateDocumentStorage()
        metadata = await run_in_threadpool(storage.confirm, payload.storage_key)
        detected_type = await run_in_threadpool(storage.detected_content_type, payload.storage_key)
    except Exception as exc: raise HTTPException(422, "Uploaded document could not be confirmed") from exc
    size = int(metadata.get("ContentLength", 0)); content_type = str(metadata.get("ContentType", payload.content_type))
    if detected_type is None or content_type != detected_type or payload.content_type != detected_type: raise HTTPException(422, "Document content does not match its declared type")
    if size <= 0 or size > 10 * 1024 * 1024: raise HTTPException(422, "Document must be between 1 byte and 10 MB")
    existing = await db.scalar(select(KYCDocument.id).where(KYCDocument.application_id == item.id, KYCDocument.document_type == payload.document_type, KYCDocument.status != "rejected"))
    if existing: raise HTTPException(409, "This document type is already uploaded; remove or reject it before replacing")
    document = KYCDocument(application_id=item.id, document_type=payload.document_type, storage_key=payload.storage_key, original_filename=payload.original_filename, content_type=content_type, size_bytes=size, expires_on=payload.expires_on); db.add(document); await db.flush()
    return {"id": str(document.id), "status": "uploaded"}


@router.post("/applications/{application_id}/submit")
async def submit(application_id: uuid.UUID, user: Annotated[User, Depends(current_user)], db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    provider, item = await own_application(user, db)
    if not item or item.id != application_id or item.status not in {"registered", "resubmit_required"}: raise HTTPException(409, "Application cannot be submitted")
    present = {d.document_type for d in item.documents if d.status != "rejected"}
    missing = REQUIRED.get(provider.provider_type, REQUIRED["driver"]) - present
    if missing: raise HTTPException(422, {"message": "Required documents are missing", "missing": sorted(missing)})
    item.status = "under_review"; item.submitted_at = datetime.now(UTC); provider.kyc_status = "under_review"
    return view(item, provider)


@router.get("/admin/applications")
async def queue(filter_status: str = Query(default="under_review", alias="status"), _: User = Depends(require_roles("admin", "superadmin")), db: AsyncSession = Depends(get_db)) -> list[dict[str, object]]:
    items = list(await db.scalars(select(KYCApplication).where(KYCApplication.status == filter_status).order_by(KYCApplication.submitted_at)))
    providers = {provider.id: provider for provider in await db.scalars(select(ProviderProfile).where(ProviderProfile.id.in_([item.provider_id for item in items])))} if items else {}
    return [view(item, providers.get(item.provider_id)) for item in items]


@router.post("/admin/applications/{application_id}/review")
async def review(application_id: uuid.UUID, payload: ReviewInput, admin: Annotated[User, Depends(require_roles("admin", "superadmin"))], db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    item = await db.scalar(select(KYCApplication).where(KYCApplication.id == application_id).with_for_update())
    if not item or item.status not in {"under_review", "verified"}: raise HTTPException(409, "Application is not reviewable")
    previous = item.status; item.status = payload.decision; item.reviewed_at = datetime.now(UTC); item.reviewed_by = admin.id; item.decision_reason = payload.reason
    provider = await db.get(ProviderProfile, item.provider_id)
    if not provider: raise HTTPException(404, "Provider profile not found")
    if payload.decision == "verified":
        required = REQUIRED.get(provider.provider_type, REQUIRED["driver"])
        documents = {document.document_type: document for document in item.documents}
        unacceptable = sorted(document_type for document_type in required if document_type not in documents or payload.document_decisions.get(document_type) != "accepted" or (documents[document_type].expires_on and documents[document_type].expires_on < date.today()))
        if unacceptable:
            raise HTTPException(422, {"message": "Required documents must be accepted and current", "documents": unacceptable})
    provider.kyc_status = payload.decision; provider.active = payload.decision != "suspended"
    for document in item.documents:
        if document.document_type in payload.document_decisions:
            document.status = payload.document_decisions[document.document_type]
            document.rejection_reason = payload.reason if document.status == "rejected" else None
    db.add(KYCReviewEvent(application_id=item.id, actor_id=admin.id, previous_status=previous, new_status=payload.decision, reason=payload.reason, document_decisions=payload.document_decisions))
    return view(item, provider)


@router.get("/documents/{document_id}/download")
async def download(document_id: uuid.UUID, user: Annotated[User, Depends(current_user)], db: AsyncSession = Depends(get_db)) -> dict[str, str | int]:
    document = await db.get(KYCDocument, document_id)
    if not document: raise HTTPException(404, "Document not found")
    item = await db.get(KYCApplication, document.application_id)
    if not item: raise HTTPException(404, "Verification application not found")
    provider = await db.get(ProviderProfile, item.provider_id)
    if not provider: raise HTTPException(404, "Provider profile not found")
    roles = {r.role for r in user.roles}
    if provider.user_id != user.id and not roles.intersection({"admin", "superadmin"}): raise HTTPException(403, "Document access denied")
    try: url = await run_in_threadpool(PrivateDocumentStorage().download_url, document.storage_key)
    except RuntimeError as exc: raise HTTPException(503, str(exc)) from exc
    db.add(AuditLog(actor_id=user.id, action="kyc.document_downloaded", entity_type="kyc_document", entity_id=document.id, after={"owner_access": provider.user_id == user.id}))
    return {"download_url": url, "expires_in": 300}


@router.get("/admin/expiring-documents")
async def expiring_documents(days: int = Query(default=30, ge=1, le=180), _: User = Depends(require_roles("admin", "superadmin")), db: AsyncSession = Depends(get_db)) -> list[dict[str, object]]:
    cutoff = date.today() + timedelta(days=days)
    documents = list(await db.scalars(select(KYCDocument).where(KYCDocument.expires_on.is_not(None), KYCDocument.expires_on <= cutoff).order_by(KYCDocument.expires_on)))
    return [{"id": str(d.id), "type": d.document_type, "expires_on": d.expires_on, "status": "expired" if d.expires_on and d.expires_on < date.today() else "expiring"} for d in documents]
