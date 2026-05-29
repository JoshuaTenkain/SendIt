"""SMS notification service using Twilio."""

from __future__ import annotations

import structlog
from twilio.rest import Client

from app.config import settings

logger = structlog.get_logger()


class SMSService:
    """Send SMS notifications via Twilio."""

    def __init__(self, account_sid: str | None = None, auth_token: str | None = None, from_number: str | None = None):
        self.account_sid = account_sid or settings.twilio_account_sid
        self.auth_token = auth_token or settings.twilio_auth_token
        self.from_number = from_number or settings.twilio_from_number
        self.client = Client(self.account_sid, self.auth_token) if self.account_sid and self.auth_token else None

    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return self.client is not None

    async def send_payment_confirmed(self, *, to_phone: str, booking_id: str, amount: str) -> bool:
        """Send payment confirmed SMS."""
        if not self.is_configured():
            logger.warning("twilio_not_configured")
            return False

        message = f"Send-it: Payment confirmed for booking {booking_id}. Amount: {amount}. Your shipment will be created shortly."
        return await self._send(to_phone=to_phone, message=message)

    async def send_out_for_delivery(
        self, *, to_phone: str, tracking_reference: str, driver_contact: str | None = None
    ) -> bool:
        """Send out for delivery SMS."""
        if not self.is_configured():
            logger.warning("twilio_not_configured")
            return False

        driver_info = f" Driver: {driver_contact}" if driver_contact else ""
        message = f"Send-it: Your package {tracking_reference} is out for delivery today.{driver_info}"
        return await self._send(to_phone=to_phone, message=message)

    async def send_delivered(self, *, to_phone: str, tracking_reference: str, tracking_link: str) -> bool:
        """Send delivery confirmation SMS."""
        if not self.is_configured():
            logger.warning("twilio_not_configured")
            return False

        message = f"Send-it: Your package {tracking_reference} has been delivered! Track: {tracking_link}"
        return await self._send(to_phone=to_phone, message=message)

    async def send_delivery_failed(self, *, to_phone: str, tracking_reference: str, reason: str) -> bool:
        """Send delivery failed SMS."""
        if not self.is_configured():
            logger.warning("twilio_not_configured")
            return False

        message = f"Send-it: Delivery failed for {tracking_reference}. Reason: {reason}. Contact support for assistance."
        return await self._send(to_phone=to_phone, message=message)

    async def send_issue_alert(self, *, to_phone: str, booking_id: str, issue_type: str) -> bool:
        """Send issue alert SMS."""
        if not self.is_configured():
            logger.warning("twilio_not_configured")
            return False

        message = f"Send-it: Issue reported for booking {booking_id} ({issue_type}). Our team will contact you shortly."
        return await self._send(to_phone=to_phone, message=message)

    async def send_quote_expiry_reminder(self, *, to_phone: str, quote_id: str) -> bool:
        """Send quote expiry reminder SMS."""
        if not self.is_configured():
            logger.warning("twilio_not_configured")
            return False

        message = f"Send-it: Your quote {quote_id} expires in 1 hour. Book now to lock in the price!"
        return await self._send(to_phone=to_phone, message=message)

    async def _send(self, *, to_phone: str, message: str) -> bool:
        """Send SMS via Twilio."""
        if not self.is_configured():
            return False

        try:
            self.client.messages.create(body=message, from_=self.from_number, to=to_phone)
            logger.info("sms_sent", to_phone=to_phone, message_length=len(message))
            return True
        except Exception as e:
            logger.error("sms_send_failed", to_phone=to_phone, error=str(e))
            return False


# Singleton instance
_sms_service: SMSService | None = None


def get_sms_service() -> SMSService:
    """Get or create SMS service instance."""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service
