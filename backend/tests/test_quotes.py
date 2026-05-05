import pytest


@pytest.fixture
def addresses(client, auth_headers):
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

    return {"pickup": pickup, "delivery": delivery}


@pytest.mark.asyncio
async def test_create_quote(client, auth_headers, addresses, mock_courier):
    response = client.post(
        "/quotes",
        headers=auth_headers,
        json={
            "pickup_address_id": addresses["pickup"]["id"],
            "delivery_address_id": addresses["delivery"]["id"],
            "parcel": {"weight_kg": 5.0, "length_cm": 30, "width_cm": 20, "height_cm": 10},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "results" in data
    assert data["results"] is not None
    assert "quotes" in data["results"]
    assert len(data["results"]["quotes"]) > 0


@pytest.mark.asyncio
async def test_get_quote(client, auth_headers, addresses, mock_courier):
    create_response = client.post(
        "/quotes",
        headers=auth_headers,
        json={
            "pickup_address_id": addresses["pickup"]["id"],
            "delivery_address_id": addresses["delivery"]["id"],
            "parcel": {"weight_kg": 5.0, "length_cm": 30, "width_cm": 20, "height_cm": 10},
        },
    )
    quote_id = create_response.json()["id"]

    response = client.get(f"/quotes/{quote_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == quote_id


@pytest.mark.asyncio
async def test_quote_ranking(client, auth_headers, addresses, mock_courier):
    response = client.post(
        "/quotes",
        headers=auth_headers,
        json={
            "pickup_address_id": addresses["pickup"]["id"],
            "delivery_address_id": addresses["delivery"]["id"],
            "parcel": {"weight_kg": 5.0, "length_cm": 30, "width_cm": 20, "height_cm": 10},
        },
    )
    data = response.json()
    quotes = data["results"]["quotes"]

    for i in range(len(quotes) - 1):
        assert quotes[i]["price_total"] <= quotes[i + 1]["price_total"]
