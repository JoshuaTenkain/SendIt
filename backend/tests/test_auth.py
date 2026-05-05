import pytest


def test_signup(client):
    response = client.post(
        "/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["first_name"] == "New"
    assert "id" in data


def test_signup_duplicate_email(client, test_user):
    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, test_user):
    response = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user):
    response = client.post("/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "password123"})
    assert response.status_code == 401
