"""Cause and action synthesis over observed evidence."""

from app.services.recommendation import recommend_actions


def identify_causes(returns: dict, feedback: dict) -> tuple[list[dict], list[str], list[str]]:
	causes = []
	evidence = []
	for item in returns["top_reasons"]:
		proof = f"Return records: {item['reason']} occurred {item['count']} time(s)."
		evidence.append(proof)
		causes.append({
			"cause": item["reason"],
			"evidence": [f"Recorded on {item['count']} return(s)."],
			"confidence": "medium" if item["count"] >= 3 else "low",
			"source_type": "return",
		})
	for item in feedback["themes"]:
		proof = f"Customer feedback: {item['theme']} appeared in {item['count']} comment(s)."
		evidence.append(proof)
		causes.append({
			"cause": f"Customer-reported {item['theme']} concerns",
			"evidence": [f"Theme detected in {item['count']} feedback comment(s)."],
			"confidence": "medium" if item["count"] >= 3 else "low",
			"source_type": "feedback",
		})
	return causes[:6], evidence, recommend_actions(returns, feedback)
