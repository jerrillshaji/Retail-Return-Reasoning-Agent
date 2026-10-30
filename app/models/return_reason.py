"""Return reason lookup table from the approved database design."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class ReturnReason(Base):
    __tablename__ = "return_reasons"

    return_reason_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reason_name: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    returns = relationship("ReturnRecord", back_populates="reason")
