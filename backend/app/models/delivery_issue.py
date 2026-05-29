"""Delivery issue model for tracking delivery problems and resolutions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeliveryIssue(Base):
    __tablename__ = "delivery_issues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)

    issue_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)

    photos: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")

    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="open", index=True)
    resolution_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resolution_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
