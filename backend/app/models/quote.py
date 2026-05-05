from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # For guest flows addresses may be inline snapshots; FKs kept nullable
    pickup_address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=True)
    delivery_address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=True)

    pickup_address_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    delivery_address_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    parcel: Mapped[dict] = mapped_column(JSONB, nullable=False)
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    urgency: Mapped[str | None] = mapped_column(String(30), nullable=True)  # same_day|overnight|economy
    budget_zar: Mapped[int | None] = mapped_column(Integer, nullable=True)  # optional hint, cents

    # Guest flow
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    guest_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="ZAR")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("char_length(currency) = 3", name="ck_quotes_currency_len"),
    )
