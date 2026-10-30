"""Optional Gemini document embeddings."""

from app.core.config import settings
from app.llm.provider import get_gemini_client


def embed_texts(texts: list[str]) -> list[list[float]] | None:
	client = get_gemini_client()
	if client is None or not texts:
		return None
	response = client.models.embed_content(model=settings.gemini_embedding_model, contents=texts)
	return [item.values for item in response.embeddings]
