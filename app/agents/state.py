"""Data passed through the return investigation workflow."""

from typing import Any, TypedDict


class InvestigationState(TypedDict, total=False):
	product: dict[str, Any]
	query: str
	return_analysis: dict[str, Any]
	feedback_analysis: dict[str, Any]
	knowledge: list[dict[str, Any]]
	probable_causes: list[dict[str, Any]]
	recommendations: list[str]
	evidence: list[str]