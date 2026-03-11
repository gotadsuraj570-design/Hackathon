from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import uuid

from models import ChatMessage, BotReply, ChatMessageResponse
from auth_utils import get_current_user
from database import get_db
from sentiment import analyse_sentiment, get_bot_reply, is_crisis, get_helplines
from routers.crisis import log_crisis_internal

router = APIRouter()


@router.post("/send", response_model=BotReply)
async def send_message(
    payload: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    db  = get_db()
    uid = current_user["sub"]
    now = datetime.utcnow().isoformat()

    score, level = analyse_sentiment(payload.content)
    crisis       = is_crisis(level)
    bot_text     = get_bot_reply(score, level)
    msg_id       = str(uuid.uuid4())
    bot_id       = str(uuid.uuid4())

    # Save user message
    db.collection("chats").document(uid).collection("messages").document(msg_id).set({
        "id":              msg_id,
        "user_id":         uid,
        "content":         payload.content,
        "role":            "user",
        "sentiment_score": score,
        "sentiment_level": level,
        "timestamp":       now,
    })

    # Save bot reply
    db.collection("chats").document(uid).collection("messages").document(bot_id).set({
        "id":        bot_id,
        "user_id":   uid,
        "content":   bot_text,
        "role":      "bot",
        "timestamp": now,
    })

    # Auto-log crisis
    if crisis:
        await log_crisis_internal(db, uid, payload.content, score, level, now)

    return BotReply(
        message=bot_text,
        sentiment_score=score,
        sentiment_level=level,
        crisis_detected=crisis,
        helplines=get_helplines() if crisis else None,
    )


@router.get("/history", response_model=list[ChatMessageResponse])
async def get_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    db  = get_db()
    uid = current_user["sub"]

    docs = list(
        db.collection("chats").document(uid)
          .collection("messages")
          .order_by("timestamp")
          .limit(limit)
          .stream()
    )

    messages = []
    for doc in docs:
        d = doc.to_dict()
        messages.append(ChatMessageResponse(
            id=d.get("id"),
            user_id=d.get("user_id", uid),
            content=d.get("content", ""),
            role=d.get("role", "user"),
            sentiment_score=d.get("sentiment_score"),
            sentiment_level=d.get("sentiment_level"),
            timestamp=d.get("timestamp"),
        ))
    return messages


@router.delete("/history")
async def clear_history(current_user: dict = Depends(get_current_user)):
    db  = get_db()
    uid = current_user["sub"]

    docs = list(
        db.collection("chats").document(uid)
          .collection("messages").stream()
    )
    for doc in docs:
        doc_ref = db.collection("chats").document(uid).collection("messages").document(doc.id)
        doc_ref.delete()

    return {"deleted": len(docs), "message": "Chat history cleared"}
