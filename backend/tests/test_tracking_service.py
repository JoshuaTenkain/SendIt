"""Tests for tracking service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.services.tracking_service import TrackingService
from app.services.issue_service import IssueService


@pytest.fixture
def booking_id():
    """Create a test booking ID."""
    return uuid4()


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def mock_registry():
    """Create a mock courier registry."""
    return Mock()


@pytest.mark.asyncio
async def test_refresh_tracking_no_booking(mock_db, mock_registry, booking_id):
    """Test refresh tracking with non-existent booking."""
    mock_db.get.return_value = None

    result = await TrackingService.refresh_tracking(
        db=mock_db,
        booking_id=booking_id,
        registry=mock_registry,
    )

    assert result == []


@pytest.mark.asyncio
async def test_refresh_tracking_no_tracking_reference(mock_db, mock_registry, booking_id):
    """Test refresh tracking with no tracking reference."""
    booking = Mock()
    booking.tracking_reference = None
    mock_db.get.return_value = booking

    result = await TrackingService.refresh_tracking(
        db=mock_db,
        booking_id=booking_id,
        registry=mock_registry,
    )

    assert result == []


def test_get_tracking_summary_no_booking(mock_db, booking_id):
    """Test getting tracking summary for non-existent booking."""
    mock_db.get.return_value = None

    result = TrackingService.get_tracking_summary(db=mock_db, booking_id=booking_id)

    assert result == {}


def test_get_tracking_summary_with_events(mock_db, booking_id):
    """Test getting tracking summary with events."""
    booking = Mock()
    booking.id = booking_id
    booking.tracking_reference = "TCG-123456"

    event1 = Mock()
    event1.status = "created"
    event1.description = "Shipment created"
    event1.location = "Johannesburg"
    event1.latitude = -26.2023
    event1.longitude = 28.0436
    event1.occurred_at = datetime.now(timezone.utc)

    event2 = Mock()
    event2.status = "in_transit"
    event2.description = "In transit"
    event2.location = "Bloemfontein"
    event2.latitude = -29.1167
    event2.longitude = 25.5167
    event2.occurred_at = datetime.now(timezone.utc)

    mock_db.get.return_value = booking
    mock_db.scalars.return_value = [event1, event2]

    result = TrackingService.get_tracking_summary(db=mock_db, booking_id=booking_id)

    assert result["booking_id"] == str(booking_id)
    assert result["tracking_reference"] == "TCG-123456"
    assert result["current_status"] == "in_transit"
    assert len(result["events"]) == 2


def test_issue_service_create_issue(mock_db, booking_id):
    """Test creating a delivery issue."""
    with patch.object(IssueService, 'create_issue') as mock_create:
        mock_issue = Mock()
        mock_issue.id = uuid4()
        mock_issue.booking_id = booking_id
        mock_issue.issue_type = "delivery_failed"
        mock_issue.description = "Recipient not available"
        mock_issue.status = "open"

        mock_create.return_value = mock_issue

        issue = IssueService.create_issue(
            db=mock_db,
            booking_id=booking_id,
            issue_type="delivery_failed",
            description="Recipient not available",
        )

        assert issue.issue_type == "delivery_failed"
        assert issue.status == "open"


def test_issue_service_invalid_issue_type(mock_db, booking_id):
    """Test creating issue with invalid type."""
    with pytest.raises(ValueError):
        IssueService.create_issue(
            db=mock_db,
            booking_id=booking_id,
            issue_type="invalid_type",
            description="Test",
        )


def test_issue_service_list_issues(mock_db, booking_id):
    """Test listing issues for a booking."""
    issue1 = Mock()
    issue1.issue_type = "delivery_failed"
    issue1.status = "open"

    issue2 = Mock()
    issue2.issue_type = "package_damaged"
    issue2.status = "resolved"

    with patch.object(IssueService, 'list_issues') as mock_list:
        mock_list.return_value = [issue1, issue2]

        issues = IssueService.list_issues(db=mock_db, booking_id=booking_id)

        assert len(issues) == 2
        assert issues[0].issue_type == "delivery_failed"
        assert issues[1].issue_type == "package_damaged"


def test_issue_service_resolve_issue(mock_db):
    """Test resolving a delivery issue."""
    issue_id = uuid4()

    with patch.object(IssueService, 'resolve_issue') as mock_resolve:
        mock_issue = Mock()
        mock_issue.id = issue_id
        mock_issue.status = "resolved"
        mock_issue.resolution_type = "refund"
        mock_issue.resolution_amount = 10000

        mock_resolve.return_value = mock_issue

        resolved = IssueService.resolve_issue(
            db=mock_db,
            issue_id=issue_id,
            resolution_type="refund",
            resolution_amount=10000,
        )

        assert resolved.status == "resolved"
        assert resolved.resolution_type == "refund"
        assert resolved.resolution_amount == 10000


def test_issue_service_invalid_resolution_type(mock_db):
    """Test resolving with invalid resolution type."""
    issue_id = uuid4()

    with pytest.raises(ValueError):
        IssueService.resolve_issue(
            db=mock_db,
            issue_id=issue_id,
            resolution_type="invalid_type",
        )


def test_issue_service_reject_issue(mock_db):
    """Test rejecting a delivery issue."""
    issue_id = uuid4()

    with patch.object(IssueService, 'reject_issue') as mock_reject:
        mock_issue = Mock()
        mock_issue.id = issue_id
        mock_issue.status = "rejected"
        mock_issue.resolution_notes = "Rejected: No evidence provided"

        mock_reject.return_value = mock_issue

        rejected = IssueService.reject_issue(
            db=mock_db,
            issue_id=issue_id,
            rejection_reason="No evidence provided",
        )

        assert rejected.status == "rejected"
        assert "Rejected" in rejected.resolution_notes
