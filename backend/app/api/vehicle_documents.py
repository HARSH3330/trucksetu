from datetime import UTC, date, datetime
from collections.abc import Callable
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.auth import current_user, require_roles
from app.core.database import get_db
from app.core.rate_limit import enforce_rate_limit
from app.core.routing import AuthenticationFirstRoute
from app.models import AuditLog, CarrierVehicle, ProviderProfile, User, VehicleDocument
from app.services.dependencies import get_private_document_storage,get_document_storage_factory
from app.services.storage import PrivateDocumentStorage

router=APIRouter(prefix='/api/v1',tags=['private vehicle documents'],route_class=AuthenticationFirstRoute)
KINDS={'rc','insurance','fitness','pollution','permit'}
Kind=Literal['rc','insurance','fitness','pollution','permit']

class Upload(BaseModel):
    document_type: Kind
    filename: str=Field(min_length=1,max_length=255)
    content_type: Literal['application/pdf','image/jpeg','image/png']

class Complete(Upload):
    storage_key: str=Field(min_length=1,max_length=500)
    expires_on: date

class Decision(BaseModel):
    status: Literal['accepted','rejected']
    reason: str=Field(min_length=10,max_length=2000)

async def authorized_vehicle(vehicle_id:uuid.UUID,user:User,db:AsyncSession)->CarrierVehicle:
    vehicle=await db.scalar(select(CarrierVehicle).where(CarrierVehicle.id==vehicle_id).with_for_update())
    if not vehicle:raise HTTPException(404,'Vehicle not found')
    provider=await db.get(ProviderProfile,vehicle.provider_id)
    roles={r.role for r in user.roles}
    if not provider or (provider.user_id!=user.id and not roles.intersection({'admin','superadmin'})):
        raise HTTPException(404,'Vehicle not found')
    return vehicle

def read(item:VehicleDocument)->dict[str,object]:
    return {'id':str(item.id),'type':item.document_type,'filename':item.original_filename,'status':item.status,'expires_on':item.expires_on.isoformat(),'review_reason':item.review_reason}

async def clean(storage:PrivateDocumentStorage,key:str,version_id:str)->None:
    if not version_id or version_id=='null':raise HTTPException(503,'Immutable document version is unavailable')
    try:await run_in_threadpool(storage.require_clean_scan,key,version_id)
    except ValueError as exc:raise HTTPException(409,'Document scan is pending or was not clean') from exc
    except Exception as exc:raise HTTPException(503,'Document scan is unavailable') from exc

async def require_accepted_documents(db:AsyncSession,vehicle_id:uuid.UUID,through:date|None=None)->list[VehicleDocument]:
    through = through or date.today()
    items=list(await db.scalars(select(VehicleDocument).where(VehicleDocument.vehicle_id==vehicle_id,VehicleDocument.status=='accepted').with_for_update()))
    present={item.document_type for item in items if item.status=='accepted' and item.expires_on>=through and item.storage_version_id and item.storage_version_id!='null'}
    if KINDS-present:raise HTTPException(422,{'message':'Accepted version-bound vehicle documents must cover the planned trip','missing':sorted(KINDS-present)})
    return items

@router.get('/carrier-vehicles/{vehicle_id}/documents')
async def list_documents(vehicle_id:uuid.UUID,user:User=Depends(current_user),db:AsyncSession=Depends(get_db))->list[dict[str,object]]:
    await authorized_vehicle(vehicle_id,user,db)
    items=await db.scalars(select(VehicleDocument).where(VehicleDocument.vehicle_id==vehicle_id).order_by(VehicleDocument.created_at))
    return [read(item) for item in items]

@router.post('/carrier-vehicles/{vehicle_id}/uploads')
async def prepare(vehicle_id:uuid.UUID,payload:Upload,request:Request,user:User=Depends(require_roles('provider','fleet_owner')),db:AsyncSession=Depends(get_db),storage:PrivateDocumentStorage=Depends(get_private_document_storage))->dict[str,object]:
    await enforce_rate_limit(request,'vehicle-upload',20,600,str(user.id))
    vehicle=await authorized_vehicle(vehicle_id,user,db)
    if vehicle.status=='approved':raise HTTPException(409,'Suspend vehicle before replacing approved documents')
    kind=f'vehicle_{vehicle.id}_{payload.document_type}'
    try:key,url=await run_in_threadpool(storage.upload_url,vehicle.provider_id,kind,payload.filename,payload.content_type)
    except ValueError as exc:raise HTTPException(422,'Invalid document filename or type') from exc
    except Exception as exc:raise HTTPException(503,'Private upload unavailable') from exc
    return {'storage_key':key,'upload_url':url,'expires_in':600}

