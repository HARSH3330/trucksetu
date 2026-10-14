from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import HTTPException

from app.api import vehicle_documents as documents
from fastapi.testclient import TestClient
from app.api.auth import current_user
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models import ProviderProfile, VehicleDocument
from app.services.dependencies import get_private_document_storage,get_document_storage_factory
from unittest.mock import Mock


@pytest.mark.asyncio
async def test_approval_requires_all_current_accepted_vehicle_files():
    db=SimpleNamespace(scalars=AsyncMock(return_value=[]))
    with pytest.raises(HTTPException) as failure:
        await documents.require_accepted_documents(db,uuid.uuid4())
    assert failure.value.status_code==422
    files=[SimpleNamespace(document_type=kind,status='accepted',storage_version_id='fictional-v1',expires_on=date.today()+timedelta(days=30)) for kind in documents.KINDS]
    db.scalars.return_value=files
    assert await documents.require_accepted_documents(db,uuid.uuid4())==files
    files[0].status='uploaded'
    with pytest.raises(HTTPException):
        await documents.require_accepted_documents(db,uuid.uuid4())


@pytest.mark.asyncio
async def test_cross_provider_vehicle_document_access_is_concealed():
    vehicle=SimpleNamespace(id=uuid.uuid4(),provider_id=uuid.uuid4())
    db=SimpleNamespace(scalar=AsyncMock(return_value=vehicle),get=AsyncMock(return_value=SimpleNamespace(user_id=uuid.uuid4())))
    user=SimpleNamespace(id=uuid.uuid4(),roles=[SimpleNamespace(role='provider')])
    with pytest.raises(HTTPException) as failure:
        await documents.authorized_vehicle(vehicle.id,user,db)
    assert failure.value.status_code==404


def test_vehicle_private_upload_scan_and_review_flow(monkeypatch):
    provider=SimpleNamespace(id=uuid.uuid4(),user_id=uuid.uuid4())
    vehicle=SimpleNamespace(id=uuid.uuid4(),provider_id=provider.id,status='pending')
    actor=SimpleNamespace(id=provider.user_id,roles=[SimpleNamespace(role='provider')])
    stored=[]
    async def scalar(query):
        return vehicle if query.column_descriptions[0]['entity'] is documents.CarrierVehicle else None
    async def get(model,ident):
        return provider if model is ProviderProfile else next((item for item in stored if isinstance(item,VehicleDocument) and item.id==ident),None)
    async def flush():
        for item in stored:
            if item.id is None:item.id=uuid.uuid4()
    db=SimpleNamespace(scalar=scalar,get=get,scalars=AsyncMock(return_value=[]),add=stored.append,flush=flush,commit=AsyncMock())
    class FakeStorage:
        status='PENDING'
        detected='application/pdf'
        version='v1'
        def upload_url(self,provider_id,kind,filename,content_type):
            return f'kyc/{provider_id}/{kind}/fictional.pdf','http://local.invalid/private-upload'
        def require_clean_scan(self,key,version_id=None):
            if self.status!='NO_THREATS_FOUND':raise ValueError('pending')
        def confirm(self,key):return {'ContentLength':64,'ContentType':'application/pdf','VersionId':self.version}
        def detected_content_type(self,key,version_id=None):return self.detected
        def download_url(self,key,version_id=None):return 'http://local.invalid/private-signed-download?version='+str(version_id or self.version)
    storage=FakeStorage()
    async def session():yield db
    async def user():return actor
    previous=dict(app.dependency_overrides)
    app.dependency_overrides.update({get_db:session,current_user:user,get_private_document_storage:lambda:storage,get_document_storage_factory:lambda:lambda:storage})
    monkeypatch.setattr(documents,'enforce_rate_limit',AsyncMock())
    monkeypatch.setattr('app.services.dependencies.PrivateDocumentStorage',Mock(side_effect=AssertionError('No real storage in local test')))
    headers={'Authorization':'Bearer '+create_access_token({'sub':str(actor.id)})}
    try:
        with TestClient(app,base_url='http://localhost') as client:
            path=f'/api/v1/carrier-vehicles/{vehicle.id}'
            upload={'document_type':'rc','filename':'NOT_A_REAL_VEHICLE_DOCUMENT.pdf','content_type':'application/pdf'}
            prepared=client.post(path+'/uploads',headers=headers,json=upload)
            assert prepared.status_code==200
            body={**upload,'storage_key':prepared.json()['storage_key'],'expires_on':(date.today()+timedelta(days=30)).isoformat()}
            pending=client.post(path+'/documents',headers=headers,json=body)
            assert pending.status_code==409 and not stored
            storage.status='NO_THREATS_FOUND';storage.detected=None
            assert client.post(path+'/documents',headers=headers,json=body).status_code==422
            storage.detected='application/pdf'
            registered=client.post(path+'/documents',headers=headers,json=body)
            assert registered.status_code==201 and registered.json()['status']=='uploaded'
            doc=stored[0]
            storage.version='v2' # still-valid PUT replaces the latest key contents
            download=path+f'/documents/{doc.id}/download'
            assert client.get(download).status_code==401
            opened=client.get(download,headers=headers).json()
            assert opened['expires_in']==300
            assert opened['download_url'].endswith('version=v1') # reviewed bytes, never the replacement
            review=f'/api/v1/admin/carrier-vehicles/{vehicle.id}/documents/{doc.id}/review'
            decision={'status':'accepted','reason':'Harmless fixture manually reviewed'}
            assert client.post(review,headers=headers,json=decision).status_code==403
            actor.roles=[SimpleNamespace(role='admin')]
            storage.status='PENDING'
            assert client.post(review,headers=headers,json=decision).status_code==409
            assert doc.status=='uploaded'
            storage.status='NO_THREATS_FOUND'
            assert client.post(review,headers=headers,json=decision).status_code==200
            assert doc.status=='accepted'
            vehicle.status='approved'
            # Losing storage configuration must not stop an administrator from
            # rejecting unsafe evidence and suspending the approved vehicle.
            app.dependency_overrides.pop(get_private_document_storage)
            app.dependency_overrides.pop(get_document_storage_factory)
            monkeypatch.setattr('app.services.dependencies.PrivateDocumentStorage',Mock(side_effect=RuntimeError('unconfigured')))
            assert client.post(review,headers=headers,json={**decision,'status':'rejected'}).status_code==200
            assert vehicle.status=='suspended' and doc.status=='rejected'
            assert client.post(review,headers=headers,json=decision).status_code==409
    finally:
        app.dependency_overrides.clear();app.dependency_overrides.update(previous)
