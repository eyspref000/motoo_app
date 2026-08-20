from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    Boolean,
    Text,
    Date,
    Integer,
    ForeignKey,
    UniqueConstraint,
    JSON,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(30))
    role: Mapped[str] = mapped_column(String(20))  # STUDENT, PARENT, ADMIN
    age_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ParentConsent(Base):
    __tablename__ = "parent_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    student_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    parent_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    consent_marketing: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_chat: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_report: Mapped[bool] = mapped_column(Boolean, default=True)
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Stock(Base):
    __tablename__ = "stocks"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    market: Mapped[str] = mapped_column(String(10))  # KOSPI, KOSDAQ
    name: Mapped[str] = mapped_column(String(100))
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class StockScore(Base):
    __tablename__ = "stock_scores"
    __table_args__ = (UniqueConstraint("stock_code", "score_date", name="uq_stock_score_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), nullable=False)
    score_date: Mapped[date] = mapped_column(Date, nullable=False)

    safety_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    future_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    total_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)

    market_cap: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    volatility_90d: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    debt_ratio: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    revenue_growth_3y: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    rnd_ratio: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    liquidity_value: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Universe(Base):
    __tablename__ = "universes"
    __table_args__ = (UniqueConstraint("effective_date", "market", "stock_code", name="uq_universe_date_market_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), nullable=False)
    rank_no: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class StockPrice(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (UniqueConstraint("stock_code", "price_date", name="uq_stock_price_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_price: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    investment_type: Mapped[str] = mapped_column(String(20), nullable=False)  # SHORT_TERM, LONG_TERM
    initial_cash: Mapped[float] = mapped_column(Numeric(20, 2), default=10_000_000)
    cash: Mapped[float] = mapped_column(Numeric(20, 2), default=10_000_000)
    next_settlement_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (UniqueConstraint("portfolio_id", "stock_code", name="uq_holding_portfolio_stock"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("portfolios.id"), nullable=False)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(20, 4), default=0)
    avg_price: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("portfolios.id"), nullable=False)
    stock_code: Mapped[str] = mapped_column(String(10), ForeignKey("stocks.code"), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    quantity: Mapped[float] = mapped_column(Numeric(20, 4), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    stock_code: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("stocks.code"), nullable=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_room_created", "room_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    room_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_rooms.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    hidden_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("portfolios.id"), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # WEEKLY, SEMIANNUAL
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    return_pct: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    volatility: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)

    education_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    discussion_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    total_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)

    coin_reward: Mapped[int] = mapped_column(Integer, default=0)
    report_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    animation_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ExpertContent(Base):
    __tablename__ = "expert_contents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    stock_code: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("stocks.code"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_age_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_age_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    animation_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expert_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    disclaimer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_age_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_age_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_no: Mapped[int] = mapped_column(Integer, default=1)


class LessonCompletion(Base):
    __tablename__ = "lesson_completions"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_completion"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id"), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id"), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CoinLedger(Base):
    __tablename__ = "coin_ledger"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    trial_days: Mapped[int] = mapped_column(Integer, default=14)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class InviteRedemption(Base):
    __tablename__ = "invite_redemptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    invite_code_id: Mapped[str] = mapped_column(String(36), ForeignKey("invite_codes.id"), nullable=False)
    parent_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    invite_code_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("invite_codes.id"), nullable=True)
    parent_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
