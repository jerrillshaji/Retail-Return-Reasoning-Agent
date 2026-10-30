"""Corrective recommendations associated with an investigation."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.investigation_id", ondelete="CASCADE"), index=True
    )
    recommendation_text: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(50), default="Medium")
    status: Mapped[str] = mapped_column(String(50), default="Proposed")
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    investigation = relationship("Investigation", back_populates="recommendations")
