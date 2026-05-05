from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class TrackingEventOut(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    status: str
    description: str | None
    location: str | None
    occurred_at: datetime

    model_config = {"from_attributes": True}
