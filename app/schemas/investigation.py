"""Investigation and report API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InvestigationRequest(BaseModel):
	product_id: str = Field(min_length=1, max_length=80)
	query: str = Field(default="Why are returns high?", min_length=1, max_length=2000)


class InvestigationRead(BaseModel):
	id: int
	product_id: str
	query: str
	status: str
	report: dict[str, Any]
	created_at: datetime
	model_config = ConfigDict(from_attributes=True)
