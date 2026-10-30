"""Optional LLM explanation generation."""

import json
import time

from google.genai import errors, types

from app.agents.prompts import RETURN_REASONING_PROMPT
from app.core.config import settings
from app.llm.provider import get_gemini_client

RETRY_CODES = {429, 500, 503, 504}   # temporary problems worth retrying
ATTEMPTS = 3


def explain_report(report: dict) -> str | None:
	client = get_gemini_client()
	if client is None:
		return None
	contents = json.dumps(report, ensure_ascii=True)
	config = types.GenerateContentConfig(
		system_instruction=RETURN_REASONING_PROMPT,
		temperature=0.2,
	)
	for attempt in range(ATTEMPTS):
		try:
			response = client.models.generate_content(
				model=settings.gemini_chat_model,
				contents=contents,
				config=config,
			)
			return response.text
		except errors.APIError as exc:
			if exc.code not in RETRY_CODES or attempt == ATTEMPTS - 1:
				raise
			time.sleep(3 * (attempt + 1))