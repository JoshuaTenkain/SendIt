"""Delivery issue service for tracking and resolving delivery problems."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery_issue import DeliveryIssue

logger = structlog.get_logger()


class IssueService:
    """Manage delivery issues and resolutions."""

    VALID_ISSUE_TYPES = {
        "delivery_failed": "Delivery Failed",
        "package_damaged": "Package Damaged",
        "package_lost": "Package Lost",
        "wrong_address": "Wrong Address",
        "recipient_unavailable": "Recipient Unavailable",
        "other": "Other",
    }

    VALID_RESOLUTIONS = {
        "refund": "Full Refund",
        "reship": "Reship Package",
        "credit": "Account Credit",
        "partial_refund": "Partial Refund",
    }

    @staticmethod
    def create_issue(
        *,
        db: Session,
        booking_id: UUID,
        issue_type: str,
        description: str,
        photos: list[str] | None = None,
    ) -> DeliveryIssue:
        """Create a new delivery issue."""
        if issue_type not in IssueService.VALID_ISSUE_TYPES:
            raise ValueError(f"Invalid issue type: {issue_type}")

        issue = DeliveryIssue(
            booking_id=booking_id,
            issue_type=issue_type,
            description=description,
            photos=photos or [],
            status="open",
        )
        db.add(issue)
        db.commit()
        db.refresh(issue)

        logger.info(
            "delivery_issue_created",
            issue_id=issue.id,
            booking_id=booking_id,
            issue_type=issue_type,
        )
        return issue

    @staticmethod
    def get_issue(*, db: Session, issue_id: UUID) -> DeliveryIssue | None:
        """Get a delivery issue by ID."""
        return db.get(DeliveryIssue, issue_id)

    @staticmethod
    def list_issues(*, db: Session, booking_id: UUID) -> list[DeliveryIssue]:
        """List all issues for a booking."""
        return list(
            db.scalars(
                select(DeliveryIssue)
                .where(DeliveryIssue.booking_id == booking_id)
                .order_by(DeliveryIssue.created_at.desc())
            )
        )

    @staticmethod
    def resolve_issue(
        *,
        db: Session,
        issue_id: UUID,
        resolution_type: str,
        resolution_amount: int | None = None,
        resolution_notes: str | None = None,
    ) -> DeliveryIssue | None:
        """Resolve a delivery issue."""
        if resolution_type not in IssueService.VALID_RESOLUTIONS:
            raise ValueError(f"Invalid resolution type: {resolution_type}")

        issue = db.get(DeliveryIssue, issue_id)
        if not issue:
            return None

        issue.status = "resolved"
        issue.resolution_type = resolution_type
        issue.resolution_amount = resolution_amount
        issue.resolution_notes = resolution_notes
        issue.resolved_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(issue)

        logger.info(
            "delivery_issue_resolved",
            issue_id=issue_id,
            resolution_type=resolution_type,
            amount=resolution_amount,
        )
        return issue

    @staticmethod
    def reject_issue(
        *,
        db: Session,
        issue_id: UUID,
        rejection_reason: str,
    ) -> DeliveryIssue | None:
        """Reject a delivery issue."""
        issue = db.get(DeliveryIssue, issue_id)
        if not issue:
            return None

        issue.status = "rejected"
        issue.resolution_notes = f"Rejected: {rejection_reason}"
        issue.resolved_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(issue)

        logger.info("delivery_issue_rejected", issue_id=issue_id)
        return issue

    @staticmethod
    def add_photo(
        *,
        db: Session,
        issue_id: UUID,
        photo_url: str,
    ) -> DeliveryIssue | None:
        """Add a photo to a delivery issue."""
        issue = db.get(DeliveryIssue, issue_id)
        if not issue:
            return None

        if photo_url not in issue.photos:
            issue.photos.append(photo_url)
            db.commit()
            db.refresh(issue)

        return issue
