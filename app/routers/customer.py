"""Customer creation endpoint required before importing or recording sales."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.customer import Customer
from app.routers.auth import require_roles
from app.schemas.customer import CustomerCreate, CustomerRead
from app.services.product import create_customer

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(require_roles("administrator", "retail_manager", "analyst", "quality_user"))],
)


@router.post("", response_model=CustomerRead, status_code=201, dependencies=[Depends(require_roles("administrator", "retail_manager"))])
def post_customer(data: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    existing = db.scalar(select(Customer).where(Customer.email == data.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Customer email already exists")
    return create_customer(db, data)
