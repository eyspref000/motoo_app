from app.workers.celery_app import celery
from app.db.session import SessionLocal
from app.services.settlement_service import settle_due_portfolios


@celery.task(name="app.workers.daily_price_sync.sync_daily_prices")
def sync_daily_prices():
    # 실제 구현 시 KRX/금융데이터 API 연동 필요
    return {"status": "stub", "message": "price sync not implemented"}


@celery.task(name="app.workers.settlement_scheduler.run_due_settlements")
def run_due_settlements():
    with SessionLocal() as db:
        return settle_due_portfolios(db)
