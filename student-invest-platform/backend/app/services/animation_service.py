from sqlalchemy.orm import Session

from app.models import Settlement


def create_settlement_animation(db: Session, settlement_id: str):
    settlement = db.get(Settlement, settlement_id)

    if not settlement:
        raise ValueError("정산 기록이 없습니다.")

    settlement.animation_url = f"https://cdn.example.com/animations/{settlement_id}.mp4"
    db.commit()

    return {
        "settlement_id": settlement_id,
        "status": "animation_queued",
        "animation_url": settlement.animation_url,
    }
