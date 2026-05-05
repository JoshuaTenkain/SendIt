from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.booking import Booking
from app.models.tracking_event import TrackingEvent
from app.models.user import User
from app.schemas.tracking import TrackingEventOut

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.get("/{booking_id}", response_model=list[TrackingEventOut])
def get_tracking_events(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TrackingEvent]:
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    events = list(
        db.scalars(
            select(TrackingEvent)
            .where(TrackingEvent.booking_id == booking_id)
            .order_by(TrackingEvent.occurred_at.asc())
        )
    )
    return events


@router.get("/public/{short_code}", response_model=dict)
def public_tracking(short_code: str, db: Session = Depends(get_db)) -> dict:
    """Public tracking page by short code — no auth, no PII."""
    short_code = short_code.upper()
    booking = db.scalar(select(Booking).where(Booking.public_short_code == short_code))
    if not booking:
        raise HTTPException(status_code=404, detail="Not found")

    events = list(
        db.scalars(
            select(TrackingEvent)
            .where(TrackingEvent.booking_id == booking.id)
            .order_by(TrackingEvent.occurred_at.asc())
        )
    )

    return {
        "short_code": booking.public_short_code,
        "status": booking.status,
        "tracking_reference": booking.tracking_reference,
        "service_level": booking.courier_service_level,
        "created_at": booking.created_at,
        "events": [
            {
                "status": ev.status,
                "description": ev.description,
                "location": ev.location,
                "occurred_at": ev.occurred_at,
            }
            for ev in events
        ],
    }
