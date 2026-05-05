from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nullable to support guest checkout; guest_email used for access
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)

    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    guest_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    public_short_code: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True, index=True)

    quote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="RESTRICT"), nullable=False, unique=True)

    courier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="RESTRICT"), nullable=False, index=True)

    courier_service_level: Mapped[str | None] = mapped_column(String(80), nullable=True)

    price_subtotal: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)
    price_tax: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    price_total: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="ZAR")

    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)

    external_shipment_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    tracking_reference: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    courier_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pricing_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    cancelled_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("char_length(currency) = 3", name="ck_bookings_currency_len"),
        CheckConstraint("idempotency_key <> ''", name="ck_bookings_idempotency_not_empty"),
        CheckConstraint("status <> ''", name="ck_bookings_status_not_empty"),
        Index("ix_bookings_user_id_created_at", "user_id", "created_at"),
        Index("ix_bookings_courier_id_created_at", "courier_id", "created_at"),
        Index("uq_bookings_user_id_idempotency_key", "user_id", "idempotency_key", unique=True),
    )
