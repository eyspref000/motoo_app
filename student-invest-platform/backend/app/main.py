from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    universe,
    portfolios,
    chat,
    settlements,
    education,
    expert_contents,
    rewards,
    invite,
)
from app.db.session import engine
from app.models import Base

app = FastAPI(
    title="Student Invest Platform",
    description="""
    본 서비스는 교육용 모의투자 시뮬레이션입니다.
    실제 주식 매매를 중개하거나 투자 권유를 하지 않습니다.
    제공되는 전문가 의견은 교육 목적이며, 실제 투자 손익을 보장하지 않습니다.
    """,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print("DB 초기화를 건너뜁니다:", e)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "disclaimer": "본 서비스는 교육용 모의투자 시뮬레이션입니다.",
    }


app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(universe.router, prefix="/v1/universe", tags=["universe"])
app.include_router(portfolios.router, prefix="/v1", tags=["portfolios"])
app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
app.include_router(settlements.router, prefix="/v1/settlements", tags=["settlements"])
app.include_router(education.router, prefix="/v1/education", tags=["education"])
app.include_router(expert_contents.router, prefix="/v1/expert-contents", tags=["expert-contents"])
app.include_router(rewards.router, prefix="/v1", tags=["rewards"])
app.include_router(invite.router, prefix="/v1", tags=["invite"])
