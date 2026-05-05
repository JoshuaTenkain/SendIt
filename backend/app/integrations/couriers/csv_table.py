"""Adapter for couriers without a live API — uses the uploaded CSV price table.

Each ``Courier`` row in the DB has an ``adapter_code="csv_table"``; the active
``PriceTable`` + ``PriceTableRow`` rows drive rate calculation.

This adapter is stateless wrt the DB; a session is injected at call time via
``CSVTableAdapter.with_db(session)`` which produces a bound adapter that can be
registered in the ``CourierRegistry`` per-request.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.integrations.couriers.base import CourierAdapter, CourierAdapterError, QuoteResult
from app.models.courier import Courier
from app.pricing.models import PriceTable, PriceTableRow
from app.pricing.service import price_from_table

logger = structlog.get_logger()


class CSVTableAdapter(CourierAdapter):
    supports_api = False

    def __init__(self, *, db: Session, courier: Courier):
        self.db = db
        self.courier = courier
        self.courier_code = courier.code
        self.courier_name = courier.name

    def _distinct_service_levels(self, price_table_id: uuid.UUID) -> list[str]:
        stmt = (
            select(PriceTableRow.service_level).distinct().where(PriceTableRow.price_table_id == price_table_id)
        )
        return [r[0] for r in self.db.execute(stmt).all()]

    async def get_quote(self, *, pickup: dict, delivery: dict, parcel: dict) -> list[QuoteResult]:
        # Find active table
        now = datetime.now(timezone.utc)
        table_stmt = (
            select(PriceTable)
            .where(
                PriceTable.courier_id == self.courier.id,
                PriceTable.is_active.is_(True),
                PriceTable.effective_from <= now,
            )
            .order_by(PriceTable.version.desc())
            .limit(1)
        )
        price_table = self.db.scalar(table_stmt)
        if not price_table:
            return []

        service_levels = self._distinct_service_levels(price_table.id)

        results: list[QuoteResult] = []
        declared_cents = int(float(parcel.get("value_zar") or 0) * 100)
        for sl in service_levels:
            breakdown = price_from_table(
                db=self.db,
                courier_id=self.courier.id,
                service_level=sl,
                actual_weight_kg=Decimal(str(parcel["weight_kg"])),
                length_cm=Decimal(str(parcel["length_cm"])),
                width_cm=Decimal(str(parcel["width_cm"])),
                height_cm=Decimal(str(parcel["height_cm"])),
                declared_value_cents=declared_cents,
                vat_rate_pct=settings.vat_rate_pct,
            )
            if not breakdown:
                continue
            # Apply courier markup
            total = breakdown.total_cents
            if self.courier.base_markup_pct:
                total = int(round(total * (100 + self.courier.base_markup_pct) / 100))
                breakdown.meta["courier_markup_pct"] = self.courier.base_markup_pct

            results.append(
                QuoteResult(
                    courier_code=self.courier_code,
                    courier_name=self.courier_name,
                    service_level=sl,
                    service_level_display=breakdown.service_level_display,
                    price_total=total,
                    currency=breakdown.currency,
                    estimated_delivery_days=breakdown.estimated_delivery_days,
                    pricing_breakdown=breakdown.to_dict(),
                    reliability_score=float(self.courier.reliability_score),
                    raw={"price_table_id": str(price_table.id), "version": price_table.version},
                )
            )
        return results

    async def create_shipment(self, *, booking: dict) -> dict:
        # CSV-table couriers have no API — caller is expected to handle manual
        # dispatch via the partner portal. Return a stub tracking reference.
        stub_ref = f"SI-{booking.get('short_code') or booking.get('id', '')[:8].upper()}"
        return {
            "shipment_id": None,
            "tracking_reference": stub_ref,
            "raw": {"manual_dispatch": True},
        }

    async def track_shipment(self, *, tracking_reference: str) -> list[dict]:
        # CSV-table couriers have no tracking feed — nothing to pull.
        return []

    async def cancel_shipment(self, *, tracking_reference: str) -> dict:
        return {"status": "cancelled", "manual_dispatch": True}
