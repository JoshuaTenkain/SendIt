"""Tests for quote caching service."""

import pytest
from unittest.mock import Mock, patch

from app.services.quote_cache_service import QuoteCacheService, get_quote_cache_service
from app.integrations.couriers.base import QuoteResult


@pytest.fixture
def cache_service():
    """Create cache service instance for testing."""
    return QuoteCacheService(redis_url=None)


@pytest.fixture
def sample_quotes():
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
            courier_code="tcg",
            courier_name="The Courier Guy",
            service_level="express",
            price_total=15000,
            currency="ZAR",
            estimated_delivery_days=1,
            raw={"test": True},
        ),
    ]


@pytest.fixture
def sample_route():
    """Create sample route parameters."""
    return {
        "pickup": {
            "city": "Johannesburg",
            "province": "Gauteng",
            "postal_code": "2000",
        },
        "delivery": {
            "city": "Cape Town",
            "province": "Western Cape",
            "postal_code": "8000",
        },
        "parcel": {
            "weight_kg": 2.0,
            "length_cm": 30,
            "width_cm": 20,
            "height_cm": 15,
        },
    }


def test_cache_service_not_available_without_redis(cache_service):
    """Test that cache service is not available without Redis."""
    assert not cache_service.is_available()


def test_cache_key_generation(cache_service, sample_route):
    """Test cache key generation."""
    key = cache_service._make_cache_key(
        pickup=sample_route["pickup"],
        delivery=sample_route["delivery"],
        parcel=sample_route["parcel"],
    )
    assert key.startswith("quote:")
    assert len(key) > 10


def test_cache_key_consistency(cache_service, sample_route):
    """Test that same route generates same cache key."""
    key1 = cache_service._make_cache_key(
        pickup=sample_route["pickup"],
        delivery=sample_route["delivery"],
        parcel=sample_route["parcel"],
    )
    key2 = cache_service._make_cache_key(
        pickup=sample_route["pickup"],
        delivery=sample_route["delivery"],
        parcel=sample_route["parcel"],
    )
    assert key1 == key2


def test_cache_get_returns_none_without_redis(cache_service, sample_route):
    """Test that cache get returns None without Redis."""
    result = cache_service.get(
        pickup=sample_route["pickup"],
        delivery=sample_route["delivery"],
        parcel=sample_route["parcel"],
    )
    assert result is None


def test_cache_set_returns_false_without_redis(cache_service, sample_route, sample_quotes):
    """Test that cache set returns False without Redis."""
    result = cache_service.set(
        pickup=sample_route["pickup"],
        delivery=sample_route["delivery"],
        parcel=sample_route["parcel"],
        results=sample_quotes,
    )
    assert result is False


def test_cache_invalidate_all_returns_false_without_redis(cache_service):
    """Test that cache invalidate returns False without Redis."""
    result = cache_service.invalidate_all()
    assert result is False


def test_cache_stats_without_redis(cache_service):
    """Test cache stats without Redis."""
    stats = cache_service.get_stats()
    assert stats["available"] is False


def test_get_cache_service_singleton():
    """Test that get_quote_cache_service returns singleton instance."""
    service1 = get_quote_cache_service()
    service2 = get_quote_cache_service()
    assert service1 is service2


@pytest.mark.asyncio
async def test_cache_with_mock_redis(sample_route, sample_quotes):
    """Test caching with mocked Redis."""
    with patch("app.services.quote_cache_service.redis") as mock_redis:
        mock_client = Mock()
        mock_redis.from_url.return_value = mock_client
        mock_client.ping.return_value = True

        service = QuoteCacheService(redis_url="redis://localhost:6379/0")

        # Test set
        result = service.set(
            pickup=sample_route["pickup"],
            delivery=sample_route["delivery"],
            parcel=sample_route["parcel"],
            results=sample_quotes,
        )
        assert result is True

        # Test get
        mock_client.get.return_value = None
        result = service.get(
            pickup=sample_route["pickup"],
            delivery=sample_route["delivery"],
            parcel=sample_route["parcel"],
        )
        assert result is None
