"""User-scoped persistence helpers for saved chat conversations."""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chat_conversation import ChatConversation, utc_now_naive
from app.models.chat_message import ChatMessageRecord
from app.models.user import User

HISTORY_LIMIT = 20


def get_owned_conversation(db: Session, user: User, conversation_id: int) -> ChatConversation:
    conversation = db.scalar(
        select(ChatConversation).where(
            ChatConversation.conversation_id == conversation_id,
            ChatConversation.user_id == user.user_id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def create_conversation(db: Session, user: User, title: str | None = None) -> ChatConversation:
    conversation = ChatConversation(user_id=user.user_id, title=(title or "New chat").strip())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations(db: Session, user: User) -> list[ChatConversation]:
    return list(db.scalars(
        select(ChatConversation)
        .where(ChatConversation.user_id == user.user_id)
        .options(selectinload(ChatConversation.messages))
        .order_by(ChatConversation.updated_at.desc(), ChatConversation.conversation_id.desc())
    ))


def get_conversation_detail(db: Session, user: User, conversation_id: int) -> ChatConversation:
    conversation = db.scalar(
        select(ChatConversation)
        .where(
            ChatConversation.conversation_id == conversation_id,
            ChatConversation.user_id == user.user_id,
        )
        .options(selectinload(ChatConversation.messages))
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def delete_conversation(db: Session, user: User, conversation_id: int) -> None:
    conversation = get_owned_conversation(db, user, conversation_id)
    db.delete(conversation)
    db.commit()


def serialize_conversation(conversation: ChatConversation) -> dict:
    messages = conversation.messages
    last_message = messages[-1].content if messages else None
    return {
        "conversation_id": conversation.conversation_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": len(messages),
        "last_message": last_message[:160] if last_message else None,
    }


def save_user_message(db: Session, conversation: ChatConversation, content: str) -> ChatMessageRecord:
    now = utc_now_naive()
    message = ChatMessageRecord(
        conversation_id=conversation.conversation_id,
        role="user",
        content=content,
        created_at=now,
    )
    db.add(message)
    if conversation.title == "New chat":
        conversation.title = content[:80].strip() or "New chat"
    conversation.updated_at = now
    db.commit()
    db.refresh(message)
    return message


def load_recent_history(db: Session, conversation: ChatConversation) -> list[dict]:
    rows = list(db.scalars(
        select(ChatMessageRecord)
        .where(ChatMessageRecord.conversation_id == conversation.conversation_id)
        .order_by(ChatMessageRecord.message_id.desc())
        .limit(HISTORY_LIMIT)
    ))
    return [{"role": row.role, "content": row.content} for row in reversed(rows)]


def save_assistant_message(db: Session, conversation: ChatConversation, reply: str, metadata: dict) -> ChatMessageRecord:
    now = datetime.now().replace(tzinfo=None)
    message = ChatMessageRecord(
        conversation_id=conversation.conversation_id,
        role="assistant",
        content=reply,
        created_at=now,
        ref=metadata.get("ref"),
        model=metadata.get("model"),
        duration_ms=metadata.get("duration_ms"),
    )
    db.add(message)
    conversation.updated_at = now
    db.commit()
    db.refresh(message)
    return message