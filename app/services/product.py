"""Product and retail-record persistence helpers  ->  app/services/product.py"""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.customer_feedback import CustomerFeedback
from app.models.customer import Customer
from app.models.product import Product
from app.models.returns import ReturnRecord
from app.models.return_reason import ReturnReason
from app.models.sale import Sale
from app.models.user import User
from app.repositories.product import get_product as find_product
from app.repositories.product import list_products as find_products
from app.schemas.customer_feedback import FeedbackCreate
from app.schemas.customer import CustomerCreate
from app.schemas.product import ProductCreate
from app.schemas.returns import ReturnCreate
from app.schemas.sale import SaleCreate
from app.services.access import can_access_product, sees_all_products


def get_product(db: Session, product_id: int, user: User | None = None) -> Product:
	"""Find a product. When a user is given, products they may not see look like missing ones."""
	product = find_product(db, product_id)
	if product is None or (user is not None and not can_access_product(user, product)):
		raise not_found("Product")
	return product


def create_product(db: Session, data: ProductCreate, user: User | None = None) -> Product:
	product = Product(**data.model_dump())
	if user is not None and not sees_all_products(user):
		product.owner_user_id = user.user_id        # a non-admin owns what they create
	db.add(product)
	db.commit()
	db.refresh(product)
	return product


def list_products(db: Session, user: User | None = None) -> list[Product]:
	if user is None or sees_all_products(user):
		return find_products(db)
	return find_products(db, owner_user_id=user.user_id)


def assign_product_to_email(db: Session, product_id: int, email: str) -> Product:
	product = db.get(Product, product_id)
	if product is None:
		raise not_found("Product")
	owner = db.scalar(select(User).where(User.email == email.strip().lower()))
	if owner is None:
		raise not_found("User")
	product.owner_user_id = owner.user_id
	db.commit()
	db.refresh(product)
	return product


def delete_product(db: Session, product_id: int) -> None:
	product = db.get(Product, product_id)
	if product is None:
		raise not_found("Product")

	sales_count = db.scalar(select(func.count()).select_from(Sale).where(Sale.product_id == product_id))
	investigation_count = db.scalar(
		select(func.count()).select_from(Product.investigations.property.mapper.class_)
		.where(Product.investigations.property.mapper.class_.product_id == product_id)
	)
	if sales_count or investigation_count:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="This product has sales or investigation history and cannot be deleted.",
		)

	db.delete(product)
	try:
		db.commit()
	except IntegrityError as exc:
		db.rollback()
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="This product has related records and cannot be deleted.",
		) from exc


def create_customer(db: Session, data: CustomerCreate) -> Customer:
	customer = Customer(**data.model_dump())
	db.add(customer)
	db.commit()
	db.refresh(customer)
	return customer


def add_sale(db: Session, data: SaleCreate, user: User | None = None) -> Sale:
	get_product(db, data.product_id, user)
	if db.get(Customer, data.customer_id) is None:
		raise not_found("Customer")
	sale = Sale(**data.model_dump())
	db.add(sale)
	db.commit()
	db.refresh(sale)
	return sale


def add_return(db: Session, data: ReturnCreate, user: User | None = None) -> ReturnRecord:
	sale = db.get(Sale, data.sale_id)
	if sale is None:
		raise not_found("Sale")
	if user is not None:
		get_product(db, sale.product_id, user)       # sales of products the user may not see look missing
	if data.return_reason_id is not None and db.get(ReturnReason, data.return_reason_id) is None:
		raise not_found("Return reason")
	record = ReturnRecord(**data.model_dump())
	db.add(record)
	db.commit()
	db.refresh(record)
	return record


def add_feedback(db: Session, data: FeedbackCreate) -> CustomerFeedback:
	if data.sale_id is not None and db.get(Sale, data.sale_id) is None:
		raise not_found("Sale")
	if data.return_id is not None and db.get(ReturnRecord, data.return_id) is None:
		raise not_found("Return")
	feedback = CustomerFeedback(**data.model_dump())
	db.add(feedback)
	db.commit()
	db.refresh(feedback)
	return feedback