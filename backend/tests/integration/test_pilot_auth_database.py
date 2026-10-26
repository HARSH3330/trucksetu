"""Former opt-in smoke test now uses its own guarded migrated local schema."""
import uuid
import httpx
from app.core import database
from app.main import app
from _local_release_db import migrated_schema,run_local


def test_signup_authenticated_request_and_refresh_rotation_use_real_database(monkeypatch):
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            credentials={'full_name':'Fictional Local Customer','email':f'pilot-{uuid.uuid4().hex}@example.com','mobile':None,'password':'PilotPass123!Local','role':'customer'}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                signup=await client.post('/api/v1/auth/signup',json=credentials)
                assert signup.status_code==201,signup.text
                session=signup.json()
                assert 'development_verification_code' not in session
                me=await client.get('/api/v1/auth/me',headers={'Authorization':'Bearer '+session['access_token']})
                assert me.status_code==200 and me.json()['roles']==['customer']
                rotated=await client.post('/api/v1/auth/refresh',json={'refresh_token':session['refresh_token']})
                assert rotated.status_code==200 and rotated.json()['refresh_token']!=session['refresh_token']
                replay=await client.post('/api/v1/auth/refresh',json={'refresh_token':session['refresh_token']})
                assert replay.status_code==401
    run_local(exercise())
