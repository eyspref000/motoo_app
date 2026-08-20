from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import Portfolio, Holding, StockPrice, Settlement, LessonCompletion, ChatMessage
from app.services.reward_service import grant_coin


def calculate_next_settlement_at(portfolio: Portfolio, now: datetime) -> datetime:
    if portfolio.investment_type == "SHORT_TERM":
        return now + relativedelta(weeks=1)

    if portfolio.investment_type == "LONG_TERM":
        return now + relativedelta(months=6)

    raise ValueError("알 수 없는 투자 유형입니다.")


def get_latest_price(db: Session, stock_code: str) -> float | None:
    price = db.scalar(
        select(StockPrice.close_price)
        .where(StockPrice.stock_code == stock_code)
        .order_by(StockPrice.price_date.desc())
        .limit(1)
    )
    return float(price) if price is not None else None


def get_education_score(db: Session, user_id: str) -> float:
    count = db.scalar(
        select(func.count(LessonCompletion.id)).where(LessonCompletion.user_id == user_id)
    )
    return min(100.0, float(count or 0) * 20.0)


def get_discussion_score(db: Session, user_id: str) -> float:
    count = db.scalar(
        select(func.count(ChatMessage.id)).where(
            ChatMessage.user_id == user_id,
            ChatMessage.is_hidden == False,
        )
    )
    return min(100.0, float(count or 0) * 5.0)


def calculate_total_score(
    return_score: float,
    risk_adjusted_score: float,
    diversification_score: float,
    education_score: float,
    discussion_score: float,
    rule_compliance_score: float,
) -> float:
    total = (
        return_score * 0.25
        + risk_adjusted_score * 0.20
        + diversification_score * 0.15
        + education_score * 0.20
        + discussion_score * 0.15
        + rule_compliance_score * 0.05
    )

    return round(min(max(total, 0), 100), 2)


def calculate_coin_reward(total_score: float) -> int:
    if total_score >= 90:
        return 100
    if total_score >= 80:
        return 70
    if total_score >= 70:
        return 50
    if total_score >= 60:
        return 30
    if total_score >= 50:
        return 20
    return 10


def calculate_portfolio_value(db: Session, portfolio: Portfolio) -> float:
    value = float(portfolio.cash or 0)

    holdings = db.scalars(select(Holding).where(Holding.portfolio_id == portfolio.id)).all()

    for holding in holdings:
        price = get_latest_price(db, holding.stock_code)
        if price is None:
            price = float(holding.avg_price or 0)

        value += float(holding.quantity or 0) * price

    return value


def calculate_diversification_score(db: Session, portfolio: Portfolio, portfolio_value: float) -> float:
    if portfolio_value <= 0:
        return 100.0

    holdings = db.scalars(select(Holding).where(Holding.portfolio_id == portfolio.id)).all()

    max_weight = 0.0

    for holding in holdings:
        price = get_latest_price(db, holding.stock_code)
        if price is None:
            price = float(holding.avg_price or 0)

        holding_value = float(holding.quantity or 0) * price
        weight = holding_value / portfolio_value
        max_weight = max(max_weight, weight)

    if max_weight <= 0.30:
        return 100.0

    return max(0.0, 100.0 - ((max_weight - 0.30) * 200.0))


def settle_portfolio(db: Session, portfolio: Portfolio, now: datetime) -> Settlement:
    end_date = now.date()

    if portfolio.investment_type == "SHORT_TERM":
        period_type = "WEEKLY"
        start_date = end_date - timedelta(days=6)
    else:
        period_type = "SEMIANNUAL"
        start_date = end_date - relativedelta(months=6)

    portfolio_value = calculate_portfolio_value(db, portfolio)
    initial_cash = float(portfolio.initial_cash or 10_000_000)

    return_pct = ((portfolio_value / initial_cash) - 1) * 100 if initial_cash else 0.0

    return_score = min(100.0, max(0.0, return_pct * 10 + 50))
    risk_adjusted_score = return_score  # MVP 에서는 단순화
    diversification_score = calculate_diversification_score(db, portfolio, portfolio_value)
    education_score = get_education_score(db, portfolio.user_id)
    discussion_score = get_discussion_score(db, portfolio.user_id)
    rule_compliance_score = 80.0  # MVP 기본값

    total_score = calculate_total_score(
        return_score=return_score,
        risk_adjusted_score=risk_adjusted_score,
        diversification_score=diversification_score,
        education_score=education_score,
        discussion_score=discussion_score,
        rule_compliance_score=rule_compliance_score,
    )

    coin_reward = calculate_coin_reward(total_score)

    report_json = {
        "portfolio_id": portfolio.id,
        "period": period_type,
        "summary": f"이번 정산 기간의 수익률은 {round(return_pct, 2)}% 입니다.",
        "economic_situation": {
            "kospi_change": 0.0,
            "kosdaq_change": 0.0,
            "exchange_rate_trend": "데이터 연동 필요",
            "interest_rate_comment": "데이터 연동 필요",
        },
        "expert_comment": {
            "expert_name": "시스템",
            "comment": "본 콘텐츠는 교육 목적이며 투자 권유가 아닙니다.",
        },
    }

    settlement = Settlement(
        portfolio_id=portfolio.id,
        period_type=period_type,
        start_date=start_date,
        end_date=end_date,
        return_pct=return_pct,
        volatility=0.0,
        max_drawdown=0.0,
        education_score=education_score,
        discussion_score=discussion_score,
        total_score=total_score,
        coin_reward=coin_reward,
        report_json=report_json,
        animation_url=f"https://cdn.example.com/animations/{portfolio.id}.mp4",
    )

    db.add(settlement)
    db.flush()

    grant_coin(
        db=db,
        user_id=portfolio.user_id,
        amount=coin_reward,
        reason="SETTLEMENT_REWARD",
        reference_id=settlement.id,
    )

    portfolio.next_settlement_at = calculate_next_settlement_at(portfolio, now)

    db.commit()

    return settlement


def settle_due_portfolios(db: Session, now: datetime | None = None):
    now = now or datetime.utcnow()

    due_portfolios = db.scalars(
        select(Portfolio).where(Portfolio.next_settlement_at <= now)
    ).all()

    settled_ids = []

    for portfolio in due_portfolios:
        settlement = settle_portfolio(db, portfolio, now)
        settled_ids.append(settlement.id)

    return {
        "status": "settlement_started",
        "now": now.isoformat(),
        "settled_portfolio_ids": settled_ids,
    }
