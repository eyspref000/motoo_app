from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import Portfolio, Holding, Order, Universe


class TradingError(Exception):
    pass


def is_stock_in_active_universe(db: Session, stock_code: str) -> bool:
    latest = db.scalar(select(func.max(Universe.effective_date)))
    if not latest:
        return False

    exists = db.scalar(
        select(Universe).where(
            Universe.stock_code == stock_code,
            Universe.effective_date == latest,
        )
    )
    return exists is not None


def place_order(
    db: Session,
    portfolio_id: str,
    user_id: str,
    stock_code: str,
    side: str,
    quantity: float,
    price: float,
):
    portfolio = db.get(Portfolio, portfolio_id)

    if not portfolio or portfolio.user_id != user_id:
        raise TradingError("본인 포트폴리오만 거래할 수 있습니다.")

    if not is_stock_in_active_universe(db, stock_code):
        raise TradingError("현재 유니버스에 포함된 종목만 거래할 수 있습니다.")

    if quantity <= 0:
        raise TradingError("수량은 0보다 커야 합니다.")

    if price <= 0:
        raise TradingError("가격은 0보다 커야 합니다.")

    cash = float(portfolio.cash or 0)

    if side == "BUY":
        total_cost = quantity * price

        if cash < total_cost:
            raise TradingError("가상 잔액이 부족합니다.")

        portfolio.cash = cash - total_cost

        holding = db.scalar(
            select(Holding).where(
                Holding.portfolio_id == portfolio_id,
                Holding.stock_code == stock_code,
            )
        )

        if holding:
            old_qty = float(holding.quantity or 0)
            old_avg = float(holding.avg_price or 0)
            new_qty = old_qty + quantity

            holding.quantity = new_qty
            holding.avg_price = ((old_qty * old_avg) + (quantity * price)) / new_qty if new_qty else 0
        else:
            db.add(
                Holding(
                    portfolio_id=portfolio_id,
                    stock_code=stock_code,
                    quantity=quantity,
                    avg_price=price,
                )
            )

    elif side == "SELL":
        holding = db.scalar(
            select(Holding).where(
                Holding.portfolio_id == portfolio_id,
                Holding.stock_code == stock_code,
            )
        )

        if not holding or float(holding.quantity or 0) < quantity:
            raise TradingError("보유 수량이 부족합니다.")

        total_value = quantity * price
        portfolio.cash = cash + total_value

        new_qty = float(holding.quantity or 0) - quantity
        holding.quantity = new_qty

    else:
        raise TradingError("잘못된 주문 방향입니다.")

    db.add(
        Order(
            portfolio_id=portfolio_id,
            stock_code=stock_code,
            side=side,
            quantity=quantity,
            price=price,
            status="FILLED",
        )
    )

    db.commit()

    return {"message": "모의 매매가 완료되었습니다."}
