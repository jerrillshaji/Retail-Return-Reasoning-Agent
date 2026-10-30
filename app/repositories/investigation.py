"""Investigation report data access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.investigation import Investigation


def latest_for_product(db: Session, product_id: int) -> Investigation | None:
	return db.scalar(
		select(Investigation)
		.where(Investigation.product_id == product_id)
		.order_by(Investigation.started_at.desc())
	)
