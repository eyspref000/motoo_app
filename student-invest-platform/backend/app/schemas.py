from datetime import datetime, date
from typing import Optional, Literal, Any

from pydantic import BaseModel, EmailStr, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StudentSignup(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    age_group: Optional[str] = None


class ParentSignup(BaseModel):
    email: EmailStr
    password: str
    nickname: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: str
    email: str
    nickname: str
    role: str
    age_group: Optional[str] = None


class ParentConsentRequest(BaseModel):
    student_email: EmailStr
    consent_marketing: bool = False
    consent_chat: bool = True
    consent_report: bool = True


class UniverseItemOut(BaseModel):
    effective_date: date
    market: str
    stock_code: str
    rank_no: Optional[int] = None
    reason: Optional[str] = None
    stock_name: Optional[str] = None
    total_score: Optional[float] = None


class StockScoreOut(ORMModel):
    stock_code: str
    score_date: date
    safety_score: Optional[float] = None
    future_score: Optional[float] = None
    total_score: Optional[float] = None


class PortfolioCreateRequest(BaseModel):
    name: str
    investment_type: Literal["SHORT_TERM", "LONG_TERM"]


class PortfolioOut(ORMModel):
    id: str
    user_id: str
    name: Optional[str] = None
    investment_type: str
    cash: float
    next_settlement_at: Optional[datetime] = None
    created_at: datetime


class OrderRequest(BaseModel):
    stock_code: str
    side: Literal["BUY", "SELL"]
    quantity: float
    price: float


class HoldingOut(ORMModel):
    stock_code: str
    quantity: float
    avg_price: float


class ChatRoomOut(ORMModel):
    id: str
    stock_code: Optional[str] = None
    title: str


class ChatMessageOut(BaseModel):
    id: str
    room_id: str
    user_id: str
    nickname: Optional[str] = None
    message: str
    created_at: datetime


class SettlementOut(ORMModel):
    id: str
    portfolio_id: str
    period_type: str
    start_date: date
    end_date: date
    return_pct: Optional[float] = None
    total_score: Optional[float] = None
    coin_reward: int
    animation_url: Optional[str] = None
    report_json: Optional[dict] = None


class CourseOut(ORMModel):
    id: str
    title: str
    description: Optional[str] = None


class LessonOut(ORMModel):
    id: str
    course_id: str
    title: str
    content: Optional[str] = None
    order_no: int


class ExpertContentOut(ORMModel):
    id: str
    stock_code: Optional[str] = None
    title: str
    summary: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    expert_name: Optional[str] = None
    disclaimer: Optional[str] = None


class CoinHistoryOut(ORMModel):
    id: str
    amount: int
    reason: str
    reference_id: Optional[str] = None
    created_at: datetime


class InviteCodeCreate(BaseModel):
    channel: str
    max_uses: int = 30
    trial_days: int = 14


class InviteCodeOut(ORMModel):
    id: str
    code: str
    channel: Optional[str] = None
    max_uses: Optional[int] = None
    used_count: int
    trial_days: int


class SurveySubmit(BaseModel):
    payload: dict
    invite_code: Optional[str] = None
