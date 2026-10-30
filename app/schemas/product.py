"""Product API schemas matching the approved database design."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProductCreate(BaseModel):
	model_config = ConfigDict(extra="forbid")

	product_name: str = Field(min_length=1, max_length=150)
	category: str = Field(min_length=1, max_length=100)
	brand: str = Field(min_length=1, max_length=100)
	price: Decimal = Field(ge=0)
	description: str | None = None
	is_active: bool = True



class ProductRead(BaseModel):
	product_id: int
	product_name: str
	category: str
	brand: str
	price: Decimal
	description: str | None = None
	is_active: bool
	owner_email: EmailStr | None = None
	model_config = ConfigDict(from_attributes=True)


class ProductAssignRequest(BaseModel):
	email: EmailStr
