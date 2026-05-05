from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models.booking import Booking
from app.models.commission_record import CommissionRecord
from app.models.courier import Courier
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.booking import BookingOut
from app.schemas.courier import CourierOut, CourierUpdate
from app.schemas.transaction import TransactionOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/couriers", response_model=list[CourierOut])
def list_couriers(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Courier]:
    return list(db.scalars(select(Courier).order_by(Courier.name)))


@router.patch("/couriers/{courier_id}", response_model=CourierOut)
def update_courier(
    courier_id: uuid.UUID,
    payload: CourierUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Courier:
    courier = db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(courier, field, value)

    db.commit()
    db.refresh(courier)
    return courier


@router.get("/bookings", response_model=list[BookingOut])
def list_all_bookings(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Booking]:
    return list(db.scalars(select(Booking).order_by(Booking.created_at.desc()).limit(100)))


@router.get("/transactions", response_model=list[TransactionOut])
def list_all_transactions(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    return list(db.scalars(select(Transaction).order_by(Transaction.created_at.desc()).limit(100)))


@router.get("/revenue", response_model=dict)
def get_revenue_summary(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    total_revenue = db.scalar(
        select(func.sum(Transaction.amount)).where(Transaction.status == "completed")
    ) or 0

    total_commission = db.scalar(
        select(func.sum(CommissionRecord.commission_amount))
    ) or 0

    booking_count = db.scalar(select(func.count(Booking.id)))

    return {
        "total_revenue": float(total_revenue),
        "total_commission": float(total_commission),
        "booking_count": booking_count,
        "currency": "ZAR",
    }
