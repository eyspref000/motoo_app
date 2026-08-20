from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ExpertContentOut
from app.services.expert_content_service import get_expert_contents

router = APIRouter()


@router.get("", response_model=list[ExpertContentOut])
def expert_contents(
    stock_code: str | None = None,
    age: int | None = None,
    db: Session = Depends(get_db),
):
    return get_expert_contents(db=db, stock_code=stock_code, age=age)
