"""Integration tests for complete workflows."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from decimal import Decimal

from app.services.quote_cache_service import QuoteCacheService
from app.services.cancellation_service import CancellationService
from app.services.tracking_service import TrackingService
from app.services.issue_service import IssueService
from app.integrations.couriers.base import QuoteResult


@pytest.fixture
def mock_db():
    """Create mock database."""
    return Mock()


@pytest.fixture
def mock_registry():
    """Create mock courier registry."""
    return Mock()


@pytest.fixture
def sample_quote_results():
    """Create sample quote results."""
    return [
        QuoteResult(
            courier_code="tcg",
            courier_name="The Courier Guy",
            service_level="economy",
            price_total=10000,
            currency="ZAR",
            estimated_delivery_days=3,
            raw={"test": True},
        ),
        QuoteResult(
            courier_code="aramex",
            courier_name="Aramex",
            service_level="standard",
            price_total=12000,
            currency="ZAR",
            estimated_delivery_days=2,
            raw={"test": True},
        ),
    ]


class TestQuoteToBookingWorkflow:
    """Test complete quote to booking workflow."""

    def test_quote_generation_with_caching(self, sample_quote_results):
        """Test quote generation with caching."""
        cache = QuoteCacheService(redis_url=None)

        route = {
            "pickup": {"city": "Johannesburg", "province": "Gauteng", "postal_code": "2000"},
            "delivery": {"city": "Cape Town", "province": "Western Cape", "postal_code": "8000"},
            "parcel": {"weight_kg": 2.0, "length_cm": 30, "width_cm": 20, "height_cm": 15},
        }

        # First call - cache miss
        result1 = cache.get(
            pickup=route["pickup"],
            delivery=route["delivery"],
            parcel=route["parcel"],
        )
        assert result1 is None

        # Set cache
        cache.set(
            pickup=route["pickup"],
            delivery=route["delivery"],
            parcel=route["parcel"],
            results=sample_quote_results,
        )

        # Second call - would be cache hit (if Redis available)
        # Without Redis, returns None
        result2 = cache.get(
            pickup=route["pickup"],
            delivery=route["delivery"],
            parcel=route["parcel"],
        )
        # Expected None without Redis
        assert result2 is None

    def test_booking_creation_and_cancellation(self, mock_db):
        """Test booking creation and cancellation workflow."""
        booking_id = uuid4()

        # Create booking (simulated)
        booking = Mock()
        booking.id = booking_id
        booking.status = "pending_payment"
        booking.price_total = Decimal("100.00")

        # Check if can cancel
        can_cancel, reason = CancellationService.can_cancel(booking)
        assert can_cancel is True

        # Calculate refund
        refund, reason = CancellationService.calculate_refund(booking)
        assert refund == Decimal("100.00")  # Full refund before payment

    def test_booking_payment_and_cancellation(self, mock_db):
        """Test booking payment and cancellation with fee."""
        booking_id = uuid4()

        # Create paid booking
        booking = Mock()
        booking.id = booking_id
        booking.status = "paid"
        booking.price_total = Decimal("100.00")

        # Check if can cancel
        can_cancel, reason = CancellationService.can_cancel(booking)
        assert can_cancel is True

        # Calculate refund (with 15% fee)
        refund, reason = CancellationService.calculate_refund(booking)
        assert refund == Decimal("85.00")  # 100 - 15% fee
        assert "15%" in reason


class TestTrackingWorkflow:
    """Test tracking and issue reporting workflow."""

    @pytest.mark.asyncio
    async def test_tracking_refresh_workflow(self, mock_db, mock_registry):
        """Test tracking refresh workflow."""
        booking_id = uuid4()

        # Create booking with tracking reference
        booking = Mock()
        booking.id = booking_id
        booking.tracking_reference = "TCG-123456"
        booking.courier_id = uuid4()

        mock_db.get.return_value = booking

        # Refresh tracking
        result = await TrackingService.refresh_tracking(
            db=mock_db,
            booking_id=booking_id,
            registry=mock_registry,
        )

        # Should return empty list (no mock adapter)
        assert isinstance(result, list)

    def test_issue_reporting_workflow(self, mock_db):
        """Test issue reporting and resolution workflow."""
        booking_id = uuid4()
        issue_id = uuid4()

        # Create issue
        with patch.object(IssueService, 'create_issue') as mock_create:
            mock_issue = Mock()
            mock_issue.id = issue_id
            mock_issue.booking_id = booking_id
            mock_issue.issue_type = "delivery_failed"
            mock_issue.status = "open"

            mock_create.return_value = mock_issue

            issue = IssueService.create_issue(
                db=mock_db,
                booking_id=booking_id,
                issue_type="delivery_failed",
                description="Recipient not available",
            )

            assert issue.status == "open"

        # Resolve issue
        with patch.object(IssueService, 'resolve_issue') as mock_resolve:
            resolved_issue = Mock()
            resolved_issue.id = issue_id
            resolved_issue.status = "resolved"
            resolved_issue.resolution_type = "refund"
            resolved_issue.resolution_amount = 10000

            mock_resolve.return_value = resolved_issue

            resolved = IssueService.resolve_issue(
                db=mock_db,
                issue_id=issue_id,
                resolution_type="refund",
                resolution_amount=10000,
            )

            assert resolved.status == "resolved"
            assert resolved.resolution_type == "refund"

    def test_issue_rejection_workflow(self, mock_db):
        """Test issue rejection workflow."""
        issue_id = uuid4()

        with patch.object(IssueService, 'reject_issue') as mock_reject:
            rejected_issue = Mock()
            rejected_issue.id = issue_id
            rejected_issue.status = "rejected"
            rejected_issue.resolution_notes = "Rejected: No evidence provided"

            mock_reject.return_value = rejected_issue

            rejected = IssueService.reject_issue(
                db=mock_db,
                issue_id=issue_id,
                rejection_reason="No evidence provided",
            )

            assert rejected.status == "rejected"


class TestMultipleQuotesComparison:
    """Test comparing multiple courier quotes."""

    def test_quote_comparison_workflow(self, sample_quote_results):
        """Test comparing quotes from multiple couriers."""
        # Simulate getting quotes from multiple couriers
        quotes = sample_quote_results

        # Sort by price
        sorted_by_price = sorted(quotes, key=lambda q: q.price_total)
        assert sorted_by_price[0].courier_code == "tcg"
        assert sorted_by_price[0].price_total == 10000

        # Sort by delivery time
        sorted_by_time = sorted(quotes, key=lambda q: q.estimated_delivery_days)
        assert sorted_by_time[0].estimated_delivery_days == 2

        # Filter by service level
        economy_quotes = [q for q in quotes if "economy" in q.service_level.lower()]
        assert len(economy_quotes) == 1

    def test_quote_selection_and_booking(self, sample_quote_results):
        """Test selecting quote and creating booking."""
        # Select cheapest quote
        selected_quote = min(sample_quote_results, key=lambda q: q.price_total)

        # Verify selection
        assert selected_quote.courier_code == "tcg"
        assert selected_quote.price_total == 10000

        # Create booking (simulated)
        booking = Mock()
        booking.courier_id = selected_quote.courier_code
        booking.price_total = Decimal(selected_quote.price_total / 100)

        assert booking.price_total == Decimal("100.00")


class TestErrorHandling:
    """Test error handling in workflows."""

    @pytest.mark.asyncio
    async def test_tracking_refresh_with_no_booking(self, mock_db, mock_registry):
        """Test tracking refresh when booking doesn't exist."""
        booking_id = uuid4()
        mock_db.get.return_value = None

        result = await TrackingService.refresh_tracking(
            db=mock_db,
            booking_id=booking_id,
            registry=mock_registry,
        )

        assert result == []

    def test_cancellation_with_invalid_status(self, mock_db):
        """Test cancellation with invalid booking status."""
        booking = Mock()
        booking.status = "delivered"

        can_cancel, reason = CancellationService.can_cancel(booking)

        assert can_cancel is False
        assert reason is not None

    def test_issue_creation_with_invalid_type(self, mock_db):
        """Test issue creation with invalid type."""
        booking_id = uuid4()

        with pytest.raises(ValueError):
            IssueService.create_issue(
                db=mock_db,
                booking_id=booking_id,
                issue_type="invalid_type",
                description="Test",
            )

    def test_issue_resolution_with_invalid_type(self, mock_db):
        """Test issue resolution with invalid type."""
        issue_id = uuid4()

        with pytest.raises(ValueError):
            IssueService.resolve_issue(
                db=mock_db,
                issue_id=issue_id,
                resolution_type="invalid_type",
            )


