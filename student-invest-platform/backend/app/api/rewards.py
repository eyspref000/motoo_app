from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import User, CoinLedger
from app.schemas import CoinHistoryOut

router = APIRouter()


@router.get("/coins/balance")
def coin_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    balance = db.scalar(
        select(func.coalesce(func.sum(CoinLedger.amount), 0)).where(
            CoinLedger.user_id == current_user.id
        )
    )

    return {"balance": int(balance or 0)}


@router.get("/coins/history", response_model=list[CoinHistoryOut])
def coin_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(CoinLedger)
        .where(CoinLedger.user_id == current_user.id)
        .order_by(CoinLedger.created_at.desc())
    ).all()
