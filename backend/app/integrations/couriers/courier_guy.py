from __future__ import annotations

from app.integrations.couriers.base import CourierAdapter, QuoteResult


class CourierGuyAdapter(CourierAdapter):
    courier_code = "courier_guy"
    courier_name = "The Courier Guy"

    async def get_quote(self, *, pickup: dict, delivery: dict, parcel: dict) -> list[QuoteResult]:
        weight = float(parcel.get("weight_kg", 1.0))
        price = int(9500 + weight * 850)
        return [
            QuoteResult(
                courier_code=self.courier_code,
                courier_name=self.courier_name,
                service_level="next_day",
                price_total=price,
                currency="ZAR",
                estimated_delivery_days=1,
                raw={"provider": "stub"},
            )
        ]

    async def create_shipment(self, *, booking: dict) -> dict:
        raise NotImplementedError

    async def track_shipment(self, *, tracking_reference: str) -> list[dict]:
        raise NotImplementedError
