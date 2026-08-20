from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Universe, Stock, StockScore
from app.schemas import UniverseItemOut, StockScoreOut

router = APIRouter()


@router.get("/current")
def current_universe(db: Session = Depends(get_db)):
    effective_date = db.scalar(select(func.max(Universe.effective_date)))

    if not effective_date:
        return {
            "effective_date": None,
            "items": [],
        }

    stmt = (
        select(Universe, Stock.name, StockScore.total_score)
        .join(Stock, Universe.stock_code == Stock.code, isouter=True)
        .join(
            StockScore,
            and_(
                StockScore.stock_code == Universe.stock_code,
                StockScore.score_date == Universe.effective_date,
            ),
            isouter=True,
        )
        .where(Universe.effective_date == effective_date)
        .order_by(Universe.market, Universe.rank_no)
    )

    items = []

    for universe, stock_name, total_score in db.execute(stmt):
        items.append(
            UniverseItemOut(
                effective_date=universe.effective_date,
                market=universe.market,
                stock_code=universe.stock_code,
                rank_no=universe.rank_no,
                reason=universe.reason,
                stock_name=stock_name,
                total_score=float(total_score) if total_score is not None else None,
            )
        )

    return {
        "effective_date": effective_date,
        "items": items,
    }


@router.get("/history")
def universe_history(db: Session = Depends(get_db)):
    dates = db.scalars(
        select(Universe.effective_date)
        .distinct()
        .order_by(Universe.effective_date.desc())
    ).all()

    return {"effective_dates": dates}


@router.get("/stocks/{code}/score", response_model=StockScoreOut)
def stock_score(code: str, db: Session = Depends(get_db)):
    score = db.scalar(
        select(StockScore)
        .where(StockScore.stock_code == code)
        .order_by(StockScore.score_date.desc())
        .limit(1)
    )

    if not score:
        raise HTTPException(status_code=404, detail="점수 데이터가 없습니다.")

    return score
