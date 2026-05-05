import pytest
import uuid


@pytest.fixture
def quote_with_results(client, auth_headers, mock_courier):
    pickup = client.post(
        "/addresses",
        headers=auth_headers,
        json={"line1": "123 Main St", "city": "Cape Town", "postal_code": "8001", "country_code": "ZA"},
    ).json()

    delivery = client.post(
        "/addresses",
        headers=auth_headers,
        json={"line1": "456 Oak Ave", "city": "Johannesburg", "postal_code": "2000", "country_code": "ZA"},
    ).json()

    quote = client.post(
        "/quotes",
        headers=auth_headers,
        json={
            "pickup_address_id": pickup["id"],
            "delivery_address_id": delivery["id"],
            "parcel": {"weight_kg": 5.0, "length_cm": 30, "width_cm": 20, "height_cm": 10},
        },
    ).json()

    return quote


@pytest.mark.asyncio
async def test_create_booking(client, auth_headers, quote_with_results, mock_courier):
    idempotency_key = str(uuid.uuid4())
    response = client.post(
        "/bookings",
        headers={**auth_headers, "Idempotency-Key": idempotency_key},
        json={
            "quote_id": quote_with_results["id"],
            "courier_id": str(mock_courier.id),
            "courier_service_level": "economy",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending_payment"
    assert "id" in data


@pytest.mark.asyncio
async def test_booking_idempotency(client, auth_headers, quote_with_results, mock_courier):
    idempotency_key = str(uuid.uuid4())
    headers = {**auth_headers, "Idempotency-Key": idempotency_key}
    payload = {
        "quote_id": quote_with_results["id"],
        "courier_id": str(mock_courier.id),
        "courier_service_level": "economy",
    }

    response1 = client.post("/bookings", headers=headers, json=payload)
    response2 = client.post("/bookings", headers=headers, json=payload)

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response1.json()["id"] == response2.json()["id"]


@pytest.mark.asyncio
async def test_list_bookings(client, auth_headers, quote_with_results, mock_courier):
    idempotency_key = str(uuid.uuid4())
    client.post(
        "/bookings",
        headers={**auth_headers, "Idempotency-Key": idempotency_key},
        json={
            "quote_id": quote_with_results["id"],
            "courier_id": str(mock_courier.id),
            "courier_service_level": "economy",
        },
    )

    response = client.get("/bookings", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_booking_requires_idempotency_key(client, auth_headers, quote_with_results, mock_courier):
    response = client.post(
        "/bookings",
        headers=auth_headers,
        json={
            "quote_id": quote_with_results["id"],
            "courier_id": str(mock_courier.id),
        },
    )
    assert response.status_code == 400
    assert "Idempotency-Key" in response.json()["detail"]
