"""Return reason lookup API schema."""

from pydantic import BaseModel, ConfigDict


class ReturnReasonRead(BaseModel):
    return_reason_id: int
    reason_name: str
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)
