from app.rag.chunker import split_text
from app.rag.vector_store import cosine_similarity


def test_chunking_keeps_document_content():
	text = "word " * 1800

	chunks = split_text(text)

	assert len(chunks) > 1
	assert chunks[0].startswith("word")
	assert chunks[-1].endswith("word")


def test_cosine_similarity_handles_equal_and_mismatched_vectors():
	assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
	assert cosine_similarity([1.0], [1.0, 0.0]) == 0.0
