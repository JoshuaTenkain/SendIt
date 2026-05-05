from __future__ import annotations

import asyncio
import secrets
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.commission_record import CommissionRecord
from app.models.courier import Courier
from app.models.quote import Quote
from app.models.transaction import Transaction


def _generate_short_code() -> str:
    """Short human-friendly public code for guest tracking URLs (12 chars)."""
    return secrets.token_urlsafe(9).replace("-", "A").replace("_", "B")[:12].upper()


def _match_quote_result(quote: Quote, courier_code: str, courier_service_level: str | None) -> dict | None:
    if not quote.results or "quotes" not in quote.results:
        return None
    for q in quote.results["quotes"]:
        if q["courier_code"] == courier_code:
            if courier_service_level is None or q["service_level"] == courier_service_level:
                return q
    return None


def create_booking(
    *,
    db: Session,
    user_id: uuid.UUID | None,
    quote_id: uuid.UUID,
    courier_id: uuid.UUID,
    courier_service_level: str | None,
    idempotency_key: str,
    # Guest flow
    guest_email: str | None = None,
    guest_phone: str | None = None,
) -> Booking:
    # Idempotency: match on (user_id, key) for authed; (guest_email, key) for guest
    if user_id is not None:
        existing = (
            db.query(Booking)
            .filter(Booking.user_id == user_id, Booking.idempotency_key == idempotency_key)
            .first()
        )
    elif guest_email:
        existing = (
            db.query(Booking)
            .filter(Booking.guest_email == guest_email, Booking.idempotency_key == idempotency_key)
            .first()
        )
    else:
        existing = None
    if existing:
        return existing

    quote = db.get(Quote, quote_id)
    if not quote:
        raise ValueError("Invalid quote")

    # Ownership: authed users can only book their own quotes; guest quotes have no user_id
    if user_id is not None:
        if quote.user_id is not None and quote.user_id != user_id:
            raise ValueError("Invalid quote")
    else:
        if quote.user_id is not None:
            raise ValueError("Invalid quote")

    courier = db.get(Courier, courier_id)
    if not courier or not courier.is_enabled:
        raise ValueError("Invalid courier")

    matching_quote = _match_quote_result(quote, courier.code, courier_service_level)
    if not matching_quote:
        raise ValueError("Selected courier not in quote results")

    price_cents = int(matching_quote["price_total"])
    markup_cents = int(price_cents * courier.base_markup_pct / 100)
    subtotal_cents = price_cents + markup_cents
    tax_cents = 0
    total_cents = subtotal_cents + tax_cents

    booking = Booking(
        user_id=user_id,
        guest_email=guest_email if user_id is None else None,
        guest_phone=guest_phone if user_id is None else None,
        quote_id=quote_id,
        courier_id=courier_id,
        courier_service_level=courier_service_level or matching_quote["service_level"],
        price_subtotal=Decimal(subtotal_cents) / 100,
        price_tax=Decimal(tax_cents) / 100,
        price_total=Decimal(total_cents) / 100,
        currency="ZAR",
        status="pending_payment",
        idempotency_key=idempotency_key,
        public_short_code=_generate_short_code(),
        pricing_breakdown=matching_quote.get("pricing_breakdown"),
    )
    db.add(booking)

    transaction = Transaction(
        booking_id=booking.id,
        provider="payfast",
        status="pending",
        amount=booking.price_total,
        currency=booking.currency,
    )
    db.add(transaction)

    db.commit()
    db.refresh(booking)
    return booking


async def confirm_payment(*, db: Session, booking_id: uuid.UUID, provider_reference: str, raw_payload: dict) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise ValueError("Booking not found")

    if booking.status != "pending_payment":
        return booking

    transaction = db.query(Transaction).filter(Transaction.booking_id == booking_id).first()
    if not transaction:
        raise ValueError("Transaction not found")

    transaction.status = "completed"
    transaction.provider_reference = provider_reference
    transaction.raw_payload = raw_payload

    booking.status = "paid"

    courier = db.get(Courier, booking.courier_id)
    if courier:
        commission_amount = booking.price_total * Decimal(courier.commission_pct) / 100
        commission_record = CommissionRecord(
            booking_id=booking.id,
            courier_id=courier.id,
            commission_pct=courier.commission_pct,
            commission_amount=commission_amount,
            currency=booking.currency,
        )
        db.add(commission_record)

    db.commit()
    db.refresh(booking)

    asyncio.create_task(_create_shipment_background(booking_id))

    return booking


async def _create_shipment_background(booking_id: uuid.UUID) -> None:
    from app.database import SessionLocal
    from app.integrations.couriers.registry import CourierRegistry
    from app.services.shipment_service import create_shipment_for_booking

    db = SessionLocal()
    try:
        await create_shipment_for_booking(
            db=db, booking_id=booking_id, registry=CourierRegistry.from_db(db)
        )
    except Exception:
        pass
    finally:
        db.close()
