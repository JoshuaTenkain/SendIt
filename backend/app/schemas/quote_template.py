"""Schemas for quote templates."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QuoteTemplateCreate(BaseModel):
    """Create a new quote template."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    pickup_address_id: UUID
    delivery_address_id: UUID
    parcel_template: dict = Field(...)
    urgency: str | None = Field(None, max_length=40)


class QuoteTemplateUpdate(BaseModel):
    """Update a quote template."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    urgency: str | None = Field(None, max_length=40)


class QuoteTemplateOut(BaseModel):
    """Quote template output."""

    id: UUID
    name: str
    description: str | None
    pickup_address_id: UUID
    delivery_address_id: UUID
    parcel_template: dict
    urgency: str | None
    usage_count: int
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
