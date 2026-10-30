"""Optional Google Gemini client factory  ->  app/llm/provider.py"""

from google import genai
from google.genai import types

from app.core.config import settings

REQUEST_TIMEOUT_MS = 60_000   # give up on a single Gemini request after 60 seconds


def get_gemini_client() -> genai.Client | None:
	if not settings.gemini_api_key:
		return None
	return genai.Client(
		api_key=settings.gemini_api_key,
		http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
	)