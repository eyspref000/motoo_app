import time

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.deps import get_current_user
from app.models import ChatRoom, ChatMessage, User, ParentConsent
from app.schemas import ChatRoomOut, ChatMessageOut
from app.services.moderation_service import moderate_message
from app.core.security import decode_token

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(room_id, []).append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active:
            if websocket in self.active[room_id]:
                self.active[room_id].remove(websocket)

    async def broadcast(self, room_id: str, payload: dict):
        for connection in self.active.get(room_id, []):
            try:
                await connection.send_json(payload)
            except Exception:
                pass


manager = ConnectionManager()
last_message_at: dict[str, float] = {}


@router.get("/rooms", response_model=list[ChatRoomOut])
def get_rooms(db: Session = Depends(get_db)):
    return db.scalars(select(ChatRoom).where(ChatRoom.is_active == True)).all()


@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageOut])
def get_messages(
    room_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(ChatMessage, User.nickname)
        .join(User, ChatMessage.user_id == User.id)
        .where(
            ChatMessage.room_id == room_id,
            ChatMessage.is_hidden == False,
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return [
        ChatMessageOut(
            id=message.id,
            room_id=message.room_id,
            user_id=message.user_id,
            nickname=nickname,
            message=message.message,
            created_at=message.created_at,
        )
        for message, nickname in reversed(rows)
    ]


@router.post("/messages/{message_id}/report")
def report_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = db.get(ChatMessage, message_id)

    if not message:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")

    return {
        "message": "신고가 접수되었습니다.",
        "message_id": message_id,
    }


@router.websocket("/rooms/{room_id}")
async def chat_websocket(
    websocket: WebSocket,
    room_id: str,
    token: str | None = Query(default=None),
):
    if not token:
        await websocket.close(code=1008)
        return

    payload = decode_token(token)

    if not payload:
        await websocket.close(code=1008)
        return

    with SessionLocal() as db:
        user = db.get(User, payload.get("sub"))

        if not user:
            await websocket.close(code=1008)
            return

        room = db.get(ChatRoom, room_id)

        if not room or not room.is_active:
            await websocket.close(code=1008)
            return

        if user.role == "STUDENT":
            consent = db.scalar(
                select(ParentConsent)
                .where(ParentConsent.student_user_id == user.id)
                .order_by(ParentConsent.consented_at.desc())
            )

            if not consent or not consent.consent_chat:
                await websocket.close(code=1008)
                return

        await manager.connect(room_id, websocket)

        try:
            while True:
                data = await websocket.receive_json()
                message = (data.get("message") or "").strip()

                now_ts = time.time()
                user_key = user.id

                if now_ts - last_message_at.get(user_key, 0) < 1.0:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "너무 빠른 메시지 전송입니다.",
                        }
                    )
                    continue

                last_message_at[user_key] = now_ts

                moderation_result = moderate_message(message)

                if not moderation_result.allowed:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "메시지가 차단되었습니다.",
                            "reason": moderation_result.reason,
                        }
                    )
                    continue

                message_row = ChatMessage(
                    room_id=room_id,
                    user_id=user.id,
                    message=message,
                )

                db.add(message_row)
                db.commit()
                db.refresh(message_row)

                await manager.broadcast(
                    room_id,
                    {
                        "type": "chat",
                        "room_id": room_id,
                        "message_id": message_row.id,
                        "user_id": user.id,
                        "nickname": user.nickname,
                        "message": message,
                        "created_at": message_row.created_at.isoformat(),
                    },
                )

        except WebSocketDisconnect:
            manager.disconnect(room_id, websocket)
