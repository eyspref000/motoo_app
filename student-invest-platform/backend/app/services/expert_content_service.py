from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExpertContent


def get_expert_contents(
    db: Session,
    stock_code: str | None = None,
    age: int | None = None,
):
    stmt = select(ExpertContent).where(ExpertContent.is_published == True)

    if stock_code:
        stmt = stmt.where(ExpertContent.stock_code == stock_code)

    if age is not None:
        stmt = stmt.where(
            ExpertContent.target_age_min <= age,
            ExpertContent.target_age_max >= age,
        )

    return db.scalars(stmt).all()
