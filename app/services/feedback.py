"""Lightweight customer-feedback theme extraction."""

from collections import Counter

from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.feedback import list_feedback


THEMES = {
	"quality": {"broken", "defective", "damaged", "quality", "faulty", "stopped"},
	"fit_or_size": {"size", "small", "large", "fit", "tight", "loose"},
	"functionality": {"work", "working", "function", "feature", "performance", "battery"},
	"usability": {"difficult", "confusing", "instructions", "use", "setup", "complicated"},
	"delivery": {"delivery", "shipping", "late", "arrived", "package"},
	"expectation_mismatch": {"expected", "description", "picture", "different", "advertised"},
}


def analyze_feedback(db: Session, product: Product) -> dict:
	entries = list_feedback(db, product.product_id)
	theme_counts: Counter[str] = Counter()
	comments = []
	for entry in entries:
		words = set(entry.feedback_text.lower().split())
		for theme, terms in THEMES.items():
			if words & terms:
				theme_counts[theme] += 1
		comments.append({"rating": entry.rating, "comment": entry.feedback_text, "date": entry.feedback_date.isoformat()})
	ratings = [entry.rating for entry in entries if entry.rating is not None]
	return {
		"feedback_count": len(entries),
		"average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
		"themes": [{"theme": theme, "count": count} for theme, count in theme_counts.most_common()],
		"feedback": comments[:30],
		"data_sufficient": bool(entries),
	}
