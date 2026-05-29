"""Quote caching service using Redis."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import redis
import structlog

from app.config import settings
from app.integrations.couriers.base import QuoteResult

logger = structlog.get_logger()


class QuoteCacheService:
    """Cache quote results to reduce API calls and improve latency."""

    CACHE_TTL_SECONDS = 300  # 5 minutes
    CACHE_KEY_PREFIX = "quote:"

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or settings.redis_url
        self.ttl = self.CACHE_TTL_SECONDS
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True) if self.redis_url else None
            if self.client:
                self.client.ping()
                logger.info("redis_connected")
        except Exception as e:
            logger.warning("redis_connection_failed", error=str(e))
            self.client = None

    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self.client is not None

    def _make_cache_key(self, *, pickup: dict, delivery: dict, parcel: dict) -> str:
        """Generate a cache key from quote parameters."""
        key_data = {
            "pickup": {
                "city": pickup.get("city"),
                "province": pickup.get("province"),
                "postal_code": pickup.get("postal_code"),
            },
            "delivery": {
                "city": delivery.get("city"),
                "province": delivery.get("province"),
                "postal_code": delivery.get("postal_code"),
            },
            "parcel": {
                "weight_kg": parcel.get("weight_kg"),
                "length_cm": parcel.get("length_cm"),
                "width_cm": parcel.get("width_cm"),
                "height_cm": parcel.get("height_cm"),
            },
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()
        return f"{self.CACHE_KEY_PREFIX}{key_hash}"

    def get(self, *, pickup: dict, delivery: dict, parcel: dict) -> list[QuoteResult] | None:
        """Get cached quote results."""
        if not self.is_available():
            return None

        cache_key = self._make_cache_key(pickup=pickup, delivery=delivery, parcel=parcel)

        try:
            cached = self.client.get(cache_key)
            if cached:
                data = json.loads(cached)
                results = [
                    QuoteResult(
                        courier_code=r["courier_code"],
                        courier_name=r["courier_name"],
                        service_level=r["service_level"],
                        price_total=r["price_total"],
                        currency=r["currency"],
                        estimated_delivery_days=r["estimated_delivery_days"],
                        raw=r.get("raw", {}),
                        service_level_display=r.get("service_level_display"),
                        reliability_score=r.get("reliability_score"),
                    )
                    for r in data
                ]
                logger.info("quote_cache_hit", cache_key=cache_key)
                return results
        except Exception as e:
            logger.warning("quote_cache_get_failed", error=str(e))

        return None

    def set(self, *, pickup: dict, delivery: dict, parcel: dict, results: list[QuoteResult]) -> bool:
        """Cache quote results."""
        if not self.is_available():
            return False

        cache_key = self._make_cache_key(pickup=pickup, delivery=delivery, parcel=parcel)

        try:
            data = [
                {
                    "courier_code": r.courier_code,
                    "courier_name": r.courier_name,
                    "service_level": r.service_level,
                    "price_total": r.price_total,
                    "currency": r.currency,
                    "estimated_delivery_days": r.estimated_delivery_days,
                    "raw": r.raw,
                    "service_level_display": r.service_level_display,
                    "reliability_score": r.reliability_score,
                }
                for r in results
            ]
            self.client.setex(cache_key, self.ttl, json.dumps(data))
            logger.info("quote_cache_set", cache_key=cache_key, ttl=self.ttl)
            return True
        except Exception as e:
            logger.warning("quote_cache_set_failed", error=str(e))
            return False

    def invalidate_all(self) -> bool:
        """Invalidate all quote caches."""
        if not self.is_available():
            return False

        try:
            pattern = f"{self.CACHE_KEY_PREFIX}*"
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            logger.info("quote_cache_invalidated_all", count=len(keys) if keys else 0)
            return True
        except Exception as e:
            logger.warning("quote_cache_invalidate_failed", error=str(e))
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if not self.is_available():
            return {"available": False}

        try:
            pattern = f"{self.CACHE_KEY_PREFIX}*"
            keys = self.client.keys(pattern)
            info = self.client.info("stats")
            return {
                "available": True,
                "cached_quotes": len(keys) if keys else 0,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.warning("quote_cache_stats_failed", error=str(e))
            return {"available": False, "error": str(e)}


# Singleton instance
_cache_service: QuoteCacheService | None = None


def get_quote_cache_service() -> QuoteCacheService:
    """Get or create quote cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = QuoteCacheService()
    return _cache_service
