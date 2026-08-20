from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_admin
from app.models import User, Settlement, Portfolio
from app.schemas import SettlementOut
from app.services.settlement_service import settle_due_portfolios

router = APIRouter()


@router.get("/me", response_model=list[SettlementOut])
def my_settlements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Settlement)
        .join(Portfolio, Settlement.portfolio_id == Portfolio.id)
        .where(Portfolio.user_id == current_user.id)
        .order_by(Settlement.created_at.desc())
    )

    return db.scalars(stmt).all()


@router.post("/admin/run")
def run_settlements(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return settle_due_portfolios(db)
