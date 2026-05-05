"""Volumetric weight calculation per PRD: (L x W x H cm) / 4000 -> kg."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

VOLUMETRIC_DIVISOR = Decimal("4000")  # cm^3 per kg (standard courier convention)


def _to_decimal(v: float | int | str | Decimal) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


def volumetric_weight_kg(
    length_cm: float | Decimal,
    width_cm: float | Decimal,
    height_cm: float | Decimal,
    *,
    divisor: Decimal = VOLUMETRIC_DIVISOR,
) -> Decimal:
    """Compute volumetric weight in kg, rounded up to 2 decimals."""
    l = _to_decimal(length_cm)
    w = _to_decimal(width_cm)
    h = _to_decimal(height_cm)
    if l <= 0 or w <= 0 or h <= 0:
        raise ValueError("Dimensions must be positive")
    vol = (l * w * h) / divisor
    # Keep 3 dp precision, quantise down to 2 dp for display/tier lookup
    return vol.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def chargeable_weight_kg(
    *,
    actual_weight_kg: float | Decimal,
    length_cm: float | Decimal,
    width_cm: float | Decimal,
    height_cm: float | Decimal,
    divisor: Decimal = VOLUMETRIC_DIVISOR,
) -> Decimal:
    """Chargeable weight = max(actual, volumetric)."""
    a = _to_decimal(actual_weight_kg)
    if a <= 0:
        raise ValueError("Actual weight must be positive")
    v = volumetric_weight_kg(length_cm, width_cm, height_cm, divisor=divisor)
    return max(a, v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
