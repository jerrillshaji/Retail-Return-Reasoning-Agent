"""Sales table from the approved retail database design."""

from datetime import date

from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Sale(Base):
	__tablename__ = "sales"

	sale_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id", ondelete="RESTRICT"), index=True)
	customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id", ondelete="RESTRICT"), index=True)
	sale_date: Mapped[date] = mapped_column(Date)
	quantity: Mapped[int] = mapped_column(Integer)
	unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

	product = relationship("Product", back_populates="sales")
	customer = relationship("Customer", back_populates="sales")
	returns = relationship("ReturnRecord", back_populates="sale")
