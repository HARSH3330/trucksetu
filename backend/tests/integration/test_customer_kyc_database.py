"""Real isolated PostgreSQL, explicit fictional storage/scans, no actual identities."""
import uuid
import httpx
from sqlalchemy import select
from app.core import database
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models import User,UserRole,CustomerKYCApplication,AuditLog
from app.services import customer_kyc
from app.services.dependencies import get_private_document_storage
from e2e_support import LocalDocumentStorage
from _local_release_db import migrated_schema,run_local
from test_demand_marketplace_database import configure,actors_and_payload


def test_customer_scan_review_download_and_publication_lifecycle(monkeypatch,tmp_path):
    configure(monkeypatch)
    monkeypatch.setattr(settings,'CUSTOMER_KYC_TEST_SIMULATION',False)
    monkeypatch.setattr(settings,'CUSTOMER_KYC_REQUIRED_DOCUMENTS','aadhaar,pan')
    monkeypatch.setattr(settings,'CUSTOMER_KYC_CONSENT_TEXT','FICTIONAL LOCAL CONSENT: private sample documents are reviewed solely for this isolated test.')
    monkeypatch.setattr(settings,'CUSTOMER_KYC_POLICY_VERSION','fictional-local-consent-v1')
    storage=LocalDocumentStorage(tmp_path,'local-control-token-not-production','http://localhost')
    monkeypatch.setattr(customer_kyc,'get_private_document_storage',lambda:storage)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,_,_=await actors_and_payload(factory)
            async with factory() as db:
                admin=User(email=f'fictional-admin-{uuid.uuid4()}@example.com',full_name='Fictional local reviewer',password_hash='not-used',roles=[UserRole(role='admin')]);db.add(admin);await db.commit()
                admin_headers={'Authorization':'Bearer '+create_access_token({'sub':str(admin.id),'sv':0})}
            app.dependency_overrides[get_private_document_storage]=lambda:storage
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    base='/api/v1/customer-kyc'
                    assert (await client.post('/api/v1/demands',headers=headers[0],json=payload)).status_code==403
                    assert (await client.get(base+'/admin/applications',headers=headers[0])).status_code==403
                    assert (await client.post(base+'/applications',headers=headers[2],json={'consent_version':'fictional-local-consent-v1','consent_sha256':__import__('hashlib').sha256(settings.CUSTOMER_KYC_CONSENT_TEXT.encode()).hexdigest()})).status_code==403
                    policy=(await client.get(base+'/policy',headers=headers[0])).json()
                    assert policy['consent_text']==settings.CUSTOMER_KYC_CONSENT_TEXT
                    assert (await client.post(base+'/applications',headers=headers[0],json={'consent_version':policy['version'],'consent_sha256':'0'*64})).status_code==409
                    started=await client.post(base+'/applications',headers=headers[0],json={'consent_version':'fictional-local-consent-v1','consent_sha256':__import__('hashlib').sha256(settings.CUSTOMER_KYC_CONSENT_TEXT.encode()).hexdigest()})
                    assert started.status_code==201,started.text
                    identity=started.json()['id'];registered=[]
                    async with factory() as db:
                        record=await db.scalar(select(AuditLog).where(AuditLog.entity_id==uuid.UUID(identity),AuditLog.action=='customer_kyc.consent_recorded'))
                        assert record.after['consent_text']==settings.CUSTOMER_KYC_CONSENT_TEXT and record.after['consent_sha256']==policy['consent_sha256']
                    for kind in ['aadhaar','pan']:
                        value={'document_type':kind,'filename':'fictional.pdf','content_type':'application/pdf'}
                        prepared=await client.post(base+'/uploads',headers=headers[0],json=value);assert prepared.status_code==200
                        key=prepared.json()['storage_key'];storage.put(key,b'%PDF-1.4 fictional local-only document','application/pdf')
                        value['storage_key']=key
                        assert (await client.post(base+'/documents',headers=headers[0],json={**value,'scan_status':'clean'})).status_code==409
                        storage.set_scan_status(key,'NO_THREATS_FOUND')
                        response=await client.post(base+'/documents',headers=headers[0],json=value);assert response.status_code==201,response.text
                        document=response.json()['documents'][-1];registered.append((document,key))
                        assert (await client.get(base+'/documents/'+document['id']+'/download',headers=headers[1])).status_code==404
                        assert (await client.get(base+'/documents/'+document['id']+'/download',headers=headers[0])).status_code==200
                    assert (await client.post(base+'/submit',headers=headers[0])).status_code==200
                    assert (await client.post('/api/v1/demands',headers=headers[0],json=payload)).status_code==403
                    decision={'decision':'verified','reason':'Fictional documents manually reviewed for local test.','document_decisions':{d['id']:'accepted' for d,_ in registered}}
                    endpoint=base+'/admin/applications/'+identity+'/review'
                    assert (await client.post(endpoint,headers=headers[0],json=decision)).status_code==403
                    storage.set_scan_status(registered[0][1],'FAILED')
                    assert (await client.post(endpoint,headers=admin_headers,json=decision)).status_code==409
                    storage.set_scan_status(registered[0][1],'NO_THREATS_FOUND')
                    approved=await client.post(endpoint,headers=admin_headers,json=decision);assert approved.status_code==200,approved.text
                    published=await client.post('/api/v1/demands',headers=headers[0],json=payload);assert published.status_code==201,published.text
                    # Replacement at same key cannot borrow an earlier scan.
                    doc,key=registered[0];old_version=storage.current_versions[key]
                    storage.put(key,b'%PDF-1.4 replacement','application/pdf')
                    assert storage.current_versions[key]!=old_version
                    assert (await client.get(base+'/documents/'+doc['id']+'/download',headers=headers[0])).status_code==200 # recorded clean version only
                    storage.version_scans[key,old_version]='FAILED'
                    assert (await client.get(base+'/documents/'+doc['id']+'/download',headers=admin_headers)).status_code==409
                    assert (await client.post('/api/v1/demands',headers=headers[0],json=payload)).status_code==409
                    suspended=await client.post(endpoint,headers=admin_headers,json={'decision':'suspended','reason':'Fictional suspension preserves historical evidence.'});assert suspended.status_code==200
                    assert (await client.post('/api/v1/demands',headers=headers[0],json=payload)).status_code==403
                    async with factory() as db:
                        item=await db.scalar(select(CustomerKYCApplication).where(CustomerKYCApplication.id==uuid.UUID(identity)));assert item.status=='suspended'
            finally:app.dependency_overrides.pop(get_private_document_storage,None)
    run_local(exercise())



