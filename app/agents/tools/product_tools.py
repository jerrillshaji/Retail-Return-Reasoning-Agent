"""Product facts available to the reasoning workflow."""

from app.models.product import Product


def product_summary(product: Product) -> dict:
	return {
		"product_id": product.product_id,
		"name": product.product_name,
		"category": product.category,
		"brand": product.brand,
		"description": product.description,
		"price": str(product.price),
	}
