"""Chat request and response schemas  ->  app/schemas/chat.py"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
	role: Literal["user", "assistant"]
	content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
	conversation_id: int = Field(gt=0)
	message: str = Field(min_length=1, max_length=2000)
	selected_product_id: int | None = Field(default=None, gt=0)


class ChatEvent(BaseModel):
	"""One tool the assistant used while answering."""
	tool: str
	args: dict[str, Any] = Field(default_factory=dict)
	ms: int
	status: str


class ChatResponse(BaseModel):
	conversation_id: int
	reply: str
	ref: str                       # short reference that also appears in logs/chat.log
	duration_ms: int
	model: str
	events: list[ChatEvent] = Field(default_factory=list)


class ChatLogResponse(BaseModel):
	source: str
	lines: list[str] = Field(default_factory=list)


class ConversationCreate(BaseModel):
	title: str | None = Field(default=None, min_length=1, max_length=200)


class ConversationSummary(BaseModel):
	conversation_id: int
	title: str
	created_at: datetime
	updated_at: datetime
	message_count: int
	last_message: str | None = None


class SavedChatMessage(BaseModel):
	message_id: int
	role: Literal["user", "assistant"]
	content: str
	created_at: datetime
	ref: str | None = None
	model: str | None = None
	duration_ms: int | None = None


class ConversationDetail(ConversationSummary):
	messages: list[SavedChatMessage] = Field(default_factory=list)