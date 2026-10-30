from datetime import date

import pytest
from fastapi import HTTPException

from app.models.customer import Customer
from app.models.product import Product
from app.models.roles import Role
from app.models.sale import Sale
from app.models.user import User
from app.schemas.product import ProductCreate
from app.services.product import assign_product_to_email, create_product, delete_product, list_products


def test_product_can_be_created_and_listed(db):
	product = create_product(db, ProductCreate(product_name="Desk lamp", category="Home", brand="Example", price=24.5))

	assert product.product_id is not None
	assert [item.product_id for item in list_products(db)] == [product.product_id]


def test_identical_products_receive_different_generated_ids(db):
	data = ProductCreate(product_name="Desk lamp", category="Home", brand="Example", price=24.5)
	first = create_product(db, data)
	second = create_product(db, data)

	assert first.product_id != second.product_id
	assert [product.product_id for product in list_products(db)] == [first.product_id, second.product_id]


def test_client_cannot_choose_product_id():
	with pytest.raises(ValueError):
		ProductCreate(product_id=77, product_name="Desk lamp", category="Home", brand="Example", price=24.5)


def test_admin_can_assign_product_to_user_email(db):
	role = Role(role_name="retail_manager")
	db.add(role)
	db.flush()
	user = User(name="Store Manager", email="manager@example.com", password_hash="hash", role=role)
	db.add(user)
	product = create_product(db, ProductCreate(product_name="Desk lamp", category="Home", brand="Example", price=24.5))
	db.flush()

	assigned = assign_product_to_email(db, product.product_id, "MANAGER@example.com")

	assert assigned.owner_user_id == user.user_id
	assert assigned.owner_email == "manager@example.com"


def test_assignment_rejects_unknown_email_without_changing_owner(db):
	product = create_product(db, ProductCreate(product_name="Desk lamp", category="Home", brand="Example", price=24.5))

	with pytest.raises(HTTPException) as error:
		assign_product_to_email(db, product.product_id, "missing@example.com")

	assert error.value.status_code == 404
	assert product.owner_user_id is None


def test_product_without_related_records_can_be_deleted(db):
	product = create_product(db, ProductCreate(product_name="Desk lamp", category="Home", brand="Example", price=24.5))

	delete_product(db, product.product_id)

	assert db.get(Product, product.product_id) is None


def test_product_with_related_sale_cannot_be_deleted(db):
	product = create_product(db, ProductCreate(product_name="Desk lamp", category="Home", brand="Example", price=24.5))
	customer = Customer(name="Alice", email="alice@example.com")
	db.add(customer)
	db.flush()
	db.add(Sale(product_id=product.product_id, customer_id=customer.customer_id, sale_date=date(2024, 1, 15), quantity=1, unit_price=24.5))
	db.commit()

	with pytest.raises(HTTPException) as error:
		delete_product(db, product.product_id)

	assert error.value.status_code == 409
	assert db.get(Product, product.product_id) is not None
