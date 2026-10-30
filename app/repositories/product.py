"""Product data access  ->  app/repositories/product.py"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product


def get_product(db: Session, product_id: int) -> Product | None:
	return db.get(Product, product_id)


def list_products(db: Session, owner_user_id: int | None = None) -> list[Product]:
	"""All products, or only the products owned by one user."""
	query = select(Product).order_by(Product.product_name)
	if owner_user_id is not None:
		query = query.where(Product.owner_user_id == owner_user_id)
	return list(db.scalars(query))