from dataclasses import dataclass
from typing import List, Dict
from collections import defaultdict
from datetime import date

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models import Stock, StockScore, Universe

KOSPI_LIMIT = 70
KOSDAQ_LIMIT = 30
SECTOR_CAP = 15

SAFE_WEIGHT = 0.55
FUTURE_WEIGHT = 0.45

FUTURE_TAGS = {
    "AI",
    "반도체",
    "이차전지",
    "로봇",
    "자율주행",
    "우주항공",
    "바이오",
    "친환경에너지",
    "클라우드",
    "보안",
    "콘텐츠",
    "게임",
    "헬스케어",
}


@dataclass
class StockMetrics:
    code: str
    market: str
    name: str
    sector: str
    market_cap: float
    liquidity_value: float
    volatility_90d: float
    debt_ratio: float
    operating_profit_stability: float
    revenue_growth_3y: float
    rnd_ratio: float
    future_industry_tags: List[str]
    is_tradable: bool


def normalize(values: List[float], reverse: bool = False) -> List[float]:
    if not values:
        return []

    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        return [0.5 for _ in values]

    if reverse:
        return [(max_v - v) / (max_v - min_v) for v in values]

    return [(v - min_v) / (max_v - min_v) for v in values]


def calculate_scores(metrics: List[StockMetrics]) -> List[dict]:
    market_caps = normalize([m.market_cap for m in metrics])
    liquidities = normalize([m.liquidity_value for m in metrics])
    volatilities = normalize([m.volatility_90d for m in metrics], reverse=True)
    debt_ratios = normalize([m.debt_ratio for m in metrics], reverse=True)
    profit_stabilities = normalize([m.operating_profit_stability for m in metrics])
    revenue_growths = normalize([m.revenue_growth_3y for m in metrics])
    rnd_ratios = normalize([m.rnd_ratio for m in metrics])

    results = []

    for i, m in enumerate(metrics):
        future_tag_score = len(set(m.future_industry_tags) & FUTURE_TAGS) / max(len(FUTURE_TAGS), 1)

        safety_score = (
            market_caps[i] * 0.20
            + liquidities[i] * 0.15
            + volatilities[i] * 0.15
            + debt_ratios[i] * 0.15
            + profit_stabilities[i] * 0.35
        ) * 100

        future_score = (
            revenue_growths[i] * 0.25
            + rnd_ratios[i] * 0.20
            + future_tag_score * 0.35
            + 0.20  # 정책/산업 모멘텀은 향후 별도 데이터 연동
        ) * 100

        total_score = safety_score * SAFE_WEIGHT + future_score * FUTURE_WEIGHT

        results.append(
            {
                "code": m.code,
                "market": m.market,
                "name": m.name,
                "sector": m.sector,
                "safety_score": round(safety_score, 2),
                "future_score": round(future_score, 2),
                "total_score": round(total_score, 2),
            }
        )

    return results


def select_universe(scored: List[dict]) -> Dict[str, List[dict]]:
    selected = {
        "KOSPI": [],
        "KOSDAQ": [],
    }

    sector_counts = {
        "KOSPI": defaultdict(int),
        "KOSDAQ": defaultdict(int),
    }

    limits = {
        "KOSPI": KOSPI_LIMIT,
        "KOSDAQ": KOSDAQ_LIMIT,
    }

    for market in ["KOSPI", "KOSDAQ"]:
        candidates = [s for s in scored if s["market"] == market]
        candidates.sort(key=lambda x: x["total_score"], reverse=True)

        for item in candidates:
            if len(selected[market]) >= limits[market]:
                break

            if sector_counts[market][item["sector"]] >= SECTOR_CAP:
                continue

            selected[market].append(item)
            sector_counts[market][item["sector"]] += 1

    return selected


def get_current_effective_date(db: Session):
    return db.scalar(select(func.max(Universe.effective_date)))


def save_scores_and_universe(
    db: Session,
    effective_date: date,
    scored: List[dict],
    selected: Dict[str, List[dict]],
):
    for item in scored:
        existing = db.scalar(
            select(StockScore).where(
                and_(
                    StockScore.stock_code == item["code"],
                    StockScore.score_date == effective_date,
                )
            )
        )

        if existing:
            existing.safety_score = item["safety_score"]
            existing.future_score = item["future_score"]
            existing.total_score = item["total_score"]
        else:
            db.add(
                StockScore(
                    stock_code=item["code"],
                    score_date=effective_date,
                    safety_score=item["safety_score"],
                    future_score=item["future_score"],
                    total_score=item["total_score"],
                )
            )

    for market, items in selected.items():
        for rank, item in enumerate(items, start=1):
            existing = db.scalar(
                select(Universe).where(
                    and_(
                        Universe.effective_date == effective_date,
                        Universe.market == market,
                        Universe.stock_code == item["code"],
                    )
                )
            )

            if not existing:
                db.add(
                    Universe(
                        effective_date=effective_date,
                        market=market,
                        stock_code=item["code"],
                        rank_no=rank,
                        reason="score-based selection",
                    )
                )

    db.commit()
