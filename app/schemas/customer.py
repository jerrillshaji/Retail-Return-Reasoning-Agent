"""Customer API schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class CustomerRead(CustomerCreate):
	customer_id: int
	model_config = ConfigDict(from_attributes=True)
