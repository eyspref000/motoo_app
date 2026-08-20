from sqlalchemy.orm import Session

from app.models import CoinLedger


def grant_coin(
    db: Session,
    user_id: str,
    amount: int,
    reason: str,
    reference_id: str | None = None,
):
    if amount <= 0:
        raise ValueError("코인은 0 보다 커야 합니다.")

    ledger = CoinLedger(
        user_id=user_id,
        amount=amount,
        reason=reason,
        reference_id=reference_id,
    )

    db.add(ledger)
    db.commit()

    return {
        "user_id": user_id,
        "amount": amount,
        "reason": reason,
    }
