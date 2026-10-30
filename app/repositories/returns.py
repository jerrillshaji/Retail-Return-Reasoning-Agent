"""Return record data access without reserved-keyword imports."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.returns import ReturnRecord
from app.models.sale import Sale


def list_returns(db: Session, product_id: int) -> list[ReturnRecord]:
    statement = (
        select(ReturnRecord)
        .join(Sale, ReturnRecord.sale_id == Sale.sale_id)
        .where(Sale.product_id == product_id)
        .order_by(ReturnRecord.return_date.desc())
    )
    return list(db.scalars(statement))
