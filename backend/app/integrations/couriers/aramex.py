"""Aramex South Africa adapter.

Implements REST API integration with Aramex for quote, shipment, and tracking.
Auth: API key + account number (env vars).
Base URL: https://api.aramex.com/ShippingAPI/REST/v1.0
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


class AramexError(CourierAdapterError):
    """Raised on a non-2xx response from Aramex."""


def _address_payload(addr: dict) -> dict:
    """Map our Address dict to Aramex format."""
    return {
        "Line1": addr.get("line1", ""),
        "Line2": addr.get("line2", ""),
        "City": addr.get("city", ""),
        "StateOrProvinceCode": addr.get("province", ""),
        "PostalCode": addr.get("postal_code", ""),
        "CountryCode": (addr.get("country_code") or "ZA").upper(),
    }


class AramexAdapter(CourierAdapter):
    courier_code = "aramex"
    courier_name = "Aramex"
    supports_api = True

    def __init__(
        self,
        *,
        api_key: str | None = None,
        account_number: str | None = None,
        base_url: str | None = None,
        timeout: httpx.Timeout | None = None,
        markup_pct: int = 0,
    ):
        self.api_key = api_key or settings.aramex_api_key
        self.account_number = account_number or settings.aramex_account_number
        self.base_url = (base_url or "https://api.aramex.com/ShippingAPI/REST/v1.0").rstrip("/")
        self.timeout = timeout or _DEFAULT_TIMEOUT
        self.markup_pct = markup_pct

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise CourierAdapterError("ARAMEX_API_KEY is not configured")
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
        """Get shipping rates from Aramex."""
        body = {
            "ShipmentDetails": {
                "Dimensions": {
                    "Length": float(parcel.get("length_cm", 10)),
                    "Width": float(parcel.get("width_cm", 10)),
                    "Height": float(parcel.get("height_cm", 10)),
                    "Unit": "CM",
                },
                "Weight": {
                    "Value": float(parcel.get("weight_kg", 1.0)),
                    "Unit": "KG",
                },
                "InsuredValue": {
                    "Amount": float(parcel.get("value_zar", 0)),
                    "CurrencyCode": "ZAR",
                },
            },
            "Shipper": _address_payload(pickup),
            "Consignee": _address_payload(delivery),
            "AccountNumber": self.account_number,
        }

        try:
            resp = await self._request("POST", "/rates", json=body)
        except (httpx.TransportError, RetryError) as e:
            logger.warning("aramex_rates_network_error", error=str(e))
            raise CourierAdapterError(f"Aramex network error: {e}") from e

        if resp.status_code != 200:
            logger.warning("aramex_rates_http_error", status=resp.status_code, body=resp.text[:500])
            raise AramexError(f"Aramex /rates returned {resp.status_code}")

        data = resp.json()
        rates = data.get("Rates", [])

        results: list[QuoteResult] = []
        for rate in rates:
            total_charge = rate.get("TotalChargeAmount", 0)
            cents = int(round(float(total_charge) * 100))
            if self.markup_pct:
                cents = int(round(cents * (100 + self.markup_pct) / 100))

            service_name = rate.get("ServiceType", "Standard")
            service_code = service_name.lower().replace(" ", "_")

            results.append(
                QuoteResult(
                    courier_code=self.courier_code,
                    courier_name=self.courier_name,
                    service_level=service_code,
                    service_level_display=service_name,
                    price_total=cents,
                    currency="ZAR",
                    estimated_delivery_days=int(rate.get("DeliveryDays", 2)),
                    raw=rate,
                )
            )
        return results

    async def create_shipment(self, *, booking: dict) -> dict:
        """Create a shipment with Aramex."""
        body = {
            "ShipmentDetails": {
                "Dimensions": {
                    "Length": float(booking["parcels"][0].get("length_cm", 10)),
                    "Width": float(booking["parcels"][0].get("width_cm", 10)),
                    "Height": float(booking["parcels"][0].get("height_cm", 10)),
                    "Unit": "CM",
                },
                "Weight": {
                    "Value": float(booking["parcels"][0].get("weight_kg", 1.0)),
                    "Unit": "KG",
                },
            },
            "Shipper": _address_payload(booking["collection_address"]),
            "Consignee": _address_payload(booking["delivery_address"]),
            "ShipperContact": {
                "Department": booking["collection_contact"].get("name", ""),
                "EmailAddress": booking["collection_contact"].get("email", ""),
                "PhoneNumber": booking["collection_contact"].get("mobile_number", ""),
            },
            "ConsigneeContact": {
                "Department": booking["delivery_contact"].get("name", ""),
                "EmailAddress": booking["delivery_contact"].get("email", ""),
                "PhoneNumber": booking["delivery_contact"].get("mobile_number", ""),
            },
            "AccountNumber": self.account_number,
            "Reference": booking.get("customer_reference", ""),
        }

        resp = await self._request("POST", "/shipments", json=body)
        if resp.status_code not in (200, 201):
            logger.warning("aramex_shipment_create_error", status=resp.status_code, body=resp.text[:500])
            raise AramexError(f"Aramex /shipments returned {resp.status_code}")

        data = resp.json()
        shipment = data.get("Shipment", data)

        return {
            "shipment_id": str(shipment.get("ShipmentID", "")),
            "tracking_reference": str(shipment.get("TrackingNumber", "")),
            "raw": shipment,
        }

    async def track_shipment(self, *, tracking_reference: str) -> list[dict]:
        """Track a shipment with Aramex."""
        resp = await self._request("GET", f"/shipments/{tracking_reference}")
        if resp.status_code != 200:
            raise AramexError(f"Aramex tracking returned {resp.status_code}")

        data = resp.json()
        shipment = data.get("Shipment", {})
        events = shipment.get("TrackingEvents", [])

        out: list[dict] = []
        for ev in events:
            ts = ev.get("EventDate")
            try:
                occurred = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.now(timezone.utc)
            except (ValueError, AttributeError):
                occurred = datetime.now(timezone.utc)

            out.append(
                {
                    "status": ev.get("EventCode", "unknown").lower(),
                    "description": ev.get("EventDescription", ""),
                    "location": ev.get("Location", ""),
                    "occurred_at": occurred,
                    "raw": ev,
                }
            )

        out.sort(key=lambda e: e["occurred_at"])
        return out

    async def cancel_shipment(self, *, tracking_reference: str) -> dict:
        """Cancel a shipment with Aramex."""
        resp = await self._request("POST", f"/shipments/{tracking_reference}/cancel", json={})
        if resp.status_code not in (200, 204):
            raise AramexError(f"Aramex cancel returned {resp.status_code}")
        try:
            return resp.json()
        except ValueError:
            return {"status": "cancelled"}
