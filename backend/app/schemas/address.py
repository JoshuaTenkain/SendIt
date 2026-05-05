from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class AddressBase(BaseModel):
    label: str | None = Field(default=None, max_length=120)
    line1: str = Field(max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    suburb: str | None = Field(default=None, max_length=120)
    city: str = Field(max_length=120)
    province: str | None = Field(default=None, max_length=120)
    postal_code: str = Field(max_length=20)
    country_code: str = Field(default="ZA", min_length=2, max_length=2)
    latitude: str | None = Field(default=None, max_length=32)
    longitude: str | None = Field(default=None, max_length=32)


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=120)
    line1: str | None = Field(default=None, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    suburb: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=20)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    latitude: str | None = Field(default=None, max_length=32)
    longitude: str | None = Field(default=None, max_length=32)


class AddressOut(AddressBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
