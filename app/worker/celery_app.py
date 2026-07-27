from celery import Celery
import os
import dotenv


dotenv.load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")

celery_app = Celery(
    "bot",
    broker=f"{REDIS_URL}/0",
    backend=f"{REDIS_URL}/1",
    include=["app.worker.tasks"],
)

celery_app.conf.beat_schedule = {
    "check-reminders-every-minute": {"task": "app.worker.tasks.check_reminders", "schedule": 60.0},
}

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]