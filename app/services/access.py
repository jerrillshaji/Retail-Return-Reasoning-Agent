"""Who may see which products  ->  app/services/access.py

Rule: an administrator sees every product; every other role sees only the products
whose owner_user_id is their own user id.
"""

from app.models.product import Product
from app.models.user import User

ADMIN_ROLE = "administrator"


def sees_all_products(user: User) -> bool:
	return user.role.role_name == ADMIN_ROLE


def can_access_product(user: User, product: Product) -> bool:
	return sees_all_products(user) or product.owner_user_id == user.user_id
