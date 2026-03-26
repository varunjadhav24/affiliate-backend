from dotenv import load_dotenv
import os

# Load .env from the repo root (one level up from backend/)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from celery import Celery
from app.core.config import settings
from app.tasks.scheduler import CELERYBEAT_SCHEDULE

celery_app = Celery(
    "affiliate_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.agent_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule=CELERYBEAT_SCHEDULE,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
    broker_connection_retry_on_startup=True,   # ← add this line

)
