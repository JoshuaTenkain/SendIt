"""Tests for booking cancellation service."""

import pytest
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

from app.services.cancellation_service import CancellationService


@pytest.fixture
def booking_id():
    """Create a test booking ID."""
    return uuid4()


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock()


def test_can_cancel_pending_payment():
    """Test that pending payment bookings can be cancelled."""
    booking = Mock()
    booking.status = "pending_payment"

    can_cancel, reason = CancellationService.can_cancel(booking)

    assert can_cancel is True
    assert reason is None


def test_can_cancel_paid():
    """Test that paid bookings can be cancelled."""
    booking = Mock()
    booking.status = "paid"

    can_cancel, reason = CancellationService.can_cancel(booking)

    assert can_cancel is True
    assert reason is None


def test_cannot_cancel_already_cancelled():
    """Test that cancelled bookings cannot be cancelled again."""
    booking = Mock()
    booking.status = "cancelled"

    can_cancel, reason = CancellationService.can_cancel(booking)

    assert can_cancel is False
    assert "already cancelled" in reason


def test_cannot_cancel_shipment_created():
    """Test that bookings with shipment created cannot be cancelled."""
    booking = Mock()
    booking.status = "shipment_created"

    can_cancel, reason = CancellationService.can_cancel(booking)

    assert can_cancel is False
    assert "shipment created" in reason


def test_cannot_cancel_in_transit():
    """Test that in-transit bookings cannot be cancelled."""
    booking = Mock()
    booking.status = "in_transit"

    can_cancel, reason = CancellationService.can_cancel(booking)

    assert can_cancel is False
    assert "in transit" in reason


def test_cannot_cancel_delivered():
    """Test that delivered bookings cannot be cancelled."""
    booking = Mock()
    booking.status = "delivered"

    can_cancel, reason = CancellationService.can_cancel(booking)

    assert can_cancel is False
    assert "delivered" in reason


def test_calculate_refund_pending_payment():
    """Test refund calculation for pending payment."""
    booking = Mock()
    booking.status = "pending_payment"
    booking.price_total = Decimal("100.00")

    refund, reason = CancellationService.calculate_refund(booking)

    assert refund == Decimal("100.00")
    assert "Full refund" in reason


def test_calculate_refund_paid():
    """Test refund calculation for paid booking."""
    booking = Mock()
    booking.status = "paid"
    booking.price_total = Decimal("100.00")

    refund, reason = CancellationService.calculate_refund(booking)

    # 100 - (100 * 15%) = 85
    assert refund == Decimal("85.00")
    assert "15%" in reason


def test_calculate_refund_shipment_created():
    """Test refund calculation for shipment created."""
    booking = Mock()
    booking.status = "shipment_created"
    booking.price_total = Decimal("100.00")

    refund, reason = CancellationService.calculate_refund(booking)

    assert refund == Decimal("0")
    assert "No refund" in reason


@pytest.mark.asyncio
async def test_cancel_booking_not_found(mock_db, booking_id):
    """Test cancelling non-existent booking."""
    mock_db.query.return_value.filter.return_value.first.return_value = None

    success, message = await CancellationService.cancel_booking(
        db=mock_db,
        booking_id=booking_id,
        reason="User requested",
    )

    assert success is False
    assert "not found" in message


@pytest.mark.asyncio
async def test_cancel_booking_already_cancelled(mock_db, booking_id):
    """Test cancelling already cancelled booking."""
    booking = Mock()
    booking.status = "cancelled"
    booking.id = booking_id

    mock_db.query.return_value.filter.return_value.first.return_value = booking

    success, message = await CancellationService.cancel_booking(
        db=mock_db,
        booking_id=booking_id,
        reason="User requested",
    )

    assert success is False
    assert "already cancelled" in message


@pytest.mark.asyncio
async def test_cancel_booking_pending_payment(mock_db, booking_id):
    """Test cancelling pending payment booking."""
    booking = Mock()
    booking.status = "pending_payment"
    booking.id = booking_id
    booking.price_total = Decimal("100.00")

    mock_db.query.return_value.filter.return_value.first.return_value = booking
    mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

    success, message = await CancellationService.cancel_booking(
        db=mock_db,
        booking_id=booking_id,
        reason="User requested",
    )

    assert success is True
    assert booking.status == "cancelled"
    assert booking.cancel_reason == "User requested"


@pytest.mark.asyncio
async def test_cancel_booking_with_refund(mock_db, booking_id):
    """Test cancelling paid booking with refund."""
    booking = Mock()
    booking.status = "paid"
    booking.id = booking_id
    booking.price_total = Decimal("100.00")

    transaction = Mock()
    transaction.booking_id = booking_id

    mock_db.query.return_value.filter.return_value.first.side_effect = [booking, transaction]

    success, message = await CancellationService.cancel_booking(
        db=mock_db,
        booking_id=booking_id,
        reason="User requested",
        refund_reason="Customer request",
    )

    assert success is True
    assert booking.status == "cancelled"
    assert transaction.refund_amount == Decimal("85.00")
    assert transaction.refund_status == "pending"
