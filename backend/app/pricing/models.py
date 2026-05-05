"""Pricing engine SQLA models.

- PriceTable: a versioned upload for a courier without live API
- PriceTableRow: per (service_level, weight band) rate in cents
- SurchargeRule: named rule (fuel levy, outlying, insurance, etc.) with JSONB predicate
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceTable(Base):
    __tablename__ = "price_tables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    courier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="ZAR")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)

    effective_from: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    effective_to: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("char_length(currency) = 3", name="ck_price_tables_currency_len"),
        CheckConstraint("version >= 1", name="ck_price_tables_version_pos"),
    )


class PriceTableRow(Base):
    __tablename__ = "price_table_rows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    price_table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("price_tables.id", ondelete="CASCADE"), nullable=False, index=True
    )

    service_level: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    service_level_display: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # inclusive lower bound, exclusive upper bound (kg)
    weight_from_kg: Mapped[Numeric] = mapped_column(Numeric(7, 2), nullable=False)
    weight_to_kg: Mapped[Numeric] = mapped_column(Numeric(7, 2), nullable=False)

    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    estimated_delivery_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="2")

    __table_args__ = (
        CheckConstraint("weight_from_kg >= 0", name="ck_price_rows_from_nonneg"),
        CheckConstraint("weight_to_kg > weight_from_kg", name="ck_price_rows_to_gt_from"),
        CheckConstraint("price_cents >= 0", name="ck_price_rows_price_nonneg"),
        CheckConstraint("estimated_delivery_days >= 0", name="ck_price_rows_days_nonneg"),
        UniqueConstraint(
            "price_table_id", "service_level", "weight_from_kg",
            name="uq_price_rows_table_service_from",
        ),
    )


class SurchargeRule(Base):
    """A surcharge rule.

    ``type`` one of:
      * ``percent``              - ``value`` is a percentage of chargeable subtotal
      * ``flat``                 - ``value`` is a flat amount in cents
      * ``percent_of_declared``  - ``value`` is a percentage of declared_value_cents

    ``applies_when`` is a simple JSONB predicate against ``SurchargeContext``:
        {"after_hours": true}
        {"service_level": ["local_same_day"]}
    Empty/null means always applies.
    """

    __tablename__ = "surcharge_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # NULL means global (applies to all couriers)
    courier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("couriers.id", ondelete="CASCADE"), nullable=True, index=True
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    surcharge_type: Mapped[str] = mapped_column(String(30), nullable=False)  # percent|flat|percent_of_declared
    value: Mapped[Numeric] = mapped_column(Numeric(10, 4), nullable=False)

    applies_when: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    effective_from: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    effective_to: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "surcharge_type IN ('percent','flat','percent_of_declared')",
            name="ck_surcharge_type_valid",
        ),
    )
