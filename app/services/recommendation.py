"""Deterministic recommendations tied to observed evidence."""


def recommend_actions(return_analysis: dict, feedback_analysis: dict) -> list[str]:
	actions = []
	reasons = {item["reason"].lower() for item in return_analysis["top_reasons"]}
	themes = {item["theme"] for item in feedback_analysis["themes"]}
	if "quality" in themes or any(term in " ".join(reasons) for term in ("defect", "broken", "damage")):
		actions.append("Inspect recent production lots and packaging; track defect rates before changing the listing.")
	if "fit_or_size" in themes or any(term in " ".join(reasons) for term in ("size", "fit")):
		actions.append("Review sizing guidance and product dimensions, then compare return rates by variant.")
	if "functionality" in themes:
		actions.append("Reproduce the reported functional issue and verify product instructions and quality checks.")
	if "usability" in themes:
		actions.append("Review setup instructions and consider clearer onboarding or product documentation.")
	if "delivery" in themes:
		actions.append("Compare return complaints with shipping and packaging records for affected orders.")
	if "expectation_mismatch" in themes:
		actions.append("Compare the product page text and images against the item customers receive.")
	if not actions:
		actions.append("Collect more return reasons and customer comments before selecting a corrective action.")
	return actions
