import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InviteCode, InviteRedemption


def generate_code() -> str:
    return f"MOM-{secrets.token_hex(4).upper()}"


def create_invite_code(
    db: Session,
    channel: str,
    max_uses: int = 30,
    trial_days: int = 14,
) -> InviteCode:
    code = generate_code()

    invite_code = InviteCode(
        code=code,
        channel=channel,
        max_uses=max_uses,
        trial_days=trial_days,
    )

    db.add(invite_code)
    db.commit()
    db.refresh(invite_code)

    return invite_code


def get_invite_code(db: Session, code: str) -> InviteCode | None:
    return db.scalar(select(InviteCode).where(InviteCode.code == code))


def validate_code(db: Session, code: str) -> bool:
    invite_code = get_invite_code(db, code)

    if not invite_code:
        return False

    if invite_code.max_uses is not None and invite_code.used_count >= invite_code.max_uses:
        return False

    return True


def redeem_code(db: Session, code: str, parent_user_id: str | None = None) -> InviteCode:
    invite_code = get_invite_code(db, code)

    if not invite_code:
        raise ValueError("초대코드가 존재하지 않습니다.")

    if invite_code.max_uses is not None and invite_code.used_count >= invite_code.max_uses:
        raise ValueError("사용 가능한 횟수가 초과되었습니다.")

    invite_code.used_count += 1

    db.add(
        InviteRedemption(
            invite_code_id=invite_code.id,
            parent_user_id=parent_user_id,
        )
    )

    db.commit()
    db.refresh(invite_code)

    return invite_code
