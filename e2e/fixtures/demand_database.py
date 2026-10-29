"""Fictional local prerequisite identities/compliance, never a real KYC approval."""
import json
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'backend'))
sys.path.insert(0,str(root/'backend/tests/integration'))
from e2e_database import safe_database_url

raw=safe_database_url()
from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine
from _local_release_db import run_local
from test_shared_booking_database import seed
from app.core.security import get_password_hash
from app.models import AvailableRoute,User


async def prepare():
    password=json.load(sys.stdin)['password']
    engine=create_async_engine(raw.replace('postgresql://','postgresql+psycopg://',1))
    factory=async_sessionmaker(engine,expire_on_commit=False)
    try:
        actors,route_id,_,_=await seed(factory)
        async with factory() as db:
            for actor in actors:
                user=await db.get(User,actor.id)
                user.password_hash=get_password_hash(password)
                user.email_verified=True
            provider=await db.get(User,actors[2].id)
            driver=await db.get(User,actors[3].id)
            provider.mobile,provider.mobile_verified='+919000000001',True
            driver.mobile,driver.mobile_verified='+919000000002',True
            # Keep these fictional phones unique across sequential fixture calls.
            import uuid
            suffix=str(uuid.uuid4().int)[:8]
            provider.mobile='+9191'+suffix
            driver.mobile='+9192'+suffix
            route=await db.get(AvailableRoute,route_id)
            route.status='cancelled'
            await db.commit()
            print(json.dumps({'customer_email':actors[0].email,'other_customer_email':actors[1].email,'provider_email':actors[2].email,'admin_email':actors[4].email,'vehicle_id':str(route.carrier_vehicle_id),'driver_id':str(route.driver_id),'pickup':route.departure_at.isoformat(),'delivery':route.expected_arrival_at.isoformat(),'provider_phone':provider.mobile,'driver_phone':driver.mobile}))
    finally:
        await engine.dispose()


if __name__=='__main__':
    try:
        run_local(prepare())
    except Exception as exc:
        raise SystemExit('Fictional local demand fixture failed: '+type(exc).__name__+'; details withheld') from None
