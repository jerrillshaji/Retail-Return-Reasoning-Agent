"""Return request and response schemas with a keyword-safe module name."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ReturnCreate(BaseModel):
    sale_id: int = Field(gt=0)
    return_reason_id: int | None = Field(default=None, gt=0)
    return_date: date = Field(default_factory=date.today)
    returned_quantity: int = Field(gt=0)
    return_status: str = Field(default="Pending", max_length=50)
    refund_amount: float | None = Field(default=None, ge=0)


class ReturnRead(ReturnCreate):
    return_id: int
    model_config = ConfigDict(from_attributes=True)
