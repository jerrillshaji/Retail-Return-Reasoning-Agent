"""Schemas for agent findings and knowledge search."""

from pydantic import BaseModel, Field


class KnowledgeDocumentCreate(BaseModel):
	title: str = Field(min_length=1, max_length=250)
	source: str = Field(default="user-upload", max_length=500)
	text: str = Field(min_length=1, max_length=100000)


class KnowledgeSearchRequest(BaseModel):
	query: str = Field(min_length=1, max_length=2000)
	limit: int = Field(default=5, ge=1, le=20)
