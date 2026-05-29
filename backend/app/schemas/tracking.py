from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TrackingEventOut(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    status: str
    description: str | None
    location: str | None
    latitude: float | None = None
    longitude: float | None = None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class TrackingSummaryOut(BaseModel):
    """Tracking summary for a booking."""

    booking_id: str
    tracking_reference: str | None
    current_status: str
    current_location: str | None
    current_coordinates: dict | None = None
    events: list[dict]
    last_update: str | None


class DeliveryIssueCreate(BaseModel):
    """Create a delivery issue."""

    issue_type: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=1000)
    photos: list[str] | None = None


class DeliveryIssueResolve(BaseModel):
    """Resolve a delivery issue."""

    resolution_type: str = Field(..., min_length=1, max_length=80)
    resolution_amount: int | None = None
    resolution_notes: str | None = Field(None, max_length=500)


class DeliveryIssueOut(BaseModel):
    """Delivery issue output."""

    id: uuid.UUID
    booking_id: uuid.UUID
    issue_type: str
    description: str
    photos: list[str]
    status: str
    resolution_type: str | None
    resolution_amount: int | None
    resolution_notes: str | None
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class TrackingWebhookCreate(BaseModel):
    """Create a tracking webhook."""

    url: str = Field(..., min_length=10, max_length=2048)
    events: list[str] = Field(..., min_items=1)


class TrackingWebhookOut(BaseModel):
    """Tracking webhook output."""

    id: uuid.UUID
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime
    last_triggered_at: datetime | None

    model_config = {"from_attributes": True}
