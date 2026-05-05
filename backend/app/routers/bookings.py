from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.integrations.payments.payfast import payfast_client
from app.models.booking import Booking
from app.models.user import User
from app.schemas.booking import (
    BookingCancel,
    BookingCreate,
    BookingCreateGuest,
    BookingGuestOut,
    BookingOut,
)
from app.services.booking_service import create_booking
from app.utils.tokens import (
    issue_booking_token,
    verify_booking_token,
    verify_quote_token,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _build_payfast_payload(booking: Booking) -> dict:
    """Build PayFast checkout payload using config URLs (fixes prior bug where
    api_base was derived from the database URL)."""
    frontend_base = settings.frontend_base_url.rstrip("/")
    api_base = settings.api_base_url.rstrip("/")
    # Guest? use short-code tracking page; authed users go to dashboard booking page.
    if booking.user_id is None and booking.public_short_code:
        return_url = f"{frontend_base}/track/{booking.public_short_code}?status=success"
        cancel_url = f"{frontend_base}/track/{booking.public_short_code}?status=cancel"
    else:
        return_url = f"{frontend_base}/bookings/{booking.id}?status=success"
        cancel_url = f"{frontend_base}/bookings/{booking.id}?status=cancel"
    return payfast_client.generate_payment_data(
        amount=float(booking.price_total),
        item_name=f"Booking {booking.public_short_code or booking.id}",
        item_description=f"Courier shipment via {booking.courier_id}",
        m_payment_id=str(booking.id),
        return_url=return_url,
        cancel_url=cancel_url,
        notify_url=f"{api_base}/payments/payfast/notify",
    )


@router.post("/", response_model=BookingOut, status_code=201)
def create_booking_endpoint(
    payload: BookingCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Booking:
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")

    try:
        booking = create_booking(
            db=db,
            user_id=current_user.id,
            quote_id=payload.quote_id,
            courier_id=payload.courier_id,
            courier_service_level=payload.courier_service_level,
            idempotency_key=idempotency_key,
        )
        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/guest", response_model=BookingGuestOut, status_code=201)
def create_booking_guest(
    payload: BookingCreateGuest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Create a booking from a guest quote, using its magic-link token.

    Returns a booking-access token the client can use to track status without
    signing in.
    """
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")

    try:
        token_payload = verify_quote_token(payload.quote_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    quote_id = uuid.UUID(token_payload["qid"])

    try:
        booking = create_booking(
            db=db,
            user_id=None,
            quote_id=quote_id,
            courier_id=payload.courier_id,
            courier_service_level=payload.courier_service_level,
            idempotency_key=idempotency_key,
            guest_email=payload.email,
            guest_phone=payload.phone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token = issue_booking_token(str(booking.id), email=payload.email)
    return {
        **BookingOut.model_validate(booking).model_dump(),
        "access_token": access_token,
    }


@router.get("/", response_model=list[BookingOut])
def list_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Booking]:
    return list(
        db.scalars(
            select(Booking).where(Booking.user_id == current_user.id).order_by(Booking.created_at.desc())
        )
    )


@router.get("/by-token/{token}", response_model=BookingOut)
def get_booking_by_token(token: str, db: Session = Depends(get_db)) -> Booking:
    try:
        payload = verify_booking_token(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    booking = db.get(Booking, uuid.UUID(payload["bid"]))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/{booking_id}/payment", response_model=dict)
def initiate_payment(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "pending_payment":
        raise HTTPException(status_code=400, detail="Booking is not pending payment")
    return _build_payfast_payload(booking)


@router.post("/guest/{token}/payment", response_model=dict)
def initiate_payment_guest(token: str, db: Session = Depends(get_db)) -> dict:
    """Generate PayFast payload for a guest booking via its access token."""
    try:
        payload = verify_booking_token(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    booking = db.get(Booking, uuid.UUID(payload["bid"]))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "pending_payment":
        raise HTTPException(status_code=400, detail="Booking is not pending payment")
    return _build_payfast_payload(booking)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: uuid.UUID,
    payload: BookingCancel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status in ("cancelled", "delivered", "returned"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel in status {booking.status}")
    booking.status = "cancelled"
    booking.cancelled_at = datetime.now(timezone.utc)
    booking.cancel_reason = payload.reason
    db.commit()
    db.refresh(booking)
    return booking
