"""Product endpoints and return statistics  ->  app/routers/product.py"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.product import Product
from app.models.user import User
from app.routers.auth import get_current_user, require_roles
from app.schemas.product import ProductAssignRequest, ProductCreate, ProductRead
from app.services.product import assign_product_to_email, create_product, delete_product, get_product, list_products
from app.services.return_analysis import analyze_returns

router = APIRouter(prefix="/products", tags=["products"], dependencies=[Depends(require_roles("administrator", "retail_manager", "analyst", "quality_user"))])


@router.post("", response_model=ProductRead, status_code=201, dependencies=[Depends(require_roles("administrator", "retail_manager"))])
def post_product(
	data: ProductCreate,
	db: Session = Depends(get_db),
	user: User = Depends(get_current_user),
) -> Product:
	return create_product(db, data, user)


@router.get("", response_model=list[ProductRead])
def get_products(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Product]:
	return list_products(db, user)


@router.get("/{product_id}", response_model=ProductRead)
def get_product_by_id(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Product:
	return get_product(db, product_id, user)


@router.patch("/{product_id}/owner", response_model=ProductRead, dependencies=[Depends(require_roles("administrator"))])
def assign_product_owner(
	product_id: int,
	data: ProductAssignRequest,
	db: Session = Depends(get_db),
) -> Product:
	return assign_product_to_email(db, product_id, data.email)


@router.delete("/{product_id}", status_code=204, dependencies=[Depends(require_roles("administrator"))])
def remove_product(product_id: int, db: Session = Depends(get_db)) -> None:
	delete_product(db, product_id)


@router.get("/{product_id}/return-analysis")
def get_return_analysis(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
	return analyze_returns(db, get_product(db, product_id, user))