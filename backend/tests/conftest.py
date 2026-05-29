import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test environment variables BEFORE importing app config
os.environ.setdefault("SENDIT_ENV", "test")
os.environ.setdefault("SENDIT_JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("SENDIT_GUEST_TOKEN_SECRET", "test-guest-secret-key-for-testing-only")
os.environ.setdefault("SENDIT_DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SENDIT_PAYFAST_MERCHANT_ID", "test-merchant")
os.environ.setdefault("SENDIT_PAYFAST_MERCHANT_KEY", "test-key")
os.environ.setdefault("SENDIT_PAYFAST_PASSPHRASE", "test-passphrase")

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.courier import Courier
from app.utils.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    user = User(
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    response = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, admin_user):
    response = client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_courier(db):
    courier = Courier(
        code="mock",
        name="Mock Courier",
        is_enabled=True,
        base_markup_pct=0,
        commission_pct=10,
        rating=4,
    )
    db.add(courier)
    db.commit()
    db.refresh(courier)
    return courier
