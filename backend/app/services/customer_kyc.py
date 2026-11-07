"""Configured customer document policy and server-side publication eligibility."""
from fastapi import HTTPException
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.models import CustomerKYCApplication, CustomerKYCDocument, AuditLog
from app.services.dependencies import get_private_document_storage

ALLOWED_DOCUMENTS={'aadhaar','pan'} # Extend only with an approved collection/expiry policy.


def customer_consent_policy():
    import hashlib
    text=settings.CUSTOMER_KYC_CONSENT_TEXT.strip()
    if not 20<=len(text)<=8000:
        raise HTTPException(503,'Customer verification consent is awaiting approved setup')
    return {'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}


async def application_consent(db,item):
    value=await db.scalar(select(AuditLog.after).where(AuditLog.entity_id==item.id,AuditLog.action=='customer_kyc.consent_recorded').order_by(AuditLog.created_at.desc()).limit(1))
    return value if isinstance(value,dict) else {}


def customer_document_policy():
    documents={s.strip() for s in settings.CUSTOMER_KYC_REQUIRED_DOCUMENTS.split(',') if s.strip()}
    if not documents or not documents.issubset(ALLOWED_DOCUMENTS) or not settings.CUSTOMER_KYC_POLICY_VERSION:
        raise HTTPException(503,'Customer verification requirements are awaiting approved setup')
    customer_consent_policy()
    return settings.CUSTOMER_KYC_POLICY_VERSION,sorted(documents)


async def current_application(db,user_id,lock=False):
    query=select(CustomerKYCApplication).where(CustomerKYCApplication.user_id==user_id).order_by(CustomerKYCApplication.created_at.desc(),CustomerKYCApplication.id.desc()).limit(1)
    return await db.scalar(query.with_for_update() if lock else query)


async def clean_document(storage,document):
    try:
        await run_in_threadpool(storage.require_clean_scan,document.storage_key,document.storage_version_id)
    except ValueError as exc:
        raise HTTPException(409,'Document scan is pending or was not clean') from exc
    except Exception as exc:
        raise HTTPException(503,'Document scan could not be verified') from exc


async def require_customer_kyc(db,user):
    if settings.APP_ENV=='test' and settings.CUSTOMER_KYC_TEST_SIMULATION:
        return # Explicit local simulation; never a production permission.
    version,required=customer_document_policy()
    item=await current_application(db,user.id,lock=True)
    if not item or item.status!='verified' or item.policy_version!=version or sorted(item.required_documents)!=required:
        raise HTTPException(403,'Complete customer document verification before publishing')
    consent=await application_consent(db,item)
    if consent.get('consent_sha256')!=customer_consent_policy()['sha256']:
        raise HTTPException(403,'Review the current customer document consent before publishing')
    documents=list(await db.scalars(select(CustomerKYCDocument).where(CustomerKYCDocument.application_id==item.id,CustomerKYCDocument.status=='accepted')))
    if set(required)!={d.document_type for d in documents}:
        raise HTTPException(403,'Current accepted customer documents are required')
    try:
        storage=get_private_document_storage()
    except Exception as exc:
        raise HTTPException(503,'Customer verification is unavailable') from exc
    for document in documents:
        await clean_document(storage,document)


def may_restart_application(existing,version,documents,consent_matches=True):
    return not existing or not consent_matches or existing.status in {'rejected','suspended'} or existing.policy_version!=version or sorted(existing.required_documents)!=sorted(documents)
