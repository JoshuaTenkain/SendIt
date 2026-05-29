"""Email notification service using SendGrid."""

from __future__ import annotations

import structlog
from jinja2 import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To

from app.config import settings

logger = structlog.get_logger()


class EmailService:
    """Send transactional emails via SendGrid."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.sendgrid_api_key
        self.from_email = settings.sendgrid_from_email
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None

    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured."""
        return self.client is not None and self.api_key is not None

    async def send_welcome_email(self, *, to_email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        if not self.is_configured():
            logger.warning("sendgrid_not_configured")
            return False

        subject = "Welcome to Send-it!"
        html_content = f"""
        <h1>Welcome to Send-it, {user_name}!</h1>
        <p>We're excited to have you on board.</p>
        <p>Start comparing courier rates and save on shipping costs today.</p>
        <a href="{settings.frontend_base_url}/dashboard">Go to Dashboard</a>
        """

        return await self._send(to_email=to_email, subject=subject, html_content=html_content)

    async def send_booking_confirmation(
        self,
        *,
        to_email: str,
        booking_id: str,
        courier_name: str,
        price_total: int,
        tracking_link: str,
    ) -> bool:
        """Send booking confirmation email."""
        if not self.is_configured():
            logger.warning("sendgrid_not_configured")
            return False

        price_display = f"R {price_total / 100:.2f}"
        subject = f"Booking Confirmed - {courier_name}"
        html_content = f"""
        <h1>Your Booking is Confirmed!</h1>
        <p>Booking ID: <strong>{booking_id}</strong></p>
        <p>Courier: <strong>{courier_name}</strong></p>
        <p>Total Price: <strong>{price_display}</strong></p>
        <p>Next step: Complete payment to activate your shipment.</p>
        <a href="{tracking_link}">View Booking Details</a>
        """

        return await self._send(to_email=to_email, subject=subject, html_content=html_content)

    async def send_payment_receipt(
        self,
        *,
        to_email: str,
        booking_id: str,
        amount: int,
        transaction_id: str,
    ) -> bool:
        """Send payment receipt email."""
        if not self.is_configured():
            logger.warning("sendgrid_not_configured")
            return False

        amount_display = f"R {amount / 100:.2f}"
        subject = f"Payment Receipt - Booking {booking_id}"
        html_content = f"""
        <h1>Payment Received</h1>
        <p>Thank you for your payment!</p>
        <p>Booking ID: <strong>{booking_id}</strong></p>
        <p>Amount: <strong>{amount_display}</strong></p>
        <p>Transaction ID: <strong>{transaction_id}</strong></p>
        <p>Your shipment will be created shortly.</p>
        """

        return await self._send(to_email=to_email, subject=subject, html_content=html_content)

    async def send_shipment_created(
        self,
        *,
        to_email: str,
        booking_id: str,
        tracking_reference: str,
        courier_name: str,
        tracking_link: str,
    ) -> bool:
        """Send shipment created notification."""
        if not self.is_configured():
            logger.warning("sendgrid_not_configured")
            return False

        subject = f"Shipment Created - Tracking {tracking_reference}"
        html_content = f"""
        <h1>Your Shipment is Ready!</h1>
        <p>Booking ID: <strong>{booking_id}</strong></p>
        <p>Courier: <strong>{courier_name}</strong></p>
        <p>Tracking Reference: <strong>{tracking_reference}</strong></p>
        <p>Track your shipment in real-time:</p>
        <a href="{tracking_link}">Track Shipment</a>
        """

        return await self._send(to_email=to_email, subject=subject, html_content=html_content)

    async def send_tracking_update(
        self,
        *,
        to_email: str,
        booking_id: str,
        tracking_reference: str,
        status: str,
        description: str,
        tracking_link: str,
    ) -> bool:
        """Send tracking update notification."""
        if not self.is_configured():
            logger.warning("sendgrid_not_configured")
            return False

        subject = f"Shipment Update - {status.title()}"
        html_content = f"""
        <h1>Shipment Update</h1>
        <p>Tracking Reference: <strong>{tracking_reference}</strong></p>
        <p>Status: <strong>{status.title()}</strong></p>
        <p>Details: {description}</p>
        <a href="{tracking_link}">View Full Tracking</a>
        """

        return await self._send(to_email=to_email, subject=subject, html_content=html_content)

    async def send_delivery_confirmation(
        self,
        *,
        to_email: str,
        booking_id: str,
        tracking_reference: str,
    ) -> bool:
        """Send delivery confirmation email."""
        if not self.is_configured():
            logger.warning("sendgrid_not_configured")
            return False

        subject = f"Delivery Confirmed - {tracking_reference}"
        html_content = f"""
        <h1>Your Package Has Been Delivered!</h1>
        <p>Booking ID: <strong>{booking_id}</strong></p>
        <p>Tracking Reference: <strong>{tracking_reference}</strong></p>
        <p>Thank you for using Send-it!</p>
        """

        return await self._send(to_email=to_email, subject=subject, html_content=html_content)

    async def send_issue_notification(
        self,
        *,
        to_email: str,
        booking_id: str,
        issue_type: str,
        description: str,
    ) -> bool:
        """Send issue notification email."""
        if not self.is_configured():
            logger.warning("sendgrid_not_configured")
            return False

        subject = f"Delivery Issue - {issue_type.title()}"
        html_content = f"""
        <h1>Delivery Issue Reported</h1>
        <p>Booking ID: <strong>{booking_id}</strong></p>
        <p>Issue Type: <strong>{issue_type.title()}</strong></p>
        <p>Description: {description}</p>
        <p>Our support team will contact you shortly.</p>
        """

        return await self._send(to_email=to_email, subject=subject, html_content=html_content)

    async def _send(self, *, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SendGrid."""
        if not self.is_configured():
            return False

        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=To(to_email),
                subject=subject,
                html_content=html_content,
            )
            self.client.send(message)
            logger.info("email_sent", to_email=to_email, subject=subject)
            return True
        except Exception as e:
            logger.error("email_send_failed", to_email=to_email, error=str(e))
            return False


# Singleton instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
