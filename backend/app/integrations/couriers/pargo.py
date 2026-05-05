from __future__ import annotations

from app.integrations.couriers.base import CourierAdapter, QuoteResult


class PargoAdapter(CourierAdapter):
    courier_code = "pargo"
    courier_name = "Pargo"

    async def get_quote(self, *, pickup: dict, delivery: dict, parcel: dict) -> list[QuoteResult]:
        weight = float(parcel.get("weight_kg", 1.0))
        price = int(8000 + weight * 600)
        return [
            QuoteResult(
                courier_code=self.courier_code,
                courier_name=self.courier_name,
                service_level="economy",
                price_total=price,
                currency="ZAR",
                estimated_delivery_days=4,
                raw={"provider": "stub"},
            )
        ]

    async def create_shipment(self, *, booking: dict) -> dict:
        raise NotImplementedError

    async def track_shipment(self, *, tracking_reference: str) -> list[dict]:
        raise NotImplementedError
