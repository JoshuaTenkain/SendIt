"""DHL Express adapter.

Implements REST API integration with DHL Express for quote, shipment, and tracking.
Supports both domestic (South Africa) and international shipping.
Auth: API key (env var).
Base URL: https://express.api.dhl.com/mydhl/in
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.integrations.couriers.base import CourierAdapter, CourierAdapterError, QuoteResult

logger = structlog.get_logger()

_DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class DHLError(CourierAdapterError):
    """Raised on a non-2xx response from DHL."""


def _address_payload(addr: dict) -> dict:
    """Map our Address dict to DHL format."""
    return {
        "addressLine1": addr.get("line1", ""),
        "addressLine2": addr.get("line2", ""),
        "cityName": addr.get("city", ""),
        "stateCode": addr.get("province", ""),
        "postalCode": addr.get("postal_code", ""),
        "countryCode": (addr.get("country_code") or "ZA").upper(),
    }


class DHLAdapter(CourierAdapter):
    courier_code = "dhl"
    courier_name = "DHL Express"
    supports_api = True

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: httpx.Timeout | None = None,
        markup_pct: int = 0,
    ):
        self.api_key = api_key or settings.dhl_api_key
        self.base_url = (base_url or "https://express.api.dhl.com/mydhl/in").rstrip("/")
        self.timeout = timeout or _DEFAULT_TIMEOUT
        self.markup_pct = markup_pct

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise CourierAdapterError("DHL_API_KEY is not configured")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.3, min=0.3, max=2.0),
        retry=retry_if_exception_type((httpx.TransportError, httpx.ReadTimeout)),
        reraise=True,
    )
    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.request(method, url, headers=self._headers(), **kwargs)
        return resp

    async def get_quote(self, *, pickup: dict, delivery: dict, parcel: dict) -> list[QuoteResult]:
        """Get shipping rates from DHL Express."""
        body = {
            "shipmentDetails": {
                "dimensions": {
                    "length": float(parcel.get("length_cm", 10)),
                    "width": float(parcel.get("width_cm", 10)),
                    "height": float(parcel.get("height_cm", 10)),
                    "unit": "cm",
                },
                "weight": {
                    "value": float(parcel.get("weight_kg", 1.0)),
                    "unit": "kg",
                },
                "insuredAmount": float(parcel.get("value_zar", 0)),
            },
            "pickup": _address_payload(pickup),
            "delivery": _address_payload(delivery),
            "plannedShippingDateAndTime": datetime.now(timezone.utc).isoformat(),
        }

        try:
            resp = await self._request("POST", "/rates", json=body)
        except (httpx.TransportError, RetryError) as e:
            logger.warning("dhl_rates_network_error", error=str(e))
            raise CourierAdapterError(f"DHL network error: {e}") from e

        if resp.status_code != 200:
            logger.warning("dhl_rates_http_error", status=resp.status_code, body=resp.text[:500])
            raise DHLError(f"DHL /rates returned {resp.status_code}")

        data = resp.json()
        products = data.get("products", [])

        results: list[QuoteResult] = []
        for product in products:
            total_price = product.get("totalPrice", [{}])[0].get("price", 0)
            cents = int(round(float(total_price) * 100))
            if self.markup_pct:
                cents = int(round(cents * (100 + self.markup_pct) / 100))

            service_name = product.get("productName", "Express")
            service_code = product.get("productCode", "express").lower()

            delivery_time = product.get("deliveryCapabilities", {})
            est_days = delivery_time.get("estimatedDeliveryDays", 2)

            results.append(
                QuoteResult(
                    courier_code=self.courier_code,
                    courier_name=self.courier_name,
                    service_level=service_code,
                    service_level_display=service_name,
                    price_total=cents,
                    currency="ZAR",
                    estimated_delivery_days=int(est_days),
                    raw=product,
                )
            )
        return results

    async def create_shipment(self, *, booking: dict) -> dict:
        """Create a shipment with DHL Express."""
        body = {
            "shipmentDetails": {
                "dimensions": {
                    "length": float(booking["parcels"][0].get("length_cm", 10)),
                    "width": float(booking["parcels"][0].get("width_cm", 10)),
                    "height": float(booking["parcels"][0].get("height_cm", 10)),
                    "unit": "cm",
                },
                "weight": {
                    "value": float(booking["parcels"][0].get("weight_kg", 1.0)),
                    "unit": "kg",
                },
            },
            "pickup": _address_payload(booking["collection_address"]),
            "delivery": _address_payload(booking["delivery_address"]),
            "pickupContact": {
                "companyName": booking["collection_contact"].get("name", ""),
                "email": booking["collection_contact"].get("email", ""),
                "phone": booking["collection_contact"].get("mobile_number", ""),
            },
            "deliveryContact": {
                "companyName": booking["delivery_contact"].get("name", ""),
                "email": booking["delivery_contact"].get("email", ""),
                "phone": booking["delivery_contact"].get("mobile_number", ""),
            },
            "customerReference": booking.get("customer_reference", ""),
        }

        resp = await self._request("POST", "/shipments", json=body)
        if resp.status_code not in (200, 201):
            logger.warning("dhl_shipment_create_error", status=resp.status_code, body=resp.text[:500])
            raise DHLError(f"DHL /shipments returned {resp.status_code}")

        data = resp.json()
        shipment = data.get("shipmentTrackingNumber", data)

        return {
            "shipment_id": str(data.get("shipmentId", "")),
            "tracking_reference": str(shipment),
            "raw": data,
        }

    async def track_shipment(self, *, tracking_reference: str) -> list[dict]:
        """Track a shipment with DHL Express."""
        resp = await self._request("GET", f"/shipments/{tracking_reference}")
        if resp.status_code != 200:
            raise DHLError(f"DHL tracking returned {resp.status_code}")

        data = resp.json()
        events = data.get("events", [])

        out: list[dict] = []
        for ev in events:
            ts = ev.get("timestamp")
            try:
                occurred = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.now(timezone.utc)
            except (ValueError, AttributeError):
                occurred = datetime.now(timezone.utc)

            out.append(
                {
                    "status": ev.get("status", "unknown").lower(),
                    "description": ev.get("description", ""),
                    "location": ev.get("location", {}).get("address", ""),
                    "occurred_at": occurred,
                    "raw": ev,
                }
            )

        out.sort(key=lambda e: e["occurred_at"])
        return out

    async def cancel_shipment(self, *, tracking_reference: str) -> dict:
        """Cancel a shipment with DHL Express."""
        resp = await self._request("DELETE", f"/shipments/{tracking_reference}")
        if resp.status_code not in (200, 204):
            raise DHLError(f"DHL cancel returned {resp.status_code}")
        try:
            return resp.json()
        except ValueError:
            return {"status": "cancelled"}
