import pytest


def test_create_address(client, auth_headers):
    response = client.post(
        "/addresses",
        headers=auth_headers,
        json={
            "label": "Home",
            "line1": "123 Main St",
            "city": "Cape Town",
            "postal_code": "8001",
            "country_code": "ZA",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["label"] == "Home"
    assert data["line1"] == "123 Main St"
    assert "id" in data


def test_list_addresses(client, auth_headers):
    client.post(
        "/addresses",
        headers=auth_headers,
        json={"line1": "123 Main St", "city": "Cape Town", "postal_code": "8001", "country_code": "ZA"},
    )
    client.post(
        "/addresses",
        headers=auth_headers,
        json={"line1": "456 Oak Ave", "city": "Johannesburg", "postal_code": "2000", "country_code": "ZA"},
    )

    response = client.get("/addresses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_update_address(client, auth_headers):
    create_response = client.post(
        "/addresses",
        headers=auth_headers,
        json={"line1": "123 Main St", "city": "Cape Town", "postal_code": "8001", "country_code": "ZA"},
    )
    address_id = create_response.json()["id"]

    response = client.patch(f"/addresses/{address_id}", headers=auth_headers, json={"label": "Work"})
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Work"


def test_delete_address(client, auth_headers):
    create_response = client.post(
        "/addresses",
        headers=auth_headers,
        json={"line1": "123 Main St", "city": "Cape Town", "postal_code": "8001", "country_code": "ZA"},
    )
    address_id = create_response.json()["id"]

    response = client.delete(f"/addresses/{address_id}", headers=auth_headers)
    assert response.status_code == 204

    get_response = client.get("/addresses", headers=auth_headers)
    assert len(get_response.json()) == 0


def test_addresses_require_auth(client):
    response = client.get("/addresses")
    assert response.status_code == 401
