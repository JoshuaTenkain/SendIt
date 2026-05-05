from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True)

    provider: Mapped[str] = mapped_column(String(40), nullable=False, server_default="payfast")

    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="ZAR")

    provider_reference: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("char_length(currency) = 3", name="ck_transactions_currency_len"),
        CheckConstraint("provider <> ''", name="ck_transactions_provider_not_empty"),
        CheckConstraint("status <> ''", name="ck_transactions_status_not_empty"),
        Index("ix_transactions_status_created_at", "status", "created_at"),
    )
