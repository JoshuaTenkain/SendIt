"""Tests for email notification service."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.email_service import EmailService, get_email_service


@pytest.fixture
def email_service():
    """Create email service instance for testing."""
    return EmailService(api_key="test-key")


def test_email_service_is_configured(email_service):
    """Test that email service can be configured."""
    assert email_service.api_key == "test-key"
    assert email_service.from_email == "no-reply@send-it.local"


def test_email_service_not_configured_without_key():
    """Test that email service is not configured without API key."""
    service = EmailService(api_key=None)
    assert not service.is_configured()


@pytest.mark.asyncio
async def test_send_welcome_email(email_service):
    """Test sending welcome email."""
    with patch.object(email_service, 'client') as mock_client:
        email_service.client = mock_client
        result = await email_service.send_welcome_email(
            to_email="user@example.com",
            user_name="John Doe"
        )
        assert result is True


@pytest.mark.asyncio
async def test_send_booking_confirmation(email_service):
    """Test sending booking confirmation email."""
    with patch.object(email_service, 'client') as mock_client:
        email_service.client = mock_client
        result = await email_service.send_booking_confirmation(
            to_email="user@example.com",
            booking_id="123",
            courier_name="The Courier Guy",
            price_total=10000,
            tracking_link="https://send-it.local/track/123"
        )
        assert result is True


@pytest.mark.asyncio
async def test_send_payment_receipt(email_service):
    """Test sending payment receipt email."""
    with patch.object(email_service, 'client') as mock_client:
        email_service.client = mock_client
        result = await email_service.send_payment_receipt(
            to_email="user@example.com",
            booking_id="123",
            amount=10000,
            transaction_id="txn-123"
        )
        assert result is True


@pytest.mark.asyncio
async def test_send_shipment_created(email_service):
    """Test sending shipment created notification."""
    with patch.object(email_service, 'client') as mock_client:
        email_service.client = mock_client
        result = await email_service.send_shipment_created(
            to_email="user@example.com",
            booking_id="123",
            tracking_reference="TCG-123456",
            courier_name="The Courier Guy",
            tracking_link="https://send-it.local/track/123"
        )
        assert result is True


@pytest.mark.asyncio
async def test_send_tracking_update(email_service):
    """Test sending tracking update notification."""
    with patch.object(email_service, 'client') as mock_client:
        email_service.client = mock_client
        result = await email_service.send_tracking_update(
            to_email="user@example.com",
            booking_id="123",
            tracking_reference="TCG-123456",
            status="in_transit",
            description="Package in transit",
            tracking_link="https://send-it.local/track/123"
        )
        assert result is True


@pytest.mark.asyncio
async def test_send_delivery_confirmation(email_service):
    """Test sending delivery confirmation email."""
    with patch.object(email_service, 'client') as mock_client:
        email_service.client = mock_client
        result = await email_service.send_delivery_confirmation(
            to_email="user@example.com",
            booking_id="123",
            tracking_reference="TCG-123456"
        )
        assert result is True


@pytest.mark.asyncio
async def test_send_issue_notification(email_service):
    """Test sending issue notification email."""
    with patch.object(email_service, 'client') as mock_client:
        email_service.client = mock_client
        result = await email_service.send_issue_notification(
            to_email="user@example.com",
            booking_id="123",
            issue_type="delivery_failed",
            description="Recipient not available"
        )
        assert result is True


def test_get_email_service_singleton():
    """Test that get_email_service returns singleton instance."""
    service1 = get_email_service()
    service2 = get_email_service()
    assert service1 is service2
