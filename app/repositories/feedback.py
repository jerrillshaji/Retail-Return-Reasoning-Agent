"""Customer feedback data access."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.customer_feedback import CustomerFeedback
from app.models.returns import ReturnRecord
from app.models.sale import Sale


def list_feedback(db: Session, product_id: int) -> list[CustomerFeedback]:
	from_sale = CustomerFeedback.sale.has(Sale.product_id == product_id)
	from_return = CustomerFeedback.return_record.has(
		ReturnRecord.sale.has(Sale.product_id == product_id)
	)
	return list(db.scalars(select(CustomerFeedback).where(or_(from_sale, from_return))))
