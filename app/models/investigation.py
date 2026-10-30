"""Investigation report and its source query."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Investigation(Base):
	__tablename__ = "investigations"

	investigation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id", ondelete="RESTRICT"), index=True)
	user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
	query: Mapped[str] = mapped_column(Text)
	started_at: Mapped[datetime] = mapped_column(DateTime)
	completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
	status: Mapped[str] = mapped_column(String(50), default="Started")

	product = relationship("Product", back_populates="investigations")
	findings = relationship("InvestigationFinding", back_populates="investigation", cascade="all, delete-orphan")
	recommendations = relationship("Recommendation", back_populates="investigation", cascade="all, delete-orphan")
