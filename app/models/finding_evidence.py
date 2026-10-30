"""Evidence references associated with an investigation finding."""

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class FindingEvidence(Base):
    __tablename__ = "finding_evidence"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('return', 'sale', 'feedback', 'knowledge_chunk')",
            name="ck_finding_evidence_source_type",
        ),
    )

    evidence_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    finding_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_findings.finding_id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[int] = mapped_column()

    finding = relationship("InvestigationFinding", back_populates="evidence")
