"""Feedback table from the approved retail database design."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class CustomerFeedback(Base):
	__tablename__ = "customer_feedback"

	feedback_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	sale_id: Mapped[int | None] = mapped_column(ForeignKey("sales.sale_id", ondelete="SET NULL"), nullable=True)
	return_id: Mapped[int | None] = mapped_column(
		ForeignKey("returns.return_id", ondelete="SET NULL"), nullable=True
	)
	rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
	feedback_text: Mapped[str] = mapped_column(Text)
	feedback_date: Mapped[date] = mapped_column(Date)

	sale = relationship("Sale", foreign_keys=[sale_id])
	return_record = relationship("ReturnRecord", foreign_keys=[return_id])
