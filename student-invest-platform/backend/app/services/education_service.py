from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lesson, LessonCompletion
from app.services.reward_service import grant_coin


def complete_lesson(db: Session, user_id: str, lesson_id: str):
    lesson = db.get(Lesson, lesson_id)

    if not lesson:
        raise ValueError("수업이 존재하지 않습니다.")

    existing = db.scalar(
        select(LessonCompletion).where(
            LessonCompletion.user_id == user_id,
            LessonCompletion.lesson_id == lesson_id,
        )
    )

    if existing:
        return {
            "message": "이미 완료한 수업입니다.",
            "coin_reward": 0,
        }

    db.add(
        LessonCompletion(
            user_id=user_id,
            lesson_id=lesson_id,
        )
    )

    db.flush()

    grant_coin(
        db=db,
        user_id=user_id,
        amount=10,
        reason="LESSON_COMPLETE",
        reference_id=lesson_id,
    )

    db.commit()

    return {
        "message": "수업 완료",
        "coin_reward": 10,
    }
