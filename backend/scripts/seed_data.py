#!/usr/bin/env python3
"""Seed database with initial courier data and test user."""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.courier import Courier
from app.models.user import User
from app.utils.security import hash_password


def seed_couriers(db):
    """Seed courier partners."""
    couriers = [
        {
            "code": "mock",
            "name": "Mock Courier (Dev Only)",
            "is_enabled": True,
            "base_markup_pct": 0,
            "commission_pct": 10,
            "rating": 4,
        },
        {
            "code": "aramex",
            "name": "Aramex",
            "is_enabled": True,
            "base_markup_pct": 5,
            "commission_pct": 12,
            "rating": 4,
        },
        {
            "code": "courier_guy",
            "name": "The Courier Guy",
            "is_enabled": True,
            "base_markup_pct": 3,
            "commission_pct": 10,
            "rating": 5,
        },
        {
            "code": "pargo",
            "name": "Pargo",
            "is_enabled": True,
            "base_markup_pct": 0,
            "commission_pct": 8,
            "rating": 4,
        },
    ]

    for courier_data in couriers:
        existing = db.query(Courier).filter(Courier.code == courier_data["code"]).first()
        if not existing:
            courier = Courier(**courier_data)
            db.add(courier)
            print(f"✓ Created courier: {courier_data['name']}")
        else:
            print(f"- Courier already exists: {courier_data['name']}")

    db.commit()


def seed_test_user(db):
    """Seed a test user account."""
    test_email = "test@send-it.local"
    existing = db.query(User).filter(User.email == test_email).first()

    if not existing:
        user = User(
            email=test_email,
            password_hash=hash_password("pass123"),
            first_name="Test",
            last_name="User",
            phone="+27123456789",
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        db.commit()
        print(f"✓ Created test user: {test_email} / pass123")
    else:
        print(f"- Test user already exists: {test_email}")


def seed_admin_user(db):
    """Seed an admin user account."""
    admin_email = "admin@send-it.local"
    existing = db.query(User).filter(User.email == admin_email).first()

    if not existing:
        user = User(
            email=admin_email,
            password_hash=hash_password("admin123"),
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_admin=True,
        )
        db.add(user)
        db.commit()
        print(f"✓ Created admin user: {admin_email} / admin123")
    else:
        print(f"- Admin user already exists: {admin_email}")


def main():
    print("🌱 Seeding database...")
    db = SessionLocal()

    try:
        seed_couriers(db)
        seed_test_user(db)
        seed_admin_user(db)
        print("\n✅ Database seeded successfully!")
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
