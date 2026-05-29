"""Tracking service for real-time shipment visibility."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import UUID

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.couriers.registry import CourierRegistry
from app.models.booking import Booking
from app.models.tracking_event import TrackingEvent
from app.models.tracking_webhook import TrackingWebhook

logger = structlog.get_logger()


class TrackingService:
    """Manage shipment tracking and webhook notifications."""

    @staticmethod
    async def refresh_tracking(
        *,
        db: Session,
        booking_id: UUID,
        registry: CourierRegistry,
    ) -> list[TrackingEvent]:
        """Refresh tracking events from courier API.

        Returns list of new/updated tracking events.
        """
        booking = db.get(Booking, booking_id)
        if not booking or not booking.tracking_reference:
            return []

        try:
            adapter = registry.get(booking.courier_id)
        except KeyError:
            logger.warning("tracking_adapter_not_found", booking_id=booking_id)
            return []

        try:
            events = await adapter.track_shipment(tracking_reference=booking.tracking_reference)
        except Exception as e:
            logger.error("tracking_refresh_failed", booking_id=booking_id, error=str(e))
            return []

        new_events = []
        for event_data in events:
            existing = db.scalar(
                select(TrackingEvent).where(
                    TrackingEvent.booking_id == booking_id,
                    TrackingEvent.status == event_data.get("status"),
                    TrackingEvent.occurred_at == event_data.get("occurred_at"),
                )
            )

            if not existing:
                event = TrackingEvent(
                    booking_id=booking_id,
                    status=event_data.get("status", "unknown"),
                    description=event_data.get("description", ""),
                    location=event_data.get("location"),
                    latitude=event_data.get("latitude"),
                    longitude=event_data.get("longitude"),
                    occurred_at=event_data.get("occurred_at", datetime.now(timezone.utc)),
                    raw_payload=event_data.get("raw", {}),
                )
                db.add(event)
                new_events.append(event)

        if new_events:
            db.commit()
            logger.info("tracking_events_created", booking_id=booking_id, count=len(new_events))

            await TrackingService.trigger_webhooks(db=db, booking_id=booking_id, events=new_events)

        return new_events

    @staticmethod
    async def trigger_webhooks(
        *,
        db: Session,
        booking_id: UUID,
        events: list[TrackingEvent],
    ) -> None:
        """Trigger tracking webhooks for subscribed external systems."""
        booking = db.get(Booking, booking_id)
        if not booking or not booking.user_id:
            return

        webhooks = db.scalars(
            select(TrackingWebhook).where(
                TrackingWebhook.user_id == booking.user_id,
                TrackingWebhook.is_active.is_(True),
            )
        )

        for webhook in webhooks:
            if not any(event.status in webhook.events for event in events):
                continue

            payload = {
                "booking_id": str(booking_id),
                "tracking_reference": booking.tracking_reference,
                "events": [
                    {
                        "status": e.status,
                        "description": e.description,
                        "location": e.location,
                        "occurred_at": e.occurred_at.isoformat(),
                    }
                    for e in events
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await TrackingService._send_webhook(
                url=webhook.url,
                payload=payload,
                secret=webhook.secret,
            )

            webhook.last_triggered_at = datetime.now(timezone.utc)
            db.add(webhook)

        db.commit()

    @staticmethod
    async def _send_webhook(*, url: str, payload: dict, secret: str) -> bool:
        """Send webhook to external system with HMAC signature."""
        try:
            payload_json = json.dumps(payload)
            signature = hmac.new(
                secret.encode(),
                payload_json.encode(),
                hashlib.sha256,
            ).hexdigest()

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={
                        "X-Send-it-Signature": f"sha256={signature}",
                        "Content-Type": "application/json",
                    },
                )

            if resp.status_code >= 400:
                logger.warning("webhook_failed", url=url, status=resp.status_code)
                return False

            logger.info("webhook_sent", url=url)
            return True

        except Exception as e:
            logger.error("webhook_send_error", url=url, error=str(e))
            return False

    @staticmethod
    def get_tracking_summary(*, db: Session, booking_id: UUID) -> dict:
        """Get tracking summary for a booking."""
        booking = db.get(Booking, booking_id)
        if not booking:
            return {}

        events = db.scalars(
            select(TrackingEvent)
            .where(TrackingEvent.booking_id == booking_id)
            .order_by(TrackingEvent.occurred_at)
        )

        event_list = [
            {
                "status": e.status,
                "description": e.description,
                "location": e.location,
                "latitude": e.latitude,
                "longitude": e.longitude,
                "occurred_at": e.occurred_at.isoformat(),
            }
            for e in events
        ]

        latest_event = event_list[-1] if event_list else None

        return {
            "booking_id": str(booking_id),
            "tracking_reference": booking.tracking_reference,
            "current_status": latest_event["status"] if latest_event else "unknown",
            "current_location": latest_event["location"] if latest_event else None,
            "current_coordinates": {
                "latitude": latest_event["latitude"],
                "longitude": latest_event["longitude"],
            } if latest_event and latest_event.get("latitude") else None,
            "events": event_list,
            "last_update": latest_event["occurred_at"] if latest_event else None,
        }
