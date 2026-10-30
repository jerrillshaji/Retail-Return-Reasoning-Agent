"""Customer feedback API schemas."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FeedbackCreate(BaseModel):
	sale_id: int | None = Field(default=None, gt=0)
	return_id: int | None = Field(default=None, gt=0)
	rating: int | None = Field(default=None, ge=1, le=5)
	feedback_text: str = Field(min_length=1, max_length=10000)
	feedback_date: date = Field(default_factory=date.today)

	@model_validator(mode="after")
	def require_reference(self):
		if self.sale_id is None and self.return_id is None:
			raise ValueError("Provide either sale_id or return_id")
		return self


class FeedbackRead(FeedbackCreate):
    feedback_id: int
    model_config = ConfigDict(from_attributes=True)
