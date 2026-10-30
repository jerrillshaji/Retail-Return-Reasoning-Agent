"""Return-analysis tool used by the reasoning workflow."""

from sqlalchemy.orm import Session

from app.models.product import Product
from app.services.return_analysis import analyze_returns


def get_return_evidence(db: Session, product: Product) -> dict:
	return analyze_returns(db, product)