@router.post('/carrier-vehicles/{vehicle_id}/documents',status_code=201)
async def register(vehicle_id:uuid.UUID,payload:Complete,request:Request,user:User=Depends(require_roles('provider','fleet_owner')),db:AsyncSession=Depends(get_db),storage:PrivateDocumentStorage=Depends(get_private_document_storage))->dict[str,object]:
    await enforce_rate_limit(request,'vehicle-register',30,600,str(user.id))
    vehicle=await authorized_vehicle(vehicle_id,user,db)
    if vehicle.status=='approved':raise HTTPException(409,'Suspend vehicle before replacing approved documents')
    prefix=f'kyc/{vehicle.provider_id}/vehicle_{vehicle.id}_{payload.document_type}/'
    if not payload.storage_key.startswith(prefix):raise HTTPException(422,'Invalid document reference')
    if payload.expires_on<date.today():raise HTTPException(422,'Document is expired')
    try:
        metadata=await run_in_threadpool(storage.confirm,payload.storage_key)
    except Exception as exc:raise HTTPException(503,'Document content could not be verified') from exc
    version_id=metadata.get('VersionId')
    if not isinstance(version_id,str) or not version_id or version_id=='null':
        raise HTTPException(503,'Private vehicle uploads require bucket versioning')
    await clean(storage,payload.storage_key,version_id)
    try:detected=await run_in_threadpool(storage.detected_content_type,payload.storage_key,version_id)
    except Exception as exc:raise HTTPException(503,'Document content could not be verified') from exc
    size=int(metadata.get('ContentLength',0))
    if size<=0 or size>10*1024*1024 or detected!=payload.content_type or metadata.get('ContentType')!=detected:
        raise HTTPException(422,'Document size or content type is invalid')
    if await db.scalar(select(VehicleDocument.id).where(VehicleDocument.vehicle_id==vehicle.id,VehicleDocument.document_type==payload.document_type,VehicleDocument.status!='rejected')):
        raise HTTPException(409,'Reject the current document before replacing it')
    item=VehicleDocument(vehicle_id=vehicle.id,document_type=payload.document_type,storage_key=payload.storage_key,storage_version_id=version_id,original_filename=payload.filename,content_type=payload.content_type,size_bytes=size,expires_on=payload.expires_on,status='uploaded')
    db.add(item);await db.flush()
    setattr(vehicle,f'{payload.document_type}_expires_on',payload.expires_on)
    vehicle.status='pending'
    db.add(AuditLog(actor_id=user.id,action='vehicle.document_registered',entity_type='vehicle_document',entity_id=item.id,after={'type':item.document_type,'vehicle_id':str(vehicle.id)}))
    await db.commit()
    return read(item)

@router.get('/carrier-vehicles/{vehicle_id}/documents/{document_id}/download')
async def download(vehicle_id:uuid.UUID,document_id:uuid.UUID,user:User=Depends(current_user),db:AsyncSession=Depends(get_db),storage:PrivateDocumentStorage=Depends(get_private_document_storage))->dict[str,object]:
    await authorized_vehicle(vehicle_id,user,db)
    item=await db.get(VehicleDocument,document_id)
    if not item or item.vehicle_id!=vehicle_id:raise HTTPException(404,'Document not found')
    await clean(storage,item.storage_key,item.storage_version_id)
    try:url=await run_in_threadpool(storage.download_url,item.storage_key,item.storage_version_id)
    except Exception as exc:raise HTTPException(503,'Document access unavailable') from exc
    db.add(AuditLog(actor_id=user.id,action='vehicle.document_accessed',entity_type='vehicle_document',entity_id=item.id))
    await db.commit()
    return {'download_url':url,'expires_in':300}

@router.post('/admin/carrier-vehicles/{vehicle_id}/documents/{document_id}/review')
async def review(vehicle_id:uuid.UUID,document_id:uuid.UUID,payload:Decision,user:User=Depends(require_roles('admin','superadmin')),db:AsyncSession=Depends(get_db),storage_factory:Callable[[],PrivateDocumentStorage]=Depends(get_document_storage_factory))->dict[str,object]:
    vehicle=await authorized_vehicle(vehicle_id,user,db)
    item=await db.get(VehicleDocument,document_id)
    if not item or item.vehicle_id!=vehicle_id:raise HTTPException(404,'Document not found')
    if item.status=='rejected':raise HTTPException(409,'Rejected document must be replaced')
    if payload.status=='accepted':
        if item.expires_on<date.today():raise HTTPException(422,'Document is expired')
        await clean(storage_factory(),item.storage_key,item.storage_version_id)
    previous=item.status
    item.status=payload.status;item.review_reason=payload.reason;item.reviewed_by=user.id;item.reviewed_at=datetime.now(UTC)
    if payload.status=='rejected' and vehicle.status=='approved':vehicle.status='suspended'
    db.add(AuditLog(actor_id=user.id,action='vehicle.document_reviewed',entity_type='vehicle_document',entity_id=item.id,before={'status':previous},after={'status':item.status,'reason':payload.reason,'vehicle_status':vehicle.status}))
    await db.commit()
    return read(item)
