"""Return statistics derived from stored sales and return records."""

from collections import Counter

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.product import Product
from app.repositories.returns import list_returns


def analyze_returns(db: Session, product: Product) -> dict:
	return_rows = list_returns(db, product.product_id)
	sales_rows = list(product.sales)
	returned_units = sum(row.returned_quantity for row in return_rows)
	sold_units = sum(row.quantity for row in sales_rows)
	reasons: Counter[str] = Counter()
	for row in return_rows:
		reason_name = row.reason.reason_name if row.reason else "Unspecified"
		reasons[reason_name] += row.returned_quantity
	monthly = Counter(row.return_date.strftime("%Y-%m") for row in return_rows)
	benchmark = settings.return_rate_threshold
	rate = returned_units / sold_units if sold_units > 0 else None
	patterns = []
	if rate is not None and rate >= benchmark:
		patterns.append("The recorded return rate meets or exceeds the configured threshold.")
	if reasons and reasons.most_common(1)[0][1] >= max(2, len(return_rows) * 0.4):
		patterns.append(f"'{reasons.most_common(1)[0][0]}' is a recurring return reason.")

	return {
		"total_returns": returned_units,
		"total_sales": sold_units,
		"return_rate": round(rate, 4) if rate is not None else None,
		"benchmark": benchmark,
		"above_benchmark": rate >= benchmark if rate is not None else None,
		"top_reasons": [{"reason": reason, "count": count} for reason, count in reasons.most_common(5)],
		"monthly_returns": dict(sorted(monthly.items())),
		"patterns": patterns,
		"data_sufficient": bool(return_rows),
		"sales_data_available": sold_units > 0,
	}
