import asyncio

from celery import Celery

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.capacity import release_expired_capacity_holds

celery_app=Celery("trucksetu",broker=settings.CELERY_BROKER_URL,backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.update(task_serializer="json",result_serializer="json",accept_content=["json"],timezone="Asia/Kolkata",enable_utc=True,task_acks_late=True,worker_prefetch_multiplier=1,beat_schedule={"release-expired-capacity-holds":{"task":"capacity.release_expired_holds","schedule":60.0}})


@celery_app.task(name="operations.health_check")
def health_check()->dict[str,str]:
    return {"status":"healthy"}


async def _release_expired() -> int:
    async with AsyncSessionLocal() as db:
        try:
            released = await release_expired_capacity_holds(db)
            await db.commit()
            return released
        except Exception:
            await db.rollback()
            raise


@celery_app.task(name="capacity.release_expired_holds", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def release_expired_holds() -> dict[str, int]:
    return {"released": asyncio.run(_release_expired())}
