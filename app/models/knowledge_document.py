"""Knowledge document metadata from the approved database design."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    document_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_name: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[str] = mapped_column(String(50))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime)

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")
