"""TCG (Shiplogic) adapter tests — mocked httpx to avoid network."""

from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.couriers.base import CourierAdapterError
from app.integrations.couriers.tcg import TCGAdapter


SAMPLE_ADDRESS = {
    "line1": "377 Fairy Glen St",
    "suburb": "Lynnwood Park",
    "city": "Pretoria",
    "province": "Gauteng",
    "postal_code": "0081",
    "country_code": "ZA",
    "latitude": "-25.806",
    "longitude": "28.334",
}

SAMPLE_PARCEL = {"weight_kg": 2.0, "length_cm": 20, "width_cm": 20, "height_cm": 10}


def _mock_transport(handler):
    return httpx.MockTransport(handler)


def _adapter_with_transport(transport):
    a = TCGAdapter(api_token="test-token", base_url="https://fake.shiplogic.com")
    # monkeypatch _request to route through the mock transport
    original_request = a._request

    async def patched_request(method, path, **kwargs):
        url = f"{a.base_url}{path}"
        async with httpx.AsyncClient(transport=transport, timeout=a.timeout) as client:
            return await client.request(method, url, headers=a._headers(), **kwargs)

    a._request = patched_request  # type: ignore
    return a


@pytest.mark.asyncio
async def test_get_quote_maps_response_to_quoteresults():
    rates_body = {
        "rates": [
            {
                "rate": 150.00,
                "service_level": {"code": "ECO", "name": "Economy"},
                "estimated_delivery_from": "2026-05-01T00:00:00Z",
                "estimated_delivery_to": "2026-05-03T00:00:00Z",
            },
            {
                "rate": 225.50,
                "service_level": {"code": "OVN", "name": "Overnight"},
                "estimated_delivery_from": "2026-05-01T00:00:00Z",
                "estimated_delivery_to": "2026-05-02T00:00:00Z",
            },
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/rates"
        body = json.loads(request.content)
        assert "collection_address" in body
        assert body["parcels"][0]["submitted_weight_kg"] == 2.0
        return httpx.Response(200, json=rates_body)

    adapter = _adapter_with_transport(_mock_transport(handler))
    results = await adapter.get_quote(pickup=SAMPLE_ADDRESS, delivery=SAMPLE_ADDRESS, parcel=SAMPLE_PARCEL)
    assert len(results) == 2
    assert {r.service_level for r in results} == {"ECO", "OVN"}

    eco = next(r for r in results if r.service_level == "ECO")
    assert eco.price_total == 15000  # R150 -> 15000 cents
    assert eco.estimated_delivery_days == 2  # May1 -> May3 = 2 days

    ovn = next(r for r in results if r.service_level == "OVN")
    assert ovn.price_total == 22550
    assert ovn.estimated_delivery_days == 1


@pytest.mark.asyncio
async def test_get_quote_applies_markup():
    rates_body = {"rates": [{"rate": 100, "service_level": {"code": "ECO", "name": "Economy"}}]}

    def handler(request):
        return httpx.Response(200, json=rates_body)

    a = _adapter_with_transport(_mock_transport(handler))
    a.markup_pct = 20
    results = await a.get_quote(pickup=SAMPLE_ADDRESS, delivery=SAMPLE_ADDRESS, parcel=SAMPLE_PARCEL)
    # R100 base +20% markup -> R120 -> 12000 cents
    assert results[0].price_total == 12000


@pytest.mark.asyncio
async def test_get_quote_non_2xx_raises():
    def handler(request):
        return httpx.Response(400, text="bad request")

    a = _adapter_with_transport(_mock_transport(handler))
    with pytest.raises(CourierAdapterError):
        await a.get_quote(pickup=SAMPLE_ADDRESS, delivery=SAMPLE_ADDRESS, parcel=SAMPLE_PARCEL)


@pytest.mark.asyncio
async def test_missing_token_raises():
    a = TCGAdapter(api_token=None, base_url="https://fake.shiplogic.com")
    with pytest.raises(CourierAdapterError):
        await a.get_quote(pickup=SAMPLE_ADDRESS, delivery=SAMPLE_ADDRESS, parcel=SAMPLE_PARCEL)


@pytest.mark.asyncio
async def test_create_shipment_returns_tracking_reference():
    def handler(request):
        assert request.url.path == "/shipments"
        body = json.loads(request.content)
        assert body["service_level_code"] == "ECO"
        return httpx.Response(
            200,
            json={
                "id": 108649,
                "short_tracking_reference": "3BM3",
                "custom_tracking_reference": "SLX3BM3",
            },
        )

    a = _adapter_with_transport(_mock_transport(handler))
    booking = {
        "collection_address": SAMPLE_ADDRESS,
        "delivery_address": SAMPLE_ADDRESS,
        "collection_contact": {"name": "Sender", "email": "s@x.co.za", "mobile_number": "012"},
        "delivery_contact": {"name": "Rx", "email": "r@x.co.za", "mobile_number": "013"},
        "parcels": [SAMPLE_PARCEL],
        "service_level_code": "ECO",
        "customer_reference": "booking-1",
    }
    result = await a.create_shipment(booking=booking)
    assert result["tracking_reference"] == "3BM3"
    assert result["shipment_id"] == "108649"


@pytest.mark.asyncio
async def test_track_shipment_normalises_events():
    body = {
        "shipments": [
            {
                "tracking_events": [
                    {"date": "2025-06-17T09:16:51.391Z", "status": "submitted", "message": ""},
                    {"date": "2025-06-17T12:23:30.493Z", "status": "at-hub", "message": "At PTA hub", "location": "PTA"},
                    {"date": "2025-06-17T12:22:32.632Z", "status": "collected", "message": ""},
                ]
            }
        ]
    }

    def handler(request):
        assert request.url.path == "/shipments"
        return httpx.Response(200, json=body)

    a = _adapter_with_transport(_mock_transport(handler))
    events = await a.track_shipment(tracking_reference="3BM3")
    assert len(events) == 3
    # Chronological
    assert events[0]["status"] == "submitted"
    assert events[-1]["status"] == "at-hub"


@pytest.mark.asyncio
async def test_cancel_shipment_posts_to_cancel_endpoint():
    def handler(request):
        assert request.url.path == "/shipments/cancel"
        body = json.loads(request.content)
        assert body["tracking_reference"] == "3BM3"
        return httpx.Response(200, json={"status": "cancelled"})

    a = _adapter_with_transport(_mock_transport(handler))
    assert (await a.cancel_shipment(tracking_reference="3BM3"))["status"] == "cancelled"
