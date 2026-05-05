from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CommissionRecord(Base):
    __tablename__ = "commission_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True)

    courier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="RESTRICT"), nullable=False, index=True)

    commission_pct: Mapped[int] = mapped_column(nullable=False)
    commission_amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="ZAR")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("char_length(currency) = 3", name="ck_commission_records_currency_len"),
        CheckConstraint("commission_pct >= 0", name="ck_commission_records_commission_nonneg"),
        Index("ix_commission_records_courier_id_created_at", "courier_id", "created_at"),
    )
