"""Individual cause and evidence stored within an investigation."""

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class InvestigationFinding(Base):
	__tablename__ = "investigation_findings"

	finding_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	investigation_id: Mapped[int] = mapped_column(
		ForeignKey("investigations.investigation_id", ondelete="CASCADE"), index=True
	)
	finding_type: Mapped[str] = mapped_column(String(100))
	finding_text: Mapped[str] = mapped_column(Text)
	confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

	investigation = relationship("Investigation", back_populates="findings")
	evidence = relationship("FindingEvidence", back_populates="finding", cascade="all, delete-orphan")