def test_verified_customer_can_renew_changed_policy_without_losing_history(monkeypatch):
    monkeypatch.setattr(settings,'CUSTOMER_KYC_REQUIRED_DOCUMENTS','pan')
    monkeypatch.setattr(settings,'CUSTOMER_KYC_CONSENT_TEXT','FICTIONAL LOCAL CONSENT: private sample documents are reviewed solely for this isolated test.')
    monkeypatch.setattr(settings,'CUSTOMER_KYC_POLICY_VERSION','fictional-renewed-v2')
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,_,_,_=await actors_and_payload(factory)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                user_id=(await client.get('/api/v1/auth/me',headers=headers[0])).json()['id']
                async with factory() as db:
                    old=CustomerKYCApplication(user_id=uuid.UUID(user_id),status='verified',policy_version='fictional-old-v1',required_documents=['pan']);db.add(old);await db.commit();old_id=old.id
                response=await client.post('/api/v1/customer-kyc/applications',headers=headers[0],json={'consent_version':'fictional-renewed-v2','consent_sha256':__import__('hashlib').sha256(settings.CUSTOMER_KYC_CONSENT_TEXT.encode()).hexdigest()})
                assert response.status_code==201,response.text
                assert response.json()['status']=='registered' and response.json()['id']!=str(old_id)
                async with factory() as db:
                    old=await db.get(CustomerKYCApplication,old_id);assert old.status=='superseded'
    run_local(exercise())
