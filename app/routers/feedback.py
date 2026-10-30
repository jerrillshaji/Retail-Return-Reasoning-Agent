"""Customer feedback endpoints  ->  app/routers/feedback.py"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.customer_feedback import CustomerFeedback
from app.models.user import User
from app.routers.auth import get_current_user, require_roles
from app.schemas.customer_feedback import FeedbackCreate, FeedbackRead
from app.services.feedback import analyze_feedback
from app.services.product import add_feedback, get_product

router = APIRouter(prefix="/products/{product_id}/feedback", tags=["feedback"], dependencies=[Depends(require_roles("administrator", "retail_manager", "analyst", "quality_user"))])


@router.post("", response_model=FeedbackRead, status_code=201, dependencies=[Depends(require_roles("administrator", "retail_manager", "quality_user"))])
def post_feedback(
	product_id: int,
	data: FeedbackCreate,
	db: Session = Depends(get_db),
	user: User = Depends(get_current_user),
) -> CustomerFeedback:
	product = get_product(db, product_id, user)
	if data.sale_id is not None and all(sale.sale_id != data.sale_id for sale in product.sales):
		from fastapi import HTTPException

		raise HTTPException(status_code=400, detail="Sale does not belong to this product")
	if data.return_id is not None:
		from app.repositories.returns import list_returns

		if all(record.return_id != data.return_id for record in list_returns(db, product_id)):
			from fastapi import HTTPException

			raise HTTPException(status_code=400, detail="Return does not belong to this product")
	return add_feedback(db, data)


@router.get("")
def get_feedback(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
	product = get_product(db, product_id, user)
	return analyze_feedback(db, product)