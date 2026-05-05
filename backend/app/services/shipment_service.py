from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.orm import Session

from app.integrations.couriers.registry import CourierRegistry
from app.models.address import Address
from app.models.booking import Booking
from app.models.quote import Quote
from app.models.tracking_event import TrackingEvent
from app.models.user import User

logger = structlog.get_logger()


def _build_adapter_payload(*, db: Session, booking: Booking) -> dict:
    """Assemble the full shipment request payload expected by courier adapters."""
    quote = db.get(Quote, booking.quote_id) if booking.quote_id else None

    pickup_addr: dict | None = None
    delivery_addr: dict | None = None
    if quote:
        if quote.pickup_address_id:
            a = db.get(Address, quote.pickup_address_id)
            if a:
                pickup_addr = {
                    "line1": a.line1, "line2": a.line2, "suburb": a.suburb,
                    "city": a.city, "province": a.province, "postal_code": a.postal_code,
                    "country_code": a.country_code, "latitude": a.latitude, "longitude": a.longitude,
                }
        else:
            pickup_addr = quote.pickup_address_snapshot
        if quote.delivery_address_id:
            a = db.get(Address, quote.delivery_address_id)
            if a:
                delivery_addr = {
                    "line1": a.line1, "line2": a.line2, "suburb": a.suburb,
                    "city": a.city, "province": a.province, "postal_code": a.postal_code,
                    "country_code": a.country_code, "latitude": a.latitude, "longitude": a.longitude,
                }
        else:
            delivery_addr = quote.delivery_address_snapshot

    # Contacts
    if booking.user_id:
        user = db.get(User, booking.user_id)
        collection_contact = {"name": user.email if user else "Sender", "email": user.email if user else "", "mobile_number": ""}
        delivery_contact = {"name": "Recipient", "email": user.email if user else "", "mobile_number": ""}
    else:
        collection_contact = {"name": "Sender", "email": booking.guest_email or "", "mobile_number": booking.guest_phone or ""}
        delivery_contact = {"name": "Recipient", "email": booking.guest_email or "", "mobile_number": booking.guest_phone or ""}

    parcel = (quote.parcel if quote else {}) or {}

    return {
        "id": str(booking.id),
        "short_code": booking.public_short_code,
        "collection_address": pickup_addr or {},
        "delivery_address": delivery_addr or {},
        "collection_contact": collection_contact,
        "delivery_contact": delivery_contact,
        "parcels": [parcel] if parcel else [],
        "service_level_code": booking.courier_service_level,
        "customer_reference": booking.public_short_code or str(booking.id),
        "declared_value": float(parcel.get("value_zar") or 0),
    }


async def create_shipment_for_booking(*, db: Session, booking_id: uuid.UUID, registry: CourierRegistry) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise ValueError("Booking not found")

    if booking.status != "paid":
        raise ValueError("Booking must be paid before creating shipment")

    if booking.external_shipment_id:
        return booking

    from app.models.courier import Courier

    courier = db.get(Courier, booking.courier_id)
    if not courier:
        raise ValueError("Courier not found")
    try:
        adapter = registry.get(courier.code)
    except KeyError:
        logger.warning("no_adapter_for_courier", courier_code=courier.code)
        raise ValueError(f"No adapter available for courier {courier.code}")

    payload = _build_adapter_payload(db=db, booking=booking)

    try:
        result = await adapter.create_shipment(booking=payload)
        booking.external_shipment_id = result.get("shipment_id")
        booking.tracking_reference = result.get("tracking_reference")
        booking.status = "shipment_created"
        booking.courier_payload = result.get("raw")

        event = TrackingEvent(
            booking_id=booking.id,
            status="created",
            description="Shipment created",
            occurred_at=datetime.now(timezone.utc),
        )
        db.add(event)

        db.commit()
        db.refresh(booking)

        logger.info("shipment_created", booking_id=booking.id, tracking_ref=booking.tracking_reference)
        return booking

    except Exception as e:
        logger.error("shipment_creation_failed", booking_id=booking.id, error=str(e))
        raise


async def refresh_tracking(*, db: Session, booking_id: uuid.UUID, registry: CourierRegistry) -> list[TrackingEvent]:
    booking = db.get(Booking, booking_id)
    if not booking or not booking.tracking_reference:
        raise ValueError("Booking not found or has no tracking reference")

    from app.models.courier import Courier

    courier = db.get(Courier, booking.courier_id)
    if not courier:
        raise ValueError("Courier not found")
    adapter = registry.get(courier.code)

    try:
        events_data = await adapter.track_shipment(tracking_reference=booking.tracking_reference)

        new_events = []
        for event_data in events_data:
            existing = (
                db.query(TrackingEvent)
                .filter(
                    TrackingEvent.booking_id == booking_id,
                    TrackingEvent.status == event_data["status"],
                    TrackingEvent.occurred_at == event_data["occurred_at"],
                )
                .first()
            )

            if not existing:
                event = TrackingEvent(
                    booking_id=booking_id,
                    status=event_data["status"],
                    description=event_data.get("description"),
                    location=event_data.get("location"),
                    occurred_at=event_data["occurred_at"],
                    raw_payload=event_data,
                )
                db.add(event)
                new_events.append(event)

        if new_events:
            db.commit()
            logger.info("tracking_refreshed", booking_id=booking_id, new_events=len(new_events))

        return new_events

    except Exception as e:
        logger.error("tracking_refresh_failed", booking_id=booking_id, error=str(e))
        raise
