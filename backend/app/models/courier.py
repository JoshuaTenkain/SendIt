from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Courier(Base):
    __tablename__ = "couriers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    base_markup_pct: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    commission_pct: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")

    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Week 1 additions: integration + ranking metadata
    supports_api: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    adapter_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "tcg", "csv_table"
    reliability_score: Mapped[Numeric] = mapped_column(Numeric(3, 2), nullable=False, server_default="0.80")
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("code <> ''", name="ck_couriers_code_not_empty"),
        CheckConstraint("name <> ''", name="ck_couriers_name_not_empty"),
        CheckConstraint("base_markup_pct >= 0", name="ck_couriers_base_markup_nonneg"),
        CheckConstraint("commission_pct >= 0", name="ck_couriers_commission_nonneg"),
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="ck_couriers_rating_range"),
        CheckConstraint(
            "reliability_score >= 0 AND reliability_score <= 1",
            name="ck_couriers_reliability_range",
        ),
    )
