from __future__ import annotations

import uuid

from pydantic import BaseModel


class CourierOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    is_enabled: bool
    base_markup_pct: int
    commission_pct: int
    rating: int | None

    model_config = {"from_attributes": True}


class CourierUpdate(BaseModel):
    is_enabled: bool | None = None
    commission_pct: int | None = None
    base_markup_pct: int | None = None
    rating: int | None = None
