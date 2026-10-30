from datetime import date
from decimal import Decimal

from app.models import Customer, Product, ReturnRecord, ReturnReason, Sale
from app.services.return_analysis import analyze_returns


def test_return_rate_uses_returned_and_sold_units(db):
	product = Product(product_name="Jacket", category="Clothing", brand="Example", price=Decimal("50.00"))
	customer = Customer(name="Test Customer", email="test@example.com")
	db.add_all([product, customer])
	db.flush()
	sale = Sale(product_id=product.product_id, customer_id=customer.customer_id, sale_date=date(2026, 9, 1), quantity=100, unit_price=Decimal("50.00"))
	reason = ReturnReason(reason_name="Too small")
	db.add_all([sale, reason])
	db.flush()
	db.add_all([
		ReturnRecord(sale_id=sale.sale_id, return_reason_id=reason.return_reason_id, return_date=date(2026, 9, 5), returned_quantity=4),
		ReturnRecord(sale_id=sale.sale_id, return_reason_id=reason.return_reason_id, return_date=date(2026, 9, 6), returned_quantity=1),
	])
	db.commit()

	result = analyze_returns(db, product)

	assert result["total_returns"] == 5
	assert result["return_rate"] == 0.05
	assert result["top_reasons"] == [{"reason": "Too small", "count": 5}]
	assert result["sales_data_available"] is True


def test_missing_sales_does_not_create_return_rate(db):
	product = Product(product_name="Lamp", category="Home", brand="Example", price=Decimal("25.00"))
	db.add(product)
	db.commit()

	result = analyze_returns(db, product)

	assert result["total_returns"] == 0
	assert result["data_sufficient"] is False
	assert result["return_rate"] is None
	assert result["above_benchmark"] is None
	assert result["sales_data_available"] is False


def test_identical_products_keep_separate_return_analysis(db):
	first = Product(product_name="Wireless Earbuds", category="Electronics", brand="SoundMax", price=Decimal("49.99"))
	second = Product(product_name="Wireless Earbuds", category="Electronics", brand="SoundMax", price=Decimal("49.99"))
	customer = Customer(name="Test Customer", email="separate-analysis@example.com")
	db.add_all([first, second, customer])
	db.flush()
	db.add(Sale(
		product_id=first.product_id,
		customer_id=customer.customer_id,
		sale_date=date(2026, 9, 1),
		quantity=25,
		unit_price=Decimal("49.99"),
	))
	db.commit()

	first_result = analyze_returns(db, first)
	second_result = analyze_returns(db, second)

	assert first.product_id != second.product_id
	assert first_result["total_sales"] == 25
	assert second_result["total_sales"] == 0
	assert second_result["return_rate"] is None
	assert second_result["data_sufficient"] is False
