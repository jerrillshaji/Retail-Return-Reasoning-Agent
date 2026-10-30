"""Customer feedback tool used by the reasoning workflow."""

from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.feedback import analyze_feedback


def get_feedback_evidence(db: Session, product: Product) -> dict:
	return analyze_feedback(db, product)
