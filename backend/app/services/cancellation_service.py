"""Booking cancellation and refund service."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.transaction import Transaction

logger = structlog.get_logger()


class CancellationService:
    """Handle booking cancellations and refunds."""

    CANCELLATION_FEE_PCT = 15  # 15% fee after payment

    @staticmethod
    def can_cancel(booking: Booking) -> tuple[bool, str | None]:
        """Check if a booking can be cancelled.

        Returns:
            (can_cancel, reason_if_not)
        """
        if booking.status == "cancelled":
            return False, "Booking is already cancelled"
        if booking.status == "shipment_created":
            return False, "Cannot cancel after shipment created"
        if booking.status == "in_transit":
            return False, "Cannot cancel while shipment in transit"
        if booking.status == "delivered":
            return False, "Cannot cancel delivered shipment"
        return True, None

    @staticmethod
    def calculate_refund(booking: Booking) -> tuple[Decimal, str]:
        """Calculate refund amount based on booking status.

        Returns:
            (refund_amount, reason)
        """
        total = Decimal(booking.price_total)

        if booking.status == "pending_payment":
            return total, "Full refund (no payment processed)"

        if booking.status == "paid":
            fee = total * Decimal(CancellationService.CANCELLATION_FEE_PCT) / Decimal(100)
            refund = total - fee
            return refund, f"Refund after {CancellationService.CANCELLATION_FEE_PCT}% cancellation fee"

        return Decimal(0), "No refund eligible"

    @staticmethod
    async def cancel_booking(
        *,
        db: Session,
        booking_id: UUID,
        reason: str,
        refund_reason: str | None = None,
    ) -> tuple[bool, str]:
        """Cancel a booking and process refund if applicable.

        Returns:
            (success, message)
        """
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return False, "Booking not found"

        can_cancel, error = CancellationService.can_cancel(booking)
        if not can_cancel:
            return False, error or "Cannot cancel this booking"

        refund_amount, refund_msg = CancellationService.calculate_refund(booking)

        booking.status = "cancelled"
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancel_reason = reason

        if refund_amount > 0 and booking.status == "paid":
            transaction = db.query(Transaction).filter(Transaction.booking_id == booking_id).first()
            if transaction:
                transaction.refund_amount = refund_amount
                transaction.refund_status = "pending"
                transaction.refund_reason = refund_reason or reason
                logger.info(
                    "refund_initiated",
                    booking_id=booking_id,
                    amount=refund_amount,
                    reason=refund_reason,
                )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        logger.info(
            "booking_cancelled",
            booking_id=booking_id,
            reason=reason,
            refund_amount=refund_amount,
        )

        return True, f"Booking cancelled. {refund_msg}"
