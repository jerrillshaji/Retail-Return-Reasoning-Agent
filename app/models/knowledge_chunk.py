"""Chunked knowledge-base text and optional embedding."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class KnowledgeChunk(Base):
	__tablename__ = "knowledge_chunks"

	chunk_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	document_id: Mapped[int] = mapped_column(
		ForeignKey("knowledge_documents.document_id", ondelete="CASCADE"), index=True
	)
	chunk_text: Mapped[str] = mapped_column(Text)
	chunk_index: Mapped[int] = mapped_column(Integer)
	embedding_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

	document = relationship("KnowledgeDocument", back_populates="chunks")
