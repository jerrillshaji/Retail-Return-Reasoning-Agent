"""Knowledge chunk data access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk


def list_chunks(db: Session) -> list[KnowledgeChunk]:
	return list(db.scalars(select(KnowledgeChunk)))
