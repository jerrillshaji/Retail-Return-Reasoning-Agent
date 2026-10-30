"""Sales and product return endpoints  ->  app/routers/return.py"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.sale import Sale
from app.models.returns import ReturnRecord
from app.models.return_reason import ReturnReason
from app.models.user import User
from app.routers.auth import get_current_user, require_roles
from app.schemas.return_reason import ReturnReasonRead
from app.schemas.returns import ReturnCreate, ReturnRead
from app.schemas.sale import SaleCreate, SaleRead
from app.services.product import add_return, add_sale
from app.repositories.returns import list_returns

router = APIRouter(prefix="", tags=["returns"], dependencies=[Depends(require_roles("administrator", "retail_manager", "analyst", "quality_user"))])


@router.get("/return-reasons", response_model=list[ReturnReasonRead])
def get_return_reasons(db: Session = Depends(get_db)) -> list[ReturnReason]:
	from sqlalchemy import select

	return list(db.scalars(select(ReturnReason).order_by(ReturnReason.reason_name)))


@router.post("/sales", response_model=SaleRead, status_code=201, dependencies=[Depends(require_roles("administrator", "retail_manager"))])
def post_sale(data: SaleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Sale:
	return add_sale(db, data, user)


@router.post("/returns", response_model=ReturnRead, status_code=201, dependencies=[Depends(require_roles("administrator", "retail_manager"))])
def post_return(data: ReturnCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ReturnRecord:
	return add_return(db, data, user)


@router.get("/products/{product_id}/returns", response_model=list[ReturnRead])
def get_returns(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[ReturnRecord]:
	from app.services.product import get_product

	get_product(db, product_id, user)
	return list_returns(db, product_id)