from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import User, Portfolio, Holding
from app.schemas import PortfolioCreateRequest, PortfolioOut, OrderRequest, HoldingOut
from app.services.trading_service import place_order, TradingError
from app.services.settlement_service import calculate_next_settlement_at

router = APIRouter()


@router.post("/portfolios", response_model=PortfolioOut)
def create_portfolio(
    payload: PortfolioCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "STUDENT":
        raise HTTPException(status_code=403, detail="학생 계정만 포트폴리오를 생성할 수 있습니다.")

    portfolio = Portfolio(
        user_id=current_user.id,
        name=payload.name,
        investment_type=payload.investment_type,
        initial_cash=10_000_000,
        cash=10_000_000,
    )

    db.add(portfolio)
    db.flush()

    portfolio.next_settlement_at = calculate_next_settlement_at(portfolio, datetime.utcnow())

    db.commit()
    db.refresh(portfolio)

    return portfolio


@router.get("/portfolios/me", response_model=list[PortfolioOut])
def my_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolios = db.scalars(
        select(Portfolio).where(Portfolio.user_id == current_user.id)
    ).all()

    return portfolios


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolio = db.get(Portfolio, portfolio_id)

    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")

    return portfolio


@router.post("/portfolios/{portfolio_id}/orders")
def create_order(
    portfolio_id: str,
    payload: OrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = place_order(
            db=db,
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            stock_code=payload.stock_code,
            side=payload.side,
            quantity=payload.quantity,
            price=payload.price,
        )
        return result
    except TradingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portfolios/{portfolio_id}/holdings", response_model=list[HoldingOut])
def get_holdings(
    portfolio_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolio = db.get(Portfolio, portfolio_id)

    if not portfolio or portfolio.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")

    holdings = db.scalars(
        select(Holding).where(Holding.portfolio_id == portfolio_id)
    ).all()

    return holdings
