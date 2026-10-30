"""Customer table from the approved retail database design."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Customer(Base):
	__tablename__ = "customers"

	customer_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String(100))
	email: Mapped[str] = mapped_column(String(150), unique=True)

	sales = relationship("Sale", back_populates="customer")
