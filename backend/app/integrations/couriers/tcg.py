"""The Courier Guy (Shiplogic) adapter.

Implements the REST endpoints from the Shiplogic Postman collection:
  * POST /rates
  * POST /shipments
  * GET  /shipments?tracking_reference=...
  * POST /shipments/cancel

Auth: Bearer token (env var SENDIT_TCG_API_TOKEN).
Base URL defaults to https://api.shiplogic.com; the prod host
https://api.portal.thecourierguy.co.za is equivalent and supported by
overriding SENDIT_TCG_BASE_URL.

Ranking fields (``service_level_code`` + ``estimated_delivery_from/to``) are
normalised into our internal ``QuoteResult``.
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
_DEFAULT_COUNTRY = "ZA"


class TCGError(CourierAdapterError):
    """Raised on a non-2xx response from Shiplogic."""


def _address_payload(addr: dict) -> dict:
    """Map our ``Address`` dict (see quote_service._address_to_dict) to Shiplogic format."""
    zone_map = {
        "Gauteng": "Gauteng", "Western Cape": "Western Cape", "KwaZulu-Natal": "KwaZulu-Natal",
        "Eastern Cape": "Eastern Cape", "Free State": "Free State", "Limpopo": "Limpopo",
        "Mpumalanga": "Mpumalanga", "North West": "North West", "Northern Cape": "Northern Cape",
    }
    province = addr.get("province") or ""
    payload = {
        "type": addr.get("type") or "residential",
        "company": addr.get("company") or "",
        "street_address": " ".join(filter(None, [addr.get("line1"), addr.get("line2")])) or addr.get("line1", ""),
        "local_area": addr.get("suburb") or "",
        "city": addr.get("city") or "",
        "zone": zone_map.get(province, province),
        "country": (addr.get("country_code") or _DEFAULT_COUNTRY).upper(),
        "code": addr.get("postal_code") or "",
    }
    lat = addr.get("latitude")
    lng = addr.get("longitude")
    if lat is not None and lng is not None:
        try:
            payload["lat"] = float(lat)
            payload["lng"] = float(lng)
        except (TypeError, ValueError):
            pass
    return payload


def _parcel_payload(parcel: dict) -> dict:
    return {
        "parcel_description": parcel.get("description") or "Parcel",
        "submitted_length_cm": float(parcel["length_cm"]),
        "submitted_width_cm": float(parcel["width_cm"]),
        "submitted_height_cm": float(parcel["height_cm"]),
        "submitted_weight_kg": float(parcel["weight_kg"]),
    }


def _estimate_days(rate: dict) -> int:
    """Estimate delivery days from rate.estimated_delivery_from/to.

    Shiplogic returns ISO timestamps; if unavailable we default to service code
    heuristics.
    """
    est_from = rate.get("estimated_delivery_from") or rate.get("service_level", {}).get(
        "collection_relative_time"
    )
    est_to = rate.get("estimated_delivery_to")
    if est_from and est_to:
        try:
            d0 = datetime.fromisoformat(est_from.replace("Z", "+00:00"))
            d1 = datetime.fromisoformat(est_to.replace("Z", "+00:00"))
            delta = (d1 - d0).days
            return max(delta, 1)
        except (ValueError, AttributeError):
            pass
    code = (rate.get("service_level", {}).get("code") or rate.get("service_level_code") or "").upper()
    return {"SD": 0, "OVN": 1, "ECO": 3, "ONX": 1}.get(code, 2)


class TCGAdapter(CourierAdapter):
    courier_code = "tcg"
    courier_name = "The Courier Guy"
    supports_api = True

    def __init__(
        self,
        *,
        api_token: str | None = None,
        base_url: str | None = None,
        timeout: httpx.Timeout | None = None,
        markup_pct: int = 0,
    ):
        self.api_token = api_token or settings.tcg_api_token
        self.base_url = (base_url or settings.tcg_base_url).rstrip("/")
        self.timeout = timeout or _DEFAULT_TIMEOUT
        self.markup_pct = markup_pct

    def _headers(self) -> dict[str, str]:
        if not self.api_token:
            raise CourierAdapterError("TCG_API_TOKEN is not configured")
        return {
            "Authorization": f"Bearer {self.api_token}",
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
        body = {
            "collection_address": _address_payload(pickup),
            "delivery_address": _address_payload(delivery),
            "parcels": [_parcel_payload(parcel)],
        }
        if parcel.get("value_zar"):
            body["declared_value"] = float(parcel["value_zar"])

        try:
            resp = await self._request("POST", "/rates", json=body)
        except (httpx.TransportError, RetryError) as e:
            logger.warning("tcg_rates_network_error", error=str(e))
            raise CourierAdapterError(f"TCG network error: {e}") from e

        if resp.status_code != 200:
            logger.warning("tcg_rates_http_error", status=resp.status_code, body=resp.text[:500])
            raise TCGError(f"TCG /rates returned {resp.status_code}")

        data = resp.json()
        rates = data.get("rates") or data.get("data") or []

        results: list[QuoteResult] = []
        for rate in rates:
            # Shiplogic returns the price in Rand (float). Convert to cents.
            rand = rate.get("rate") or rate.get("total_charge") or 0
            cents = int(round(float(rand) * 100))
            if self.markup_pct:
                cents = int(round(cents * (100 + self.markup_pct) / 100))

            service = rate.get("service_level") or {}
            service_code = service.get("code") or rate.get("service_level_code") or "unknown"
            service_name = service.get("name") or rate.get("service_level_name") or service_code

            results.append(
                QuoteResult(
                    courier_code=self.courier_code,
                    courier_name=self.courier_name,
                    service_level=service_code,
                    service_level_display=service_name,
                    price_total=cents,
                    currency="ZAR",
                    estimated_delivery_days=_estimate_days(rate),
                    raw=rate,
                )
            )
        return results

    async def create_shipment(self, *, booking: dict) -> dict:
        """``booking`` shape expected:
        {
            "collection_address": {...Address dict...},
            "delivery_address":   {...},
            "collection_contact": {"name":..., "mobile_number":..., "email":...},
            "delivery_contact":   {...},
            "parcels": [{"weight_kg":..., "length_cm":..., ...}],
            "service_level_code": "ECO",
            "customer_reference": "booking_id",
            "declared_value":   0,        # optional
        }
        """
        body = {
            "collection_address": _address_payload(booking["collection_address"]),
            "delivery_address": _address_payload(booking["delivery_address"]),
            "collection_contact": booking["collection_contact"],
            "delivery_contact": booking["delivery_contact"],
            "parcels": [_parcel_payload(p) for p in booking["parcels"]],
            "service_level_code": booking["service_level_code"],
            "mute_notifications": booking.get("mute_notifications", False),
        }
        if booking.get("customer_reference"):
            body["customer_reference"] = booking["customer_reference"]
        if booking.get("declared_value"):
            body["declared_value"] = float(booking["declared_value"])
        if booking.get("special_instructions_collection"):
            body["special_instructions_collection"] = booking["special_instructions_collection"]
        if booking.get("special_instructions_delivery"):
            body["special_instructions_delivery"] = booking["special_instructions_delivery"]

        resp = await self._request("POST", "/shipments", json=body)
        if resp.status_code not in (200, 201):
            logger.warning("tcg_shipment_create_error", status=resp.status_code, body=resp.text[:500])
            raise TCGError(f"TCG /shipments returned {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        # Shiplogic returns the full shipment object (often unwrapped)
        shipment = data.get("shipment") or data
        tracking_ref = (
            shipment.get("short_tracking_reference")
            or shipment.get("custom_tracking_reference")
            or shipment.get("tracking_reference")
        )
        return {
            "shipment_id": str(shipment.get("id", "")) or None,
            "tracking_reference": tracking_ref,
            "raw": shipment,
        }

    async def track_shipment(self, *, tracking_reference: str) -> list[dict]:
        resp = await self._request(
            "GET", "/shipments", params={"tracking_reference": tracking_reference}
        )
        if resp.status_code != 200:
            raise TCGError(f"TCG /shipments GET returned {resp.status_code}")

        data = resp.json()
        shipments = data.get("shipments") or data.get("data") or []
        if not shipments:
            return []
        shipment = shipments[0]
        events = shipment.get("tracking_events") or []

        out: list[dict] = []
        for ev in events:
            ts = ev.get("date") or ev.get("event_time")
            try:
                occurred = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.now(timezone.utc)
            except (ValueError, AttributeError):
                occurred = datetime.now(timezone.utc)
            out.append(
                {
                    "status": ev.get("status") or "unknown",
                    "description": ev.get("message") or "",
                    "location": ev.get("location") or "",
                    "occurred_at": occurred,
                    "raw": ev,
                }
            )
        # Sort chronologically oldest -> newest
        out.sort(key=lambda e: e["occurred_at"])
        return out

    async def cancel_shipment(self, *, tracking_reference: str) -> dict:
        resp = await self._request(
            "POST", "/shipments/cancel", json={"tracking_reference": tracking_reference}
        )
        if resp.status_code not in (200, 204):
            raise TCGError(f"TCG /shipments/cancel returned {resp.status_code}")
        try:
            return resp.json()
        except ValueError:
            return {"status": "cancelled"}


def default_tcg_adapter() -> TCGAdapter | None:
    """Return a configured adapter when TCG is enabled + has a token, else None."""
    if not settings.tcg_enabled or not settings.tcg_api_token:
        return None
    return TCGAdapter()
