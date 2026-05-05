from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuoteResult:
    courier_code: str
    courier_name: str
    service_level: str
    price_total: int  # cents, total the customer pays (incl. surcharges+tax from adapter)
    currency: str
    estimated_delivery_days: int
    raw: dict
    service_level_display: str | None = None
    # Optional detailed breakdown (for CSV/pricing-engine adapters)
    pricing_breakdown: dict | None = None
    # Optional signals for ranking (0..1)
    reliability_score: float | None = None


class CourierAdapterError(RuntimeError):
    """Base error for courier adapters."""


class CourierAdapter:
    courier_code: str
    courier_name: str
    supports_api: bool = False  # True when the adapter calls an external API

    async def get_quote(self, *, pickup: dict, delivery: dict, parcel: dict) -> list[QuoteResult]:
        raise NotImplementedError

    async def create_shipment(self, *, booking: dict) -> dict:
        raise NotImplementedError

    async def track_shipment(self, *, tracking_reference: str) -> list[dict]:
        raise NotImplementedError

    async def cancel_shipment(self, *, tracking_reference: str) -> dict:
        raise NotImplementedError