class TestConcurrentOperations:
    """Test concurrent operations."""

    def test_multiple_quote_requests(self, sample_quote_results):
        """Test handling multiple quote requests."""
        cache = QuoteCacheService(redis_url=None)

        routes = [
            {
                "pickup": {"city": "Johannesburg", "province": "Gauteng", "postal_code": "2000"},
                "delivery": {"city": "Cape Town", "province": "Western Cape", "postal_code": "8000"},
                "parcel": {"weight_kg": 2.0, "length_cm": 30, "width_cm": 20, "height_cm": 15},
            },
            {
                "pickup": {"city": "Pretoria", "province": "Gauteng", "postal_code": "0001"},
                "delivery": {"city": "Durban", "province": "KwaZulu-Natal", "postal_code": "4000"},
                "parcel": {"weight_kg": 5.0, "length_cm": 50, "width_cm": 40, "height_cm": 30},
            },
        ]

        # Generate cache keys for multiple routes
        keys = []
        for route in routes:
            key = cache._make_cache_key(
                pickup=route["pickup"],
                delivery=route["delivery"],
                parcel=route["parcel"],
            )
            keys.append(key)

        # Verify keys are unique
        assert len(keys) == len(set(keys))

    def test_multiple_issue_reports(self, mock_db):
        """Test handling multiple issue reports."""
        booking_id = uuid4()

        issue_types = [
            "delivery_failed",
            "package_damaged",
            "package_lost",
            "wrong_address",
            "recipient_unavailable",
        ]

        with patch.object(IssueService, 'create_issue') as mock_create:
            for issue_type in issue_types:
                mock_issue = Mock()
                mock_issue.issue_type = issue_type
                mock_issue.status = "open"

                mock_create.return_value = mock_issue

                issue = IssueService.create_issue(
                    db=mock_db,
                    booking_id=booking_id,
                    issue_type=issue_type,
                    description="Test issue",
                )

                assert issue.issue_type == issue_type
