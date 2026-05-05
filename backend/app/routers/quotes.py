from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.integrations.couriers.registry import CourierRegistry
from app.models.quote import Quote
from app.models.user import User
from app.schemas.quote import (
    QuoteCreate,
    QuoteCreateGuest,
    QuoteEmailRequest,
    QuoteGuestOut,
    QuoteOut,
)
from app.services.quote_service import create_quote
from app.utils.tokens import issue_quote_token, verify_quote_token

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/", response_model=QuoteOut)
async def generate_quote(
    payload: QuoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Quote:
    try:
        return await create_quote(
            db=db,
            user_id=current_user.id,
            pickup_address_id=payload.pickup_address_id,
            delivery_address_id=payload.delivery_address_id,
            parcel=payload.parcel.model_dump(),
            urgency=payload.urgency,
            budget_zar=int(payload.budget_zar * 100) if payload.budget_zar else None,
            registry=CourierRegistry.from_db(db),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/guest", response_model=QuoteGuestOut)
async def generate_quote_guest(
    payload: QuoteCreateGuest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Create a quote without authentication.

    Returns a signed magic-link ``access_token`` that can be used to retrieve or
    convert the quote into a booking within ``GUEST_TOKEN_MAX_AGE_HOURS`` (72h
    default). Rate-limited per IP by SlowAPI middleware.
    """
    try:
        quote = await create_quote(
            db=db,
            user_id=None,
            pickup_address_id=None,
            delivery_address_id=None,
            pickup_snapshot=payload.pickup.model_dump(),
            delivery_snapshot=payload.delivery.model_dump(),
            parcel=payload.parcel.model_dump(),
            urgency=payload.urgency,
            budget_zar=int(payload.budget_zar * 100) if payload.budget_zar else None,
            guest_email=payload.email,
            guest_phone=payload.phone,
            registry=CourierRegistry.from_db(db),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = issue_quote_token(str(quote.id), email=payload.email)

    return {
        **QuoteOut.model_validate(quote).model_dump(),
        "access_token": token,
    }


@router.get("/by-token/{token}", response_model=QuoteOut)
def get_quote_by_token(token: str, db: Session = Depends(get_db)) -> Quote:
    try:
        payload = verify_quote_token(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    quote = db.get(Quote, uuid.UUID(payload["qid"]))
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.expires_at and quote.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Quote expired")
    return quote


@router.post("/{quote_id}/email", status_code=202)
def email_quote(
    quote_id: uuid.UUID, payload: QuoteEmailRequest, db: Session = Depends(get_db)
) -> dict:
    """Send the quote to the supplied email via the notifications outbox.

    Works for both authed and guest quotes; the caller must already know the
    quote ID (guest obtains it from the prior create-quote response). Actual
    email delivery is handled by the notifications worker (Week 2).
    """
    quote = db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.expires_at and quote.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Quote expired")

    # Stash the email so Week 2 notifications worker can pick it up.
    quote.guest_email = payload.email
    token = issue_quote_token(str(quote.id), email=payload.email)
    db.commit()
    return {"status": "queued", "access_token": token}


@router.get("/{quote_id}", response_model=QuoteOut)
def get_quote(
    quote_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Quote:
    quote = db.get(Quote, quote_id)
    if not quote or (quote.user_id and quote.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote
