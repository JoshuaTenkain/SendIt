from __future__ import annotations

import random

from app.integrations.couriers.base import CourierAdapter, QuoteResult


class MockCourierAdapter(CourierAdapter):
    courier_code = "mock"
    courier_name = "Mock Courier"

    async def get_quote(self, *, pickup: dict, delivery: dict, parcel: dict) -> list[QuoteResult]:
        weight = float(parcel.get("weight_kg", 1.0))
        base = int(5000 + weight * 800)
        return [
            QuoteResult(
                courier_code=self.courier_code,
                courier_name=self.courier_name,
                service_level="economy",
                price_total=base,
                currency="ZAR",
                estimated_delivery_days=3,
                raw={"mock": True},
            ),
            QuoteResult(
                courier_code=self.courier_code,
                courier_name=self.courier_name,
                service_level="next_day",
                price_total=base + random.randint(1200, 2500),
                currency="ZAR",
                estimated_delivery_days=1,
                raw={"mock": True},
            ),
        ]

    async def create_shipment(self, *, booking: dict) -> dict:
        return {"shipment_id": f"MOCK-{booking['id']}", "tracking_reference": f"TRK-{booking['id']}"}

    async def track_shipment(self, *, tracking_reference: str) -> list[dict]:
        return [
            {"status": "created", "description": "Shipment created", "occurred_at": "2026-03-08T10:00:00Z"},
            {"status": "in_transit", "description": "In transit", "occurred_at": "2026-03-09T10:00:00Z"},
        ]
