"""Knowledge retrieval using Chroma semantic search with SQL keyword fallback."""

import logging

from chromadb.errors import ChromaError
from google.genai.errors import APIError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.repositories.knowledge import list_chunks
from app.rag.vector_store import get_embedding_api_key, get_vectorstore

logger = logging.getLogger(__name__)


def _keyword_results(chunks, query: str, limit: int) -> list[dict]:
	terms = set(query.lower().split())
	ranked = []
	for chunk in chunks:
		content_terms = set(chunk.chunk_text.lower().split())
		score = len(terms & content_terms) / max(len(terms), 1)
		ranked.append((score, chunk))
	ranked.sort(key=lambda pair: pair[0], reverse=True)
	return [
		{
			"title": chunk.document.document_name,
			"source": chunk.document.source,
			"text": chunk.chunk_text,
			"score": round(score, 4),
		}
		for score, chunk in ranked[:limit]
		if score > 0
	]


def retrieve(db: Session, query: str, limit: int = 5) -> list[dict]:
	chunks = list_chunks(db)
	if not chunks or limit <= 0:
		return []
	keyword_chunks = [chunk for chunk in chunks if chunk.embedding_reference is None]

	if not get_embedding_api_key():
		return _keyword_results(db, query, limit)

	try:
		vector_results = get_vectorstore().similarity_search_with_relevance_scores(query, k=limit)
	except (APIError, ChromaError, OSError, RuntimeError, ValueError):
		logger.exception("Chroma knowledge search failed; falling back to SQL keyword search")
		return _keyword_results(db, query, limit)

	vector_docs = [
		(document, score)
		for document, score in vector_results
		if score > 0
	]
	if not vector_docs:
		return _keyword_results(db, query, limit)

	document_ids = {
		document.metadata.get("document_id")
		for document, _ in vector_docs
		if document.metadata.get("document_id") is not None
	}
	documents = {
		document.document_id: document
		for document in db.scalars(
			select(KnowledgeDocument).where(KnowledgeDocument.document_id.in_(document_ids))
		)
	} if document_ids else {}
	results = [
		{
			"title": document.metadata.get("document_name")
			or (documents[document.metadata["document_id"]].document_name
			    if document.metadata.get("document_id") in documents else "Return guidance"),
			"source": documents[document.metadata["document_id"]].source
			if document.metadata.get("document_id") in documents else None,
			"text": document.page_content,
			"score": round(float(score), 4),
		}
		for document, score in vector_docs
	]

	vector_chunk_keys = {
		(document.metadata.get("document_id"), document.metadata.get("chunk_index"))
		for document, _ in vector_docs
	}
	unindexed_chunks = [
		chunk for chunk in keyword_chunks
		if (chunk.document_id, chunk.chunk_index) not in vector_chunk_keys
	]
	results.extend(_keyword_results(unindexed_chunks, query, limit - len(results)))
	return results[:limit]
