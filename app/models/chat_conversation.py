"""A saved chat owned by one authenticated user."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    conversation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    user = relationship("User", back_populates="chat_conversations")
    messages = relationship(
        "ChatMessageRecord",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessageRecord.message_id",
    )
