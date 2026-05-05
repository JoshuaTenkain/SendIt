from __future__ import annotations

import uuid

from pydantic import BaseModel


class TransactionOut(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    provider: str
    status: str
    amount: str
    currency: str
    provider_reference: str | None

    model_config = {"from_attributes": True}
