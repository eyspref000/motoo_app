from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Survey, InviteCode


def submit_survey(
    db: Session,
    parent_user_id: str | None,
    payload: dict,
    invite_code: str | None = None,
) -> Survey:
    invite_code_id = None

    if invite_code:
        code_row = db.scalar(select(InviteCode).where(InviteCode.code == invite_code))
        if code_row:
            invite_code_id = code_row.id

    survey = Survey(
        invite_code_id=invite_code_id,
        parent_user_id=parent_user_id,
        payload=payload,
    )

    db.add(survey)
    db.commit()
    db.refresh(survey)

    return survey
