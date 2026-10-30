"""Investigation workflow and saved report endpoints  ->  app/routers/investigaton.py (keep your file name)"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.database.session import get_db
from app.models.investigation import Investigation
from app.models.user import User
from app.routers.auth import get_current_user, require_roles
from app.schemas.investigation import InvestigationRequest, InvestigationRead
from app.services.investigation import build_report, get_latest_investigation, save_investigation
from app.services.product import get_product

router = APIRouter(tags=["investigations"], dependencies=[Depends(require_roles("administrator", "retail_manager", "analyst", "quality_user"))])


@router.post("/investigate", response_model=InvestigationRead)
def investigate(
	data: InvestigationRequest,
	db: Session = Depends(get_db),
	user: User = Depends(get_current_user),
) -> dict:
	product = get_product(db, data.product_id, user)
	report = build_report(db, product, data.query)
	saved = save_investigation(db, product.product_id, data.query, report, user.user_id)
	return investigation_response(saved, report)


@router.post("/investigate/{product_id}/report", response_model=InvestigationRead)
def generate_report(
	product_id: int,
	query: str = Query(default="Why are returns high?", min_length=1, max_length=2000),
	db: Session = Depends(get_db),
	user: User = Depends(get_current_user),
 ) -> dict:
	product = get_product(db, product_id, user)
	report = build_report(db, product, query)
	saved = save_investigation(db, product.product_id, query, report, user.user_id)
	return investigation_response(saved, report)


@router.get("/investigate/{product_id}/report", response_model=InvestigationRead)
def latest_report(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
	product = get_product(db, product_id, user)
	result = get_latest_investigation(db, product_id)
	if result is None:
		raise not_found("Investigation")
	return investigation_response(result, build_report(db, product, result.query))


def investigation_response(investigation: Investigation, report: dict) -> dict:
	return {
		"investigation_id": investigation.investigation_id,
		"product_id": investigation.product_id,
		"query": investigation.query,
		"status": investigation.status,
		"started_at": investigation.started_at,
		"report": report,
	}