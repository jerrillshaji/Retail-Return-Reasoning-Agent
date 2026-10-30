"""Split knowledge documents into overlapping text chunks."""

from app.core.config import settings


def split_text(text: str) -> list[str]:
	words = text.split()
	size = max(settings.chunk_size, 50)
	overlap = min(settings.chunk_overlap, size // 2)
	chunks = []
	start = 0
	while start < len(words):
		end = min(start + size, len(words))
		chunks.append(" ".join(words[start:end]))
		if end == len(words):
			break
		start = end - overlap
	return chunks
