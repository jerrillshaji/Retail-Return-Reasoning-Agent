"""Sale API schemas."""

from datetime import date

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SaleCreate(BaseModel):
	product_id: int = Field(gt=0)
	customer_id: int = Field(gt=0)
	sale_date: date = Field(default_factory=date.today)
	quantity: int = Field(gt=0)
	unit_price: Decimal = Field(ge=0)


class SaleRead(SaleCreate):
    sale_id: int
    model_config = ConfigDict(from_attributes=True)
