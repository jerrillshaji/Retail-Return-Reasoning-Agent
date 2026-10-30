"""Return table from the approved retail database design."""

from datetime import date

from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class ReturnRecord(Base):
    __tablename__ = "returns"

    return_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.sale_id", ondelete="RESTRICT"), index=True)
    return_reason_id: Mapped[int | None] = mapped_column(
        ForeignKey("return_reasons.return_reason_id", ondelete="SET NULL"), nullable=True
    )
    return_date: Mapped[date] = mapped_column(Date)
    returned_quantity: Mapped[int] = mapped_column(Integer)
    return_status: Mapped[str] = mapped_column(String(50), default="Pending")
    refund_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    sale = relationship("Sale", back_populates="returns")
    reason = relationship("ReturnReason", back_populates="returns")
