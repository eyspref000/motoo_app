from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_admin
from app.models import User
from app.schemas import InviteCodeCreate, InviteCodeOut, SurveySubmit
from app.services.invite_service import create_invite_code, validate_code, redeem_code
from app.services.survey_service import submit_survey

router = APIRouter()


@router.post("/admin/invite-codes", response_model=InviteCodeOut)
def create_invite_code_endpoint(
    payload: InviteCodeCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return create_invite_code(
        db=db,
        channel=payload.channel,
        max_uses=payload.max_uses,
        trial_days=payload.trial_days,
    )


@router.get("/invite-codes/{code}/validate")
def validate_invite_code(code: str, db: Session = Depends(get_db)):
    return {"valid": validate_code(db=db, code=code)}


@router.post("/invite-codes/{code}/redeem")
def redeem_invite_code(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "PARENT":
        raise HTTPException(status_code=403, detail="학부모 계정만 초대코드를 사용할 수 있습니다.")

    try:
        invite_code = redeem_code(db=db, code=code, parent_user_id=current_user.id)
        return {
            "message": "초대코드가 적용되었습니다.",
            "trial_days": invite_code.trial_days,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/surveys")
def submit_survey_endpoint(
    payload: SurveySubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = submit_survey(
        db=db,
        parent_user_id=current_user.id,
        payload=payload.payload,
        invite_code=payload.invite_code,
    )

    return {
        "message": "설문이 제출되었습니다.",
        "survey_id": survey.id,
    }
