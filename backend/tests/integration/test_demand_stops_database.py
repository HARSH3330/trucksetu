"""Isolated migrated PostgreSQL; fictional stops only, no Google/payment call."""
import httpx
from app.core import database
from app.main import app
from _local_release_db import migrated_schema,run_local
from test_demand_marketplace_database import configure,actors_and_payload

STOPS=[{'address':'PRIVATE stop lane 1, Okhla','activity':'pickup','instructions':'Collect 4 cartons'},
       {'address':'PRIVATE stop lane 2, Saket','activity':'drop','instructions':None},
       {'address':'PRIVATE stop lane 3, Dwarka','activity':'drop','instructions':'Gate 2'}]


def test_stops_are_saved_private_to_the_customer_and_editable(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,_,_=await actors_and_payload(factory)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as c:
                created=await c.post('/api/v1/demands',headers=headers[0],json={**payload,'stops':STOPS});assert created.status_code==201,created.text
                item=created.json()
                assert [s['address'] for s in item['stops']]==[s['address'] for s in STOPS] and item['stop_count']==3
                public=next(x for x in (await c.get('/api/v1/demands',headers=headers[2])).json() if x['id']==item['id'])
                assert public['stop_count']==3 and 'stops' not in public and 'PRIVATE stop' not in str(public)
                detail=(await c.get('/api/v1/demands/'+item['id'],headers=headers[2])).json()
                assert detail['stop_count']==3 and 'stops' not in detail
                edited=await c.put('/api/v1/demands/'+item['id'],headers=headers[0],json={**payload,'expected_revision':1,'stops':STOPS[:1]})
                assert edited.status_code==200,edited.text
                assert edited.json()['stop_count']==1 and edited.json()['stops'][0]['address']==STOPS[0]['address']
                mine=next(x for x in (await c.get('/api/v1/demands/mine',headers=headers[0])).json() if x['id']==item['id'])
                assert len(mine['stops'])==1
                blocked=await c.post('/api/v1/demands',headers=headers[0],json={**payload,'stops':[{'address':'PRIVATE lane 9','instructions':'Call 9876543210 at the gate'}]})
                assert blocked.status_code==422
    run_local(exercise())
