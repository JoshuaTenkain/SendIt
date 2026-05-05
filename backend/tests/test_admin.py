import pytest


def test_admin_list_couriers(client, admin_headers, mock_courier):
    response = client.get("/admin/couriers", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_admin_update_courier(client, admin_headers, mock_courier):
    response = client.patch(
        f"/admin/couriers/{mock_courier.id}",
        headers=admin_headers,
        params={"is_enabled": False, "commission_pct": 15},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_enabled"] is False
    assert data["commission_pct"] == 15


def test_admin_endpoints_require_admin(client, auth_headers):
    response = client.get("/admin/couriers", headers=auth_headers)
    assert response.status_code == 403


def test_admin_revenue_summary(client, admin_headers):
    response = client.get("/admin/revenue", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "total_commission" in data
    assert "booking_count" in data
