from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User, ParentConsent
from app.schemas import (
    StudentSignup,
    ParentSignup,
    LoginRequest,
    TokenResponse,
    UserOut,
    ParentConsentRequest,
)
from app.core.security import hash_password, verify_password, create_access_token
from app.deps import get_current_user

router = APIRouter()


@router.post("/signup/student", response_model=UserOut)
def signup_student(payload: StudentSignup, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email))

    if existing:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        role="STUDENT",
        age_group=payload.age_group,
    )

    db.add(user)
    db.flush()

    db.add(
        ParentConsent(
            student_user_id=user.id,
            consent_marketing=False,
            consent_chat=False,
            consent_report=True,
        )
    )

    db.commit()
    db.refresh(user)

    return user


@router.post("/signup/parent", response_model=UserOut)
def signup_parent(payload: ParentSignup, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email))

    if existing:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        role="PARENT",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    token = create_access_token(user.id, user.role)

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/parent-consent")
def parent_consent(
    payload: ParentConsentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "PARENT":
        raise HTTPException(status_code=403, detail="학부모 계정만 동의할 수 있습니다.")

    student = db.scalar(
        select(User).where(
            User.email == payload.student_email,
            User.role == "STUDENT",
        )
    )

    if not student:
        raise HTTPException(status_code=404, detail="학생 계정을 찾을 수 없습니다.")

    consent = db.scalar(
        select(ParentConsent)
        .where(ParentConsent.student_user_id == student.id)
        .order_by(ParentConsent.consented_at.desc())
    )

    if consent:
        consent.parent_user_id = current_user.id
        consent.consent_marketing = payload.consent_marketing
        consent.consent_chat = payload.consent_chat
        consent.consent_report = payload.consent_report
    else:
        consent = ParentConsent(
            student_user_id=student.id,
            parent_user_id=current_user.id,
            consent_marketing=payload.consent_marketing,
            consent_chat=payload.consent_chat,
            consent_report=payload.consent_report,
        )
        db.add(consent)

    db.commit()

    return {"message": "학부모 동의가 완료되었습니다."}
