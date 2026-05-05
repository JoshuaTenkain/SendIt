"""Pricing service: look up a price table row, apply surcharges, return a breakdown."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.pricing.models import PriceTable, PriceTableRow, SurchargeRule
from app.pricing.surcharges import SurchargeContext, SurchargeLine, apply_surcharges
from app.pricing.volumetric import chargeable_weight_kg


@dataclass
class PricingBreakdown:
    service_level: str
    service_level_display: str | None
    chargeable_weight_kg: Decimal
    volumetric_weight_kg: Decimal
    actual_weight_kg: Decimal
    base_price_cents: int
    surcharge_lines: list[SurchargeLine]
    subtotal_cents: int
    tax_cents: int
    total_cents: int
    currency: str
    estimated_delivery_days: int
    price_table_id: uuid.UUID | None = None
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "service_level": self.service_level,
            "service_level_display": self.service_level_display,
            "chargeable_weight_kg": float(self.chargeable_weight_kg),
            "volumetric_weight_kg": float(self.volumetric_weight_kg),
            "actual_weight_kg": float(self.actual_weight_kg),
            "base_price_cents": self.base_price_cents,
            "surcharge_lines": [asdict(line) for line in self.surcharge_lines],
            "subtotal_cents": self.subtotal_cents,
            "tax_cents": self.tax_cents,
            "total_cents": self.total_cents,
            "currency": self.currency,
            "estimated_delivery_days": self.estimated_delivery_days,
            "price_table_id": str(self.price_table_id) if self.price_table_id else None,
            "meta": self.meta,
        }


def get_active_price_table(db: Session, courier_id: uuid.UUID) -> PriceTable | None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(PriceTable)
        .where(
            PriceTable.courier_id == courier_id,
            PriceTable.is_active.is_(True),
            PriceTable.effective_from <= now,
            or_(PriceTable.effective_to.is_(None), PriceTable.effective_to > now),
        )
        .order_by(PriceTable.version.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def find_row(
    db: Session, *, price_table_id: uuid.UUID, service_level: str, weight_kg: Decimal
) -> PriceTableRow | None:
    stmt = (
        select(PriceTableRow)
        .where(
            PriceTableRow.price_table_id == price_table_id,
            PriceTableRow.service_level == service_level,
            PriceTableRow.weight_from_kg <= weight_kg,
            PriceTableRow.weight_to_kg > weight_kg,
        )
        .limit(1)
    )
    return db.scalar(stmt)


def get_surcharge_rules(db: Session, courier_id: uuid.UUID | None) -> list[SurchargeRule]:
    now = datetime.now(timezone.utc)
    stmt = select(SurchargeRule).where(
        SurchargeRule.is_active.is_(True),
        SurchargeRule.effective_from <= now,
        or_(SurchargeRule.effective_to.is_(None), SurchargeRule.effective_to > now),
        or_(
            SurchargeRule.courier_id.is_(None),
            SurchargeRule.courier_id == courier_id,
        ),
    )
    return list(db.scalars(stmt))


def price_from_table(
    *,
    db: Session,
    courier_id: uuid.UUID,
    service_level: str,
    actual_weight_kg: Decimal | float,
    length_cm: Decimal | float,
    width_cm: Decimal | float,
    height_cm: Decimal | float,
    declared_value_cents: int = 0,
    after_hours: bool = False,
    saturday: bool = False,
    outlying: bool = False,
    vat_rate_pct: int = 15,
) -> PricingBreakdown | None:
    """Produce a full pricing breakdown for a given courier + service level.

    Returns None when no active price table exists for the courier or when no
    matching weight band is found.
    """
    price_table = get_active_price_table(db, courier_id)
    if not price_table:
        return None

    actual = Decimal(str(actual_weight_kg))
    charge_kg = chargeable_weight_kg(
        actual_weight_kg=actual,
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
    )
    vol_kg = chargeable_weight_kg(
        actual_weight_kg=Decimal("0.0001"),
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
    )

    row = find_row(db, price_table_id=price_table.id, service_level=service_level, weight_kg=charge_kg)
    if not row:
        return None

    base_cents = int(row.price_cents)

    ctx = SurchargeContext(
        service_level=service_level,
        chargeable_weight_kg=charge_kg,
        declared_value_cents=declared_value_cents,
        after_hours=after_hours,
        saturday=saturday,
        outlying=outlying,
    )
    rules = get_surcharge_rules(db, courier_id)
    surcharge_lines = apply_surcharges(rules=rules, subtotal_cents=base_cents, ctx=ctx)

    subtotal = base_cents + sum(line.amount_cents for line in surcharge_lines)
    tax = int(round(subtotal * vat_rate_pct / 100))
    total = subtotal + tax

    return PricingBreakdown(
        service_level=service_level,
        service_level_display=row.service_level_display or service_level,
        chargeable_weight_kg=charge_kg,
        volumetric_weight_kg=vol_kg,
        actual_weight_kg=actual,
        base_price_cents=base_cents,
        surcharge_lines=surcharge_lines,
        subtotal_cents=subtotal,
        tax_cents=tax,
        total_cents=total,
        currency=price_table.currency,
        estimated_delivery_days=int(row.estimated_delivery_days),
        price_table_id=price_table.id,
        meta={"price_table_version": price_table.version, "price_table_name": price_table.name},
    )
