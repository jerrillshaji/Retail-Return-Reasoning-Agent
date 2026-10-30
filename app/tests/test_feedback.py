from datetime import date
from decimal import Decimal

from app.models import Customer, CustomerFeedback, Product, Sale
from app.services.feedback import analyze_feedback


def test_feedback_detects_recurring_themes(db):
	product = Product(product_name="Headphones", category="Electronics", brand="Example", price=Decimal("80.00"))
	customer = Customer(name="Test Customer", email="feedback@example.com")
	db.add_all([product, customer])
	db.flush()
	sale = Sale(product_id=product.product_id, customer_id=customer.customer_id, sale_date=date(2026, 9, 1), quantity=1, unit_price=Decimal("80.00"))
	db.add(sale)
	db.flush()
	db.add_all([
		CustomerFeedback(sale_id=sale.sale_id, feedback_date=date(2026, 9, 1), rating=2, feedback_text="Battery stopped working"),
		CustomerFeedback(sale_id=sale.sale_id, feedback_date=date(2026, 9, 2), rating=3, feedback_text="Battery performance is poor"),
	])
	db.commit()

	result = analyze_feedback(db, product)

	assert result["feedback_count"] == 2
	assert result["average_rating"] == 2.5
	assert result["themes"][0] == {"theme": "functionality", "count": 2}
