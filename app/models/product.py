"""Product table from the approved retail database design."""

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Product(Base):
	__tablename__ = "products"

	product_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	product_name: Mapped[str] = mapped_column(String(150))
	category: Mapped[str] = mapped_column(String(100))
	brand: Mapped[str] = mapped_column(String(100))
	price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
	description: Mapped[str | None] = mapped_column(Text, nullable=True)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True)
	owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
	owner = relationship("User", foreign_keys=[owner_user_id])
	sales = relationship("Sale", back_populates="product")
	investigations = relationship("Investigation", back_populates="product")

	@property
	def owner_email(self) -> str | None:
		return self.owner.email if self.owner else None
