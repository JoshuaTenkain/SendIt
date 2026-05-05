import pytest
from app.integrations.couriers.mock import MockCourierAdapter
from app.integrations.couriers.registry import CourierRegistry


@pytest.mark.asyncio
async def test_mock_adapter_get_quote():
    adapter = MockCourierAdapter()
    pickup = {"city": "Cape Town", "postal_code": "8001"}
    delivery = {"city": "Johannesburg", "postal_code": "2000"}
    parcel = {"weight_kg": 5.0, "length_cm": 30, "width_cm": 20, "height_cm": 10}

    results = await adapter.get_quote(pickup=pickup, delivery=delivery, parcel=parcel)

    assert len(results) > 0
    for result in results:
        assert result.courier_code == "mock"
        assert result.price_total > 0
        assert result.currency == "ZAR"
        assert result.estimated_delivery_days > 0


@pytest.mark.asyncio
async def test_mock_adapter_create_shipment():
    adapter = MockCourierAdapter()
    booking = {"id": "test-booking-123"}

    result = await adapter.create_shipment(booking=booking)

    assert "shipment_id" in result
    assert "tracking_reference" in result
    assert "MOCK" in result["shipment_id"]


@pytest.mark.asyncio
async def test_mock_adapter_track_shipment():
    adapter = MockCourierAdapter()
    tracking_ref = "TRK-123"

    events = await adapter.track_shipment(tracking_reference=tracking_ref)

    assert len(events) > 0
    for event in events:
        assert "status" in event
        assert "occurred_at" in event


def test_courier_registry():
    registry = CourierRegistry()
    adapters = registry.get_enabled(None)

    assert len(adapters) > 0
    assert any(a.courier_code == "mock" for a in adapters)


def test_courier_registry_get_specific():
    registry = CourierRegistry()
    adapter = registry.get("mock")

    assert adapter.courier_code == "mock"
    assert adapter.courier_name == "Mock Courier"
