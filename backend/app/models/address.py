from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    label: Mapped[str | None] = mapped_column(String(120), nullable=True)

    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    suburb: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    province: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, server_default="ZA")

    latitude: Mapped[str | None] = mapped_column(String(32), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("line1 <> ''", name="ck_addresses_line1_not_empty"),
        CheckConstraint("city <> ''", name="ck_addresses_city_not_empty"),
        CheckConstraint("postal_code <> ''", name="ck_addresses_postal_code_not_empty"),
        CheckConstraint("char_length(country_code) = 2", name="ck_addresses_country_code_len"),
    )
