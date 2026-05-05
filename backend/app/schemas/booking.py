from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class BookingCreate(BaseModel):
    quote_id: uuid.UUID
    courier_id: uuid.UUID
    courier_service_level: str | None = Field(default=None, max_length=80)


class BookingCreateGuest(BaseModel):
    """Create a booking from a guest quote via its magic-link access token."""

    quote_token: str
    courier_id: uuid.UUID
    courier_service_level: str | None = Field(default=None, max_length=80)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)


class BookingCancel(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class BookingOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    quote_id: uuid.UUID
    courier_id: uuid.UUID
    courier_service_level: str | None
    price_subtotal: str
    price_tax: str
    price_total: str
    currency: str
    status: str
    external_shipment_id: str | None
    tracking_reference: str | None
    public_short_code: str | None = None
    guest_email: str | None = None
    cancelled_at: datetime | None = None
    pricing_breakdown: dict | None = None

    model_config = {"from_attributes": True}


class BookingGuestOut(BookingOut):
    access_token: str
