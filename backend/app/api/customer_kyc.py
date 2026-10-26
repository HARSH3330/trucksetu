"""Customer submission/review: scan-clean permits review, never automatic approval."""
import uuid
from datetime import UTC,datetime
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from app.api.auth import require_roles
from app.core.database import get_db
from app.core.routing import AuthenticationFirstRoute
from app.models import CustomerKYCApplication,CustomerKYCDocument,AuditLog,User
from app.services.dependencies import get_private_document_storage
from app.services.customer_kyc import customer_document_policy,current_application,clean_document,may_restart_application,customer_consent_policy,application_consent

router=APIRouter(prefix='/api/v1/customer-kyc',tags=['customer verification'],route_class=AuthenticationFirstRoute)
customer=require_roles('customer')
admin=require_roles('admin','superadmin')


class Start(BaseModel):
    consent_version: str=Field(min_length=1,max_length=80)
    consent_sha256: str=Field(pattern=r"^[0-9a-f]{64}$")


class Upload(BaseModel):
    document_type: str=Field(max_length=50)
    filename: str=Field(min_length=1,max_length=255)
    content_type: Literal['application/pdf','image/png','image/jpeg']


class Complete(Upload):
    storage_key: str=Field(min_length=1,max_length=500)


class Review(BaseModel):
    decision: Literal['verified','rejected','resubmit_required','suspended']
    reason: str=Field(min_length=10,max_length=2000)
    document_decisions: dict[uuid.UUID,Literal['accepted','rejected']]=Field(default_factory=dict)


def audit(db,actor,action,item,after):
    db.add(AuditLog(actor_id=actor,action='customer_kyc.'+action,entity_type='customer_kyc',entity_id=item.id,after=after))


async def view(db,item):
    docs=list(await db.scalars(select(CustomerKYCDocument).where(CustomerKYCDocument.application_id==item.id).order_by(CustomerKYCDocument.created_at)))
    consent=await application_consent(db,item)
    return dict(consent_sha256=consent.get("consent_sha256"),id=str(item.id),status=item.status,policy_version=item.policy_version,required_documents=item.required_documents,decision_reason=item.decision_reason,documents=[dict(id=str(d.id),type=d.document_type,status=d.status) for d in docs])


async def editable(db,user):
    item=await current_application(db,user.id,lock=True)
    if not item or item.status not in {'registered','resubmit_required'}:
        raise HTTPException(409,'Customer verification documents cannot be changed at this stage')
    return item


@router.get('/policy')
async def policy(user=Depends(customer)):
    version,documents=customer_document_policy()
    consent=customer_consent_policy()
    return dict(version=version,required_documents=documents,consent_text=consent["text"],consent_sha256=consent["sha256"])


@router.get('/me')
async def me(db=Depends(get_db),user=Depends(customer)):
    item=await current_application(db,user.id)
    return await view(db,item) if item else None


@router.post('/applications',status_code=201)
async def start(payload:Start,db=Depends(get_db),user=Depends(customer)):
    version,documents=customer_document_policy()
    consent=customer_consent_policy()
    if payload.consent_version!=version or payload.consent_sha256!=consent['sha256']:
        raise HTTPException(409,'Review the current customer verification policy')
    await db.scalar(select(User).where(User.id==user.id).with_for_update())
    existing=await current_application(db,user.id)
    previous_consent=await application_consent(db,existing) if existing else {}
    if not may_restart_application(existing,version,documents,previous_consent.get('consent_sha256')==consent['sha256']):
        raise HTTPException(409,'A customer verification application already exists')
    if existing and existing.status not in {'rejected','suspended'}:
        existing.status='superseded'
        audit(db,user.id,'policy_superseded',existing,{'new_policy_version':version})
        await db.flush()
    item=CustomerKYCApplication(user_id=user.id,policy_version=version,required_documents=documents)
    db.add(item);await db.flush()
    audit(db,user.id,'consent_recorded',item,{'policy_version':version,'consent_sha256':consent['sha256'],'consent_text':consent['text']})
    await db.commit()
    return await view(db,item)


@router.post('/uploads')
async def upload(payload:Upload,db=Depends(get_db),user=Depends(customer),storage=Depends(get_private_document_storage)):
    item=await editable(db,user)
    if payload.document_type not in item.required_documents:
        raise HTTPException(422,'Document is not required by this application')
    key,url=await run_in_threadpool(storage.upload_url,item.id,payload.document_type,payload.filename,payload.content_type)
    return dict(storage_key=key,upload_url=url,expires_in=600)


