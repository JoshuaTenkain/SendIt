"""CSV price-table loader.

Two accepted CSV shapes:

1. Wide (as in PRD) - first column is "Chargeable Weight (kg)" or
   "weight_kg" giving either a single number (e.g. "2") or a band
   ("0-1", "1-2", "20-25", "25+"); each subsequent column header is a
   service level (e.g. "Local Same-Day", "Local Overnight").

   Chargeable Weight (kg),Local Same-Day,Local Overnight,Regional Overnight,National Economy
   0-1,9500,6500,8500,7000
   1-2,11500,7500,10500,8500

2. Long - columns: service_level, weight_from_kg, weight_to_kg, price_cents,
   [estimated_delivery_days], [service_level_display]

Prices may be specified in cents (integer) or Rand (decimal) — the loader
auto-detects by looking for a '.' in the value; Rand values are converted
to cents.
"""

from __future__ import annotations

import csv
import io
import re
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import IO, Iterable

from sqlalchemy.orm import Session

from app.pricing.models import PriceTable, PriceTableRow

# Mapping from human header -> canonical service_level code
_DEFAULT_HEADER_MAP = {
    "local same-day": "local_same_day",
    "local same day": "local_same_day",
    "local overnight": "local_overnight",
    "regional overnight": "regional_overnight",
    "national economy": "national_economy",
    "national overnight": "national_overnight",
    "economy": "economy",
    "express": "express",
    "overnight": "overnight",
    "same day": "same_day",
    "same-day": "same_day",
}

_DEFAULT_DAYS = {
    "local_same_day": 0,
    "same_day": 0,
    "local_overnight": 1,
    "regional_overnight": 1,
    "national_overnight": 1,
    "overnight": 1,
    "express": 1,
    "national_economy": 3,
    "economy": 3,
}

_BAND_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*$")
_PLUS_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*\+\s*$")
_SINGLE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:kg)?\s*$", re.IGNORECASE)


class CSVLoadError(ValueError):
    pass


@dataclass
class CSVRow:
    service_level: str
    service_level_display: str
    weight_from_kg: Decimal
    weight_to_kg: Decimal
    price_cents: int
    estimated_delivery_days: int


def _to_cents(raw: str) -> int:
    raw = (raw or "").strip().replace(",", "").replace("R", "")
    if raw == "":
        raise CSVLoadError("Empty price value")
    if "." in raw:
        return int(Decimal(raw) * 100)
    return int(raw)


def _parse_band(label: str, fallback_upper: Decimal = Decimal("9999")) -> tuple[Decimal, Decimal]:
    label = label.strip().lower()
    m = _BAND_RE.match(label)
    if m:
        return Decimal(m.group(1)), Decimal(m.group(2))
    m = _PLUS_RE.match(label)
    if m:
        return Decimal(m.group(1)), fallback_upper
    m = _SINGLE_RE.match(label)
    if m:
        v = Decimal(m.group(1))
        # treat a single number as the upper bound of a [v-1, v] band when v>=1
        lower = v - Decimal("1") if v >= 1 else Decimal("0")
        return lower, v
    raise CSVLoadError(f"Unrecognised weight band: {label!r}")


def _canonical_service_level(header: str) -> tuple[str, str]:
    cleaned = header.strip()
    key = cleaned.lower()
    code = _DEFAULT_HEADER_MAP.get(key)
    if code:
        return code, cleaned
    # Fallback: snake_case the header
    code = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return code or "unknown", cleaned


def parse_csv(content: str | IO[str]) -> list[CSVRow]:
    """Parse a CSV string/stream into CSVRow list. Auto-detects wide vs long."""
    if isinstance(content, str):
        buf = io.StringIO(content)
    else:
        buf = content

    reader = csv.reader(buf)
    rows = [r for r in reader if any(cell.strip() for cell in r)]
    if len(rows) < 2:
        raise CSVLoadError("CSV must contain a header and at least one data row")

    header = [h.strip() for h in rows[0]]
    header_lower = [h.lower() for h in header]

    # Detect long format by header names
    if {"service_level", "weight_from_kg", "weight_to_kg", "price_cents"} <= set(header_lower):
        return list(_parse_long(header_lower, rows[1:]))

    # Otherwise treat as wide
    return list(_parse_wide(header, rows[1:]))


