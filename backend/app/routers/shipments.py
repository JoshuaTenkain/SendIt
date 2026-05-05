from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.integrations.couriers.registry import CourierRegistry
from app.models.booking import Booking
from app.models.user import User
from app.services.shipment_service import create_shipment_for_booking, refresh_tracking

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.post("/{booking_id}/create")
async def create_shipment(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        await create_shipment_for_booking(db=db, booking_id=booking_id, registry=CourierRegistry())
        return {"status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{booking_id}/refresh-tracking")
async def refresh_tracking_endpoint(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        new_events = await refresh_tracking(db=db, booking_id=booking_id, registry=CourierRegistry())
        return {"new_events": len(new_events)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
