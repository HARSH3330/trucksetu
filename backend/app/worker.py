from celery import Celery
from app.core.config import settings

celery_app=Celery("trucksetu",broker=settings.CELERY_BROKER_URL,backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.update(task_serializer="json",result_serializer="json",accept_content=["json"],timezone="Asia/Kolkata",enable_utc=True,task_acks_late=True,worker_prefetch_multiplier=1)


@celery_app.task(name="operations.health_check")
def health_check()->dict[str,str]:
    return {"status":"healthy"}
