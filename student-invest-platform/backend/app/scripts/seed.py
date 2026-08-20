from datetime import date

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.models import (
    Base,
    User,
    ParentConsent,
    Stock,
    ChatRoom,
    Course,
    Lesson,
    ExpertContent,
    InviteCode,
)
from app.services.universe_service import (
    StockMetrics,
    calculate_scores,
    select_universe,
    save_scores_and_universe,
)


def get_or_create_user(
    db,
    email: str,
    password: str,
    nickname: str,
    role: str,
    age_group: str | None = None,
):
    user = db.scalar(select(User).where(User.email == email))

    if user:
        return user

    user = User(
        email=email,
        password_hash=hash_password(password),
        nickname=nickname,
        role=role,
        age_group=age_group,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_or_create_stock(db, code: str, market: str, name: str, sector: str):
    stock = db.get(Stock, code)

    if stock:
        return stock

    stock = Stock(
        code=code,
        market=market,
        name=name,
        sector=sector,
    )

    db.add(stock)
    db.commit()
    db.refresh(stock)

    return stock


def seed():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        admin = get_or_create_user(
            db=db,
            email="admin@example.com",
            password="admin123",
            nickname="관리자",
            role="ADMIN",
        )

        parent = get_or_create_user(
            db=db,
            email="parent@example.com",
            password="parent123",
            nickname="학부모",
            role="PARENT",
        )

        student = get_or_create_user(
            db=db,
            email="student@example.com",
            password="student123",
            nickname="학생투자자",
            role="STUDENT",
            age_group="10s",
        )

        consent = db.scalar(
            select(ParentConsent).where(ParentConsent.student_user_id == student.id)
        )

        if not consent:
            db.add(
                ParentConsent(
                    student_user_id=student.id,
                    parent_user_id=parent.id,
                    consent_marketing=False,
                    consent_chat=True,
                    consent_report=True,
                )
            )

        get_or_create_stock(db, "005930", "KOSPI", "삼성전자", "반도체")
        get_or_create_stock(db, "000660", "KOSPI", "SK 하이닉스", "반도체")
        get_or_create_stock(db, "035420", "KOSPI", "NAVER", "인터넷")
        get_or_create_stock(db, "247540", "KOSDAQ", "에코프로비엠", "이차전지")
        get_or_create_stock(db, "196170", "KOSDAQ", "알테오젠", "바이오")

        metrics = [
            StockMetrics(
                code="005930",
                market="KOSPI",
                name="삼성전자",
                sector="반도체",
                market_cap=400_000_000_000_000,
                liquidity_value=1_000_000_000_000,
                volatility_90d=0.25,
                debt_ratio=20.0,
                operating_profit_stability=0.9,
                revenue_growth_3y=0.08,
                rnd_ratio=0.07,
                future_industry_tags=["AI", "반도체"],
                is_tradable=True,
            ),
            StockMetrics(
                code="000660",
                market="KOSPI",
                name="SK 하이닉스",
                sector="반도체",
                market_cap=150_000_000_000_000,
                liquidity_value=800_000_000_000,
                volatility_90d=0.35,
                debt_ratio=30.0,
                operating_profit_stability=0.7,
                revenue_growth_3y=0.12,
                rnd_ratio=0.08,
                future_industry_tags=["AI", "반도체"],
                is_tradable=True,
            ),
            StockMetrics(
                code="035420",
                market="KOSPI",
                name="NAVER",
                sector="인터넷",
                market_cap=30_000_000_000_000,
                liquidity_value=300_000_000_000,
                volatility_90d=0.30,
                debt_ratio=25.0,
                operating_profit_stability=0.8,
                revenue_growth_3y=0.10,
                rnd_ratio=0.10,
                future_industry_tags=["AI", "클라우드", "콘텐츠"],
                is_tradable=True,
            ),
            StockMetrics(
                code="247540",
                market="KOSDAQ",
                name="에코프로비엠",
                sector="이차전지",
                market_cap=10_000_000_000_000,
                liquidity_value=200_000_000_000,
                volatility_90d=0.55,
                debt_ratio=45.0,
                operating_profit_stability=0.5,
                revenue_growth_3y=0.35,
                rnd_ratio=0.06,
                future_industry_tags=["이차전지", "친환경에너지"],
                is_tradable=True,
            ),
            StockMetrics(
                code="196170",
                market="KOSDAQ",
                name="알테오젠",
                sector="바이오",
                market_cap=3_000_000_000_000,
                liquidity_value=100_000_000_000,
                volatility_90d=0.65,
                debt_ratio=35.0,
                operating_profit_stability=0.4,
                revenue_growth_3y=0.25,
                rnd_ratio=0.20,
                future_industry_tags=["바이오", "헬스케어"],
                is_tradable=True,
            ),
        ]

        scored = calculate_scores(metrics)
        selected = select_universe(scored)

        effective_date = date.today()

        save_scores_and_universe(
            db=db,
            effective_date=effective_date,
            scored=scored,
            selected=selected,
        )

        for market_items in selected.values():
            for item in market_items:
                room = db.scalar(
                    select(ChatRoom).where(ChatRoom.stock_code == item["code"])
                )

                if not room:
                    db.add(
                        ChatRoom(
                            stock_code=item["code"],
                            title=f"{item['name']} 토론방",
                        )
                    )

        course = db.scalar(select(Course).where(Course.title == "기초 경제교육"))

        if not course:
            course = Course(
                title="기초 경제교육",
                description="주식과 위험, 분산투자를 배우는 기초 과정",
            )
            db.add(course)
            db.flush()

            db.add(
                Lesson(
                    course_id=course.id,
                    title="주식이란?",
                    content="주식은 회사의 지분을 나타냅니다.",
                    order_no=1,
                )
            )

        expert_content = db.scalar(
            select(ExpertContent).where(ExpertContent.title == "이번 주 반도체 산업 알아보기")
        )

        if not expert_content:
            db.add(
                ExpertContent(
                    stock_code="005930",
                    title="이번 주 반도체 산업 알아보기",
                    target_age_min=10,
                    target_age_max=19,
                    summary="AI 수요 증가로 반도체 업종에 관심이 커지고 있어요.",
                    body="본 콘텐츠는 교육 목적이며 투자 권유가 아닙니다.",
                    expert_name="김전문가",
                    disclaimer="본 콘텐츠는 교육 목적이며 투자 권유가 아닙니다.",
                    is_published=True,
                )
            )

        invite_code = db.scalar(select(InviteCode).where(InviteCode.code == "MOM-DEMO"))

        if not invite_code:
            db.add(
                InviteCode(
                    code="MOM-DEMO",
                    channel="momcafe",
                    max_uses=100,
                    trial_days=14,
                )
            )

        db.commit()

        print("Seed completed")
        print("Admin: admin@example.com / admin123")
        print("Parent: parent@example.com / parent123")
        print("Student: student@example.com / student123")


if __name__ == "__main__":
    seed()