@router.post('/documents',status_code=201)
async def complete(payload:Complete,db=Depends(get_db),user=Depends(customer),storage=Depends(get_private_document_storage)):
    item=await editable(db,user)
    if payload.document_type not in item.required_documents or not payload.storage_key.startswith(f'kyc/{item.id}/{payload.document_type}/'):
        raise HTTPException(422,'Invalid customer document reference')
    try:
        metadata=await run_in_threadpool(storage.confirm,payload.storage_key)
        version=metadata.get('VersionId')
        if not version or version=='null' or len(version)>255:
            raise HTTPException(503,'Immutable document version is required')
        candidate=CustomerKYCDocument(storage_key=payload.storage_key,storage_version_id=version)
        await clean_document(storage,candidate)
        detected=await run_in_threadpool(storage.detected_content_type,payload.storage_key,version)
        size=int(metadata.get('ContentLength',0))
        if not 0<size<=10*1024*1024 or detected!=payload.content_type or metadata.get('ContentType')!=detected:
            raise HTTPException(422,'Document size or content type is invalid')
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503,'Uploaded document could not be verified') from exc
    existing=await db.scalar(select(CustomerKYCDocument.id).where(CustomerKYCDocument.application_id==item.id,CustomerKYCDocument.document_type==payload.document_type,CustomerKYCDocument.status!='rejected'))
    if existing:
        raise HTTPException(409,'Reject the previous document before replacement')
    candidate.application_id=item.id;candidate.document_type=payload.document_type;candidate.content_type=detected;candidate.size_bytes=size
    db.add(candidate);await db.flush()
    audit(db,user.id,'document_registered',item,{'document_id':str(candidate.id),'type':payload.document_type})
    await db.commit()
    return await view(db,item)


@router.post('/submit')
async def submit(db=Depends(get_db),user=Depends(customer),storage=Depends(get_private_document_storage)):
    item=await editable(db,user)
    docs=list(await db.scalars(select(CustomerKYCDocument).where(CustomerKYCDocument.application_id==item.id,CustomerKYCDocument.status!='rejected')))
    if {d.document_type for d in docs}!=set(item.required_documents):
        raise HTTPException(422,'Required customer documents are missing')
    for document in docs:
        await clean_document(storage,document)
    item.status='under_review';audit(db,user.id,'submitted',item,{})
    await db.commit()
    return await view(db,item)


@router.get('/admin/applications')
async def queue(status: str=Query(default='under_review',max_length=30),offset:int=Query(default=0,ge=0),limit:int=Query(default=30,ge=1,le=100),db=Depends(get_db),user=Depends(admin)):
    items=list(await db.scalars(select(CustomerKYCApplication).where(CustomerKYCApplication.status==status).order_by(CustomerKYCApplication.created_at).offset(offset).limit(limit)))
    return [await view(db,item) for item in items]


@router.post('/admin/applications/{identity}/review')
async def review(identity:uuid.UUID,payload:Review,db=Depends(get_db),user=Depends(admin),storage=Depends(get_private_document_storage)):
    item=await db.scalar(select(CustomerKYCApplication).where(CustomerKYCApplication.id==identity).with_for_update())
    if not item or item.status not in {'under_review','verified'} or (item.status=='verified' and payload.decision!='suspended'):
        raise HTTPException(409,'Customer application is not reviewable')
    if item.user_id==user.id:
        raise HTTPException(403,'You cannot review your own identity documents')
    docs=list(await db.scalars(select(CustomerKYCDocument).where(CustomerKYCDocument.application_id==item.id,CustomerKYCDocument.status!='rejected')))
    if not set(payload.document_decisions).issubset({d.id for d in docs}):
        raise HTTPException(422,'Document decision does not belong to this application')
    if payload.decision=='verified' and (set(item.required_documents)!={d.document_type for d in docs} or any(payload.document_decisions.get(d.id)!='accepted' for d in docs)):
        raise HTTPException(422,'Every required document needs manual acceptance')
    for document in docs:
        if payload.document_decisions.get(document.id)=='accepted':
            await clean_document(storage,document)
    previous=item.status
    for document in docs:
        if document.id in payload.document_decisions:
            document.status=payload.document_decisions[document.id]
    item.status=payload.decision;item.reviewed_by=user.id;item.reviewed_at=datetime.now(UTC);item.decision_reason=payload.reason
    audit(db,user.id,'reviewed',item,{'previous':previous,'decision':payload.decision,'reason':payload.reason,'document_decisions':{str(k):v for k,v in payload.document_decisions.items()}})
    await db.commit()
    return await view(db,item)


@router.get('/documents/{identity}/download')
async def download(identity:uuid.UUID,db=Depends(get_db),user=Depends(require_roles('customer','admin','superadmin')),storage=Depends(get_private_document_storage)):
    document=await db.get(CustomerKYCDocument,identity)
    item=await db.get(CustomerKYCApplication,document.application_id) if document else None
    if not item or (item.user_id!=user.id and not {r.role for r in user.roles}.intersection({'admin','superadmin'})):
        raise HTTPException(404,'Customer document not found')
    await clean_document(storage,document)
    url=await run_in_threadpool(storage.download_url,document.storage_key,document.storage_version_id)
    audit(db,user.id,'document_downloaded',item,{'document_id':str(document.id),'owner_access':item.user_id==user.id})
    await db.commit()
    return dict(download_url=url,expires_in=300)
