"""Isolated migrated PostgreSQL; synthetic KYC prerequisites, no Google/payment call."""
import httpx
from app.core import database
from app.main import app
from _local_release_db import migrated_schema,run_local
from test_demand_marketplace_database import configure,actors_and_payload

def test_private_draft_publish_edit_locations_and_ownership(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,_,_=await actors_and_payload(factory)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as c:
                draft_payload={'pickup_lat':'28.61','pickup_lng':'77.2','pickup_pin_confirmed':True,'pickup_address':payload['pickup_address']}
                draft=await c.post('/api/v1/demands/drafts',headers=headers[0],json={'payload':draft_payload});assert draft.status_code==201,draft.text
                own=await c.get('/api/v1/demands/drafts',headers=headers[0]);assert own.json()[0]['payload']==draft_payload
                p={**payload,'pickup_location':{'lat':28.61,'lng':77.2},'destination_location':{'lat':28.55,'lng':77.4},'draft_id':draft.json()['id'],'expected_draft_version':1}
                created=await c.post('/api/v1/demands',headers=headers[0],json=p);assert created.status_code==201,created.text
                item=created.json();assert item['pickup_location']==p['pickup_location']
                assert (await c.get('/api/v1/demands/drafts',headers=headers[0])).json()==[]
                public=await c.get('/api/v1/demands',headers=headers[2]);assert public.status_code==200
                found=next(x for x in public.json() if x['id']==item['id']);assert 'pickup_location' not in found and 'destination_location' not in found
                detail=await c.get('/api/v1/demands/'+item['id'],headers=headers[2]);assert 'pickup_location' not in detail.json()
                assert (await c.put('/api/v1/demands/'+item['id'],headers=headers[1],json={**payload,'expected_revision':1})).status_code==403
                edited=await c.put('/api/v1/demands/'+item['id'],headers=headers[0],json={**payload,'expected_revision':1,'pickup_location':None,'destination_location':None});assert edited.status_code==200,edited.text
                assert edited.json()['pickup_location'] is None and edited.json()['revision']==2
                bad=await c.post('/api/v1/demands',headers=headers[0],json={**payload,'pickup_location':{'lat':91,'lng':0}});assert bad.status_code==422
    run_local(exercise())
