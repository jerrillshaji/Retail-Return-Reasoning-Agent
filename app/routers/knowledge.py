"""Knowledge document ingestion and semantic/keyword retrieval endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from datetime import datetime

from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.routers.auth import require_roles
from app.schemas.agent import KnowledgeDocumentCreate, KnowledgeSearchRequest
from app.rag.chunker import split_text
from app.rag.retriever import retrieve

router = APIRouter(prefix="/knowledge", tags=["knowledge"], dependencies=[Depends(require_roles("administrator", "retail_manager", "analyst", "quality_user"))])


@router.post("/documents", status_code=201, dependencies=[Depends(require_roles("administrator", "analyst"))])
def add_document(data: KnowledgeDocumentCreate, db: Session = Depends(get_db)) -> dict:
    chunks = split_text(data.text)
    document = KnowledgeDocument(
        document_name=data.title,
        source=data.source,
        document_type="text",
        uploaded_at=datetime.now(),
    )
    db.add(document)
    db.flush()
    for index, content in enumerate(chunks):
        db.add(KnowledgeChunk(
            document_id=document.document_id,
            chunk_text=content,
            chunk_index=index,
            embedding_reference=None,
        ))
    db.commit()
    return {"document_id": document.document_id, "title": data.title, "source": data.source, "chunks_created": len(chunks)}


@router.post("/search")
def search_knowledge(data: KnowledgeSearchRequest, db: Session = Depends(get_db)) -> dict:
    return {"query": data.query, "results": retrieve(db, data.query, data.limit)}