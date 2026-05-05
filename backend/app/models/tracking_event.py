from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    location: Mapped[str | None] = mapped_column(String(120), nullable=True)

    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status <> ''", name="ck_tracking_events_status_not_empty"),
        Index("ix_tracking_events_booking_id_occurred_at", "booking_id", "occurred_at"),
    )
