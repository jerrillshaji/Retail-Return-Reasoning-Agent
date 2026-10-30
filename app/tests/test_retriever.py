from datetime import datetime
from unittest.mock import Mock

from langchain_core.documents import Document
import pytest

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.rag import retriever


@pytest.fixture
def embedding_api_key(monkeypatch):
    monkeypatch.setattr(retriever, "get_embedding_api_key", lambda: "test-key")


def add_chunk(db, title, source, text, chunk_index=0, embedding_reference=None):
    document = KnowledgeDocument(
        document_name=title,
        source=source,
        document_type="text",
        uploaded_at=datetime.now(),
    )
    db.add(document)
    db.flush()
    chunk = KnowledgeChunk(
        document_id=document.document_id,
        chunk_text=text,
        chunk_index=chunk_index,
        embedding_reference=embedding_reference,
    )
    db.add(chunk)
    db.commit()
    return chunk


@pytest.mark.usefixtures("embedding_api_key")
def test_retrieve_uses_chroma_results_and_appends_unindexed_sql_chunks(db, monkeypatch):
    indexed = add_chunk(
        db,
        "Battery guidance",
        "battery.md",
        "Battery drains quickly and will not hold charge.",
        embedding_reference="doc1-chunk0",
    )
    add_chunk(
        db,
        "Charging guidance",
        "charging.md",
        "Charging case fails after repeated use.",
    )
    vectorstore = Mock()
    vectorstore.similarity_search_with_relevance_scores.return_value = [
        (
            Document(
                page_content=indexed.chunk_text,
                metadata={
                    "document_id": indexed.document_id,
                    "document_name": "Battery guidance",
                    "chunk_index": indexed.chunk_index,
                },
            ),
            0.91,
        )
    ]
    monkeypatch.setattr(retriever, "get_vectorstore", lambda: vectorstore)

    results = retriever.retrieve(db, "battery drains quickly charging")

    assert results[0] == {
        "title": "Battery guidance",
        "source": "battery.md",
        "text": indexed.chunk_text,
        "score": 0.91,
    }
    assert results[1]["title"] == "Charging guidance"
    vectorstore.similarity_search_with_relevance_scores.assert_called_once_with(
        "battery drains quickly charging",
        k=5,
    )


@pytest.mark.usefixtures("embedding_api_key")
def test_retrieve_uses_sql_keyword_search_when_chroma_is_empty(db, monkeypatch):
    chunk = add_chunk(
        db,
        "Battery guidance",
        "battery.md",
        "Battery drains quickly and will not hold charge.",
    )
    vectorstore = Mock()
    vectorstore.similarity_search_with_relevance_scores.return_value = []
    monkeypatch.setattr(retriever, "get_vectorstore", lambda: vectorstore)

    results = retriever.retrieve(db, "battery drains")

    assert results[0]["text"] == chunk.chunk_text
    assert results[0]["score"] > 0


@pytest.mark.usefixtures("embedding_api_key")
def test_retrieve_logs_chroma_failure_and_falls_back_to_sql(db, monkeypatch, caplog):
    chunk = add_chunk(
        db,
        "Battery guidance",
        "battery.md",
        "Battery drains quickly and will not hold charge.",
    )
    vectorstore = Mock()
    vectorstore.similarity_search_with_relevance_scores.side_effect = RuntimeError("offline")
    monkeypatch.setattr(retriever, "get_vectorstore", lambda: vectorstore)

    results = retriever.retrieve(db, "battery drains")

    assert results[0]["text"] == chunk.chunk_text
    assert "Chroma knowledge search failed" in caplog.text


def test_retrieve_uses_sql_keyword_search_without_embedding_api_key(db, monkeypatch):
    chunk = add_chunk(
        db,
        "Battery guidance",
        "battery.md",
        "Battery drains quickly and will not hold charge.",
    )
    vectorstore = Mock()
    monkeypatch.setattr(retriever, "get_embedding_api_key", lambda: "")
    monkeypatch.setattr(retriever, "get_vectorstore", lambda: vectorstore)

    results = retriever.retrieve(db, "battery drains")

    assert results[0]["text"] == chunk.chunk_text
    vectorstore.similarity_search_with_relevance_scores.assert_not_called()
