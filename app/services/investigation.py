"""Evidence-first investigation report orchestration."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.investigation import Investigation
from app.models.investigation_finding import InvestigationFinding
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.models.returns import ReturnRecord
from app.models.sale import Sale
from app.models.finding_evidence import FindingEvidence
from app.agents.return_reasoning_agent import investigate_product
from app.repositories.investigation import latest_for_product
from app.repositories.feedback import list_feedback


def build_report(db: Session, product: Product, query: str) -> dict:
	state = investigate_product(db, product, query)
	returns = state["return_analysis"]
	feedback = state["feedback_analysis"]
	knowledge = state["knowledge"]
	report = {**state, "uncertainty": [], "interpretation": None}
	if not returns["data_sufficient"]:
		report["uncertainty"].append("No return records are available for this product.")
	if not returns["sales_data_available"]:
		report["uncertainty"].append("Sales data is missing; a return rate cannot be calculated.")
	if not feedback["data_sufficient"]:
		report["uncertainty"].append("No customer feedback is available for this product.")
	if not knowledge:
		report["uncertainty"].append("No matching knowledge-base documents were retrieved.")
	if returns["return_rate"] is not None and returns["return_rate"] < settings.return_rate_threshold:
		report["uncertainty"].append("The recorded return rate is below the configured high-return threshold.")

	try:
		from app.llm.client import explain_report

		report["interpretation"] = explain_report(report)
	except Exception:
		report["uncertainty"].append("LLM explanation was unavailable; deterministic findings are shown.")
	return report


def save_investigation(db: Session, product_id: int, query: str, report: dict) -> Investigation:
	now = datetime.now()
	investigation = Investigation(
		product_id=product_id,
		query=query,
		started_at=now,
		completed_at=now,
		status="Completed",
	)
	db.add(investigation)
	db.flush()
	for item in report["probable_causes"]:
		confidence = {"low": 0.35, "medium": 0.65, "high": 0.9}.get(item["confidence"], 0.5)
		finding = InvestigationFinding(
			investigation_id=investigation.investigation_id,
			finding_type=item["source_type"],
			finding_text=item["cause"],
			confidence=confidence,
		)
		db.add(finding)
		db.flush()
		if item["source_type"] == "return":
			rows = db.scalars(
				select(ReturnRecord)
				.join(Sale, ReturnRecord.sale_id == Sale.sale_id)
				.where(Sale.product_id == product_id)
			).all()
			for row in rows:
				if row.reason and row.reason.reason_name == item["cause"]:
					db.add(FindingEvidence(finding_id=finding.finding_id, source_type="return", source_id=row.return_id))
		elif item["source_type"] == "feedback":
			for row in list_feedback(db, product_id):
				db.add(FindingEvidence(finding_id=finding.finding_id, source_type="feedback", source_id=row.feedback_id))
	for action in report["recommendations"]:
		db.add(Recommendation(investigation_id=investigation.investigation_id, recommendation_text=action))
	db.commit()
	db.refresh(investigation)
	return investigation


def get_latest_investigation(db: Session, product_id: int) -> Investigation | None:
	return latest_for_product(db, product_id)