def _parse_long(header: list[str], data_rows: list[list[str]]) -> Iterable[CSVRow]:
    idx = {name: header.index(name) for name in header}
    for i, row in enumerate(data_rows, start=2):
        try:
            service_level = row[idx["service_level"]].strip()
            display = row[idx["service_level_display"]].strip() if "service_level_display" in idx else service_level
            wf = Decimal(row[idx["weight_from_kg"]].strip())
            wt = Decimal(row[idx["weight_to_kg"]].strip())
            price = int(row[idx["price_cents"]].strip())
            days = int(row[idx["estimated_delivery_days"]].strip()) if "estimated_delivery_days" in idx else _DEFAULT_DAYS.get(service_level, 2)
        except (ValueError, IndexError, KeyError) as e:
            raise CSVLoadError(f"Row {i}: {e}") from e
        if wt <= wf:
            raise CSVLoadError(f"Row {i}: weight_to_kg must exceed weight_from_kg")
        yield CSVRow(service_level, display, wf, wt, price, days)


def _parse_wide(header: list[str], data_rows: list[list[str]]) -> Iterable[CSVRow]:
    # First column is the weight band; subsequent columns are service levels
    service_cols = [(i, *_canonical_service_level(h)) for i, h in enumerate(header) if i > 0 and h.strip()]
    if not service_cols:
        raise CSVLoadError("No service-level columns found in header")

    for i, row in enumerate(data_rows, start=2):
        if not row or not row[0].strip():
            continue
        try:
            wf, wt = _parse_band(row[0])
        except CSVLoadError as e:
            raise CSVLoadError(f"Row {i}: {e}") from e
        for col_idx, code, display in service_cols:
            if col_idx >= len(row):
                continue
            cell = row[col_idx].strip()
            if cell == "" or cell == "-":
                continue
            try:
                price_cents = _to_cents(cell)
            except CSVLoadError as e:
                raise CSVLoadError(f"Row {i}, column {display}: {e}") from e
            yield CSVRow(
                service_level=code,
                service_level_display=display,
                weight_from_kg=wf,
                weight_to_kg=wt,
                price_cents=price_cents,
                estimated_delivery_days=_DEFAULT_DAYS.get(code, 2),
            )


def load_price_table(
    *,
    db: Session,
    courier_id: uuid.UUID,
    name: str,
    content: str | IO[str],
    uploaded_by_user_id: uuid.UUID | None = None,
    currency: str = "ZAR",
    deactivate_previous: bool = True,
) -> PriceTable:
    """Parse CSV and create a new versioned PriceTable.

    If ``deactivate_previous`` is True, any existing active tables for the same
    courier will have ``is_active`` set to False within the same transaction so
    only the new one is used by the pricing engine.
    """
    parsed = list(parse_csv(content))
    if not parsed:
        raise CSVLoadError("No rows found in CSV")

    # Version = current max + 1
    prev_max = (
        db.query(PriceTable.version)
        .filter(PriceTable.courier_id == courier_id)
        .order_by(PriceTable.version.desc())
        .limit(1)
        .scalar()
    ) or 0

    if deactivate_previous:
        db.query(PriceTable).filter(
            PriceTable.courier_id == courier_id, PriceTable.is_active.is_(True)
        ).update({"is_active": False}, synchronize_session=False)

    price_table = PriceTable(
        courier_id=courier_id,
        name=name,
        currency=currency,
        version=prev_max + 1,
        is_active=True,
        uploaded_by_user_id=uploaded_by_user_id,
    )
    db.add(price_table)
    db.flush()

    for r in parsed:
        db.add(
            PriceTableRow(
                price_table_id=price_table.id,
                service_level=r.service_level,
                service_level_display=r.service_level_display,
                weight_from_kg=r.weight_from_kg,
                weight_to_kg=r.weight_to_kg,
                price_cents=r.price_cents,
                estimated_delivery_days=r.estimated_delivery_days,
            )
        )

    db.commit()
    db.refresh(price_table)
    return price_table
