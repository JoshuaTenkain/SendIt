from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.integrations.couriers.registry import CourierRegistry
from app.models.booking import Booking
from app.models.delivery_issue import DeliveryIssue
from app.models.tracking_event import TrackingEvent
from app.models.tracking_webhook import TrackingWebhook
from app.models.user import User
from app.schemas.tracking import (
    DeliveryIssueCreate,
    DeliveryIssueOut,
    DeliveryIssueResolve,
    TrackingEventOut,
    TrackingSummaryOut,
    TrackingWebhookCreate,
    TrackingWebhookOut,
)
from app.services.issue_service import IssueService
from app.services.tracking_service import TrackingService

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


@router.get("/{booking_id}/summary", response_model=TrackingSummaryOut)
def get_tracking_summary(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get tracking summary for a booking."""
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    return TrackingService.get_tracking_summary(db=db, booking_id=booking_id)


@router.post("/{booking_id}/refresh")
async def refresh_tracking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Manually refresh tracking from courier."""
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    registry = CourierRegistry.from_db(db)
    events = await TrackingService.refresh_tracking(db=db, booking_id=booking_id, registry=registry)

    return {
        "booking_id": str(booking_id),
        "new_events": len(events),
        "events": [
            {
                "status": e.status,
                "description": e.description,
                "location": e.location,
                "occurred_at": e.occurred_at.isoformat(),
            }
            for e in events
        ],
    }


@router.post("/{booking_id}/issues", response_model=DeliveryIssueOut, status_code=201)
def report_issue(
    booking_id: uuid.UUID,
    payload: DeliveryIssueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeliveryIssue:
    """Report a delivery issue."""
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        issue = IssueService.create_issue(
            db=db,
            booking_id=booking_id,
            issue_type=payload.issue_type,
            description=payload.description,
            photos=payload.photos,
        )
        return issue
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{booking_id}/issues", response_model=list[DeliveryIssueOut])
def list_issues(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DeliveryIssue]:
    """List all issues for a booking."""
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    return IssueService.list_issues(db=db, booking_id=booking_id)


@router.post("/issues/{issue_id}/resolve", response_model=DeliveryIssueOut)
def resolve_issue(
    issue_id: uuid.UUID,
    payload: DeliveryIssueResolve,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeliveryIssue:
    """Resolve a delivery issue (admin only)."""
    issue = db.get(DeliveryIssue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    booking = db.get(Booking, issue.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        resolved = IssueService.resolve_issue(
            db=db,
            issue_id=issue_id,
            resolution_type=payload.resolution_type,
            resolution_amount=payload.resolution_amount,
            resolution_notes=payload.resolution_notes,
        )
        return resolved
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhooks", response_model=TrackingWebhookOut, status_code=201)
def create_webhook(
    payload: TrackingWebhookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrackingWebhook:
    """Create a tracking webhook for external integrations."""
    import secrets

    webhook = TrackingWebhook(
        user_id=current_user.id,
        url=payload.url,
        events=payload.events,
        secret=secrets.token_urlsafe(32),
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.get("/webhooks", response_model=list[TrackingWebhookOut])
def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TrackingWebhook]:
    """List all tracking webhooks for current user."""
    return list(
        db.scalars(
            select(TrackingWebhook).where(TrackingWebhook.user_id == current_user.id)
        )
    )


@router.delete("/webhooks/{webhook_id}", status_code=204, response_model=None)
def delete_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a tracking webhook."""
    webhook = db.get(TrackingWebhook, webhook_id)
    if not webhook or webhook.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(webhook)
    db.commit()


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
