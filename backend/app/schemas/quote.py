from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class ParcelIn(BaseModel):
    weight_kg: float = Field(gt=0, le=1000)
    length_cm: float = Field(gt=0, le=300)
    width_cm: float = Field(gt=0, le=300)
    height_cm: float = Field(gt=0, le=300)
    value_zar: float | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=120)


class AddressSnapshot(BaseModel):
    """Inline address used for guest quotes (no saved Address row)."""

    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    suburb: str | None = Field(default=None, max_length=120)
    city: str = Field(min_length=1, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    postal_code: str = Field(min_length=3, max_length=20)
    country_code: str = Field(default="ZA", min_length=2, max_length=2)
    latitude: str | None = Field(default=None, max_length=32)
    longitude: str | None = Field(default=None, max_length=32)
    type: Literal["residential", "business", "counter", "locker"] | None = Field(default=None)


class QuoteCreate(BaseModel):
    """Authenticated quote creation (uses saved Address rows)."""

    pickup_address_id: uuid.UUID
    delivery_address_id: uuid.UUID
    parcel: ParcelIn
    urgency: Literal["same_day", "overnight", "economy"] | None = None
    budget_zar: float | None = Field(default=None, ge=0)


class QuoteCreateGuest(BaseModel):
    """Public quote creation (no auth)."""

    pickup: AddressSnapshot
    delivery: AddressSnapshot
    parcel: ParcelIn
    urgency: Literal["same_day", "overnight", "economy"] | None = None
    budget_zar: float | None = Field(default=None, ge=0)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    consent: bool = Field(default=False)

    @model_validator(mode="after")
    def _require_consent_if_email(self):
        # Storing email implies POPIA consent.
        if self.email and not self.consent:
            raise ValueError("consent must be true when providing an email")
        return self


class QuoteEmailRequest(BaseModel):
    email: EmailStr


class QuoteOut(BaseModel):
    id: uuid.UUID
    pickup_address_id: uuid.UUID | None = None
    delivery_address_id: uuid.UUID | None = None
    pickup_address_snapshot: dict | None = None
    delivery_address_snapshot: dict | None = None
    parcel: dict
    results: dict | None = None
    urgency: str | None = None
    budget_zar: int | None = None
    guest_email: str | None = None
    expires_at: datetime | None = None
    currency: str

    model_config = {"from_attributes": True}


class QuoteGuestOut(QuoteOut):
    """Returned from guest endpoints — includes a one-time magic-link token."""

    access_token: str
