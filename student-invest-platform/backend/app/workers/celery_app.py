from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "student_invest",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery.conf.timezone = "Asia/Seoul"

celery.conf.beat_schedule = {
    "daily-price-sync": {
        "task": "app.workers.daily_price_sync.sync_daily_prices",
        "schedule": crontab(hour=17, minute=0),
    },
    "weekly-shortterm-settlement": {
        "task": "app.workers.settlement_scheduler.run_due_settlements",
        "schedule": crontab(hour=23, minute=30, day_of_week=0),
    },
    "longterm-settlement-check": {
        "task": "app.workers.settlement_scheduler.run_due_settlements",
        "schedule": crontab(hour=1, minute=0),
    },
}
