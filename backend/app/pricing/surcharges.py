"""Surcharge rule evaluation.

Rules are applied additively to a base subtotal; each produces a line item.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable


@dataclass(frozen=True)
class SurchargeContext:
    """Context against which a ``SurchargeRule.applies_when`` is evaluated."""

    service_level: str
    chargeable_weight_kg: Decimal
    declared_value_cents: int = 0
    after_hours: bool = False
    saturday: bool = False
    outlying: bool = False
    return_to_sender: bool = False
    # Arbitrary extra attributes for future extension
    extras: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = {
            "service_level": self.service_level,
            "chargeable_weight_kg": float(self.chargeable_weight_kg),
            "declared_value_cents": self.declared_value_cents,
            "after_hours": self.after_hours,
            "saturday": self.saturday,
            "outlying": self.outlying,
            "return_to_sender": self.return_to_sender,
        }
        d.update(self.extras)
        return d


@dataclass(frozen=True)
class SurchargeLine:
    code: str
    name: str
    amount_cents: int
    detail: str


def _matches(applies_when: dict[str, Any] | None, ctx: SurchargeContext) -> bool:
    """Return True if all predicates in applies_when are satisfied by ctx."""
    if not applies_when:
        return True
    ctx_d = ctx.as_dict()
    for key, expected in applies_when.items():
        actual = ctx_d.get(key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif isinstance(expected, dict):
            # Only range ops supported for numeric keys: {"gte": x, "lte": y}
            try:
                actual_num = float(actual)
            except (TypeError, ValueError):
                return False
            if "gte" in expected and actual_num < float(expected["gte"]):
                return False
            if "gt" in expected and actual_num <= float(expected["gt"]):
                return False
            if "lte" in expected and actual_num > float(expected["lte"]):
                return False
            if "lt" in expected and actual_num >= float(expected["lt"]):
                return False
        else:
            if actual != expected:
                return False
    return True


def _compute_amount(rule, subtotal_cents: int, ctx: SurchargeContext) -> int:
    surcharge_type = rule.surcharge_type
    value = Decimal(str(rule.value))
    if surcharge_type == "percent":
        amount = (Decimal(subtotal_cents) * value / Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        return int(amount)
    if surcharge_type == "flat":
        return int(value)
    if surcharge_type == "percent_of_declared":
        if ctx.declared_value_cents <= 0:
            return 0
        amount = (Decimal(ctx.declared_value_cents) * value / Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        return int(amount)
    return 0


def apply_surcharges(
    *,
    rules: Iterable,
    subtotal_cents: int,
    ctx: SurchargeContext,
    now: datetime | None = None,
) -> list[SurchargeLine]:
    """Evaluate ``rules`` against ``ctx`` and return list of ``SurchargeLine``.

    ``rules`` may be ``SurchargeRule`` ORM instances or any duck-typed objects
    exposing: ``code``, ``name``, ``surcharge_type``, ``value``, ``applies_when``,
    ``is_active``, ``effective_from``, ``effective_to``.
    """
    now = now or datetime.now(timezone.utc)
    lines: list[SurchargeLine] = []

    for rule in rules:
        if not getattr(rule, "is_active", True):
            continue
        ef_from = getattr(rule, "effective_from", None)
        ef_to = getattr(rule, "effective_to", None)
        if ef_from and ef_from > now:
            continue
        if ef_to and ef_to <= now:
            continue
        if not _matches(getattr(rule, "applies_when", None), ctx):
            continue
        amount = _compute_amount(rule, subtotal_cents, ctx)
        if amount == 0:
            continue
        detail = _describe(rule, ctx)
        lines.append(
            SurchargeLine(
                code=rule.code,
                name=rule.name,
                amount_cents=amount,
                detail=detail,
            )
        )
    return lines


def _describe(rule, ctx: SurchargeContext) -> str:
    t = rule.surcharge_type
    if t == "percent":
        return f"{rule.value}% of base"
    if t == "flat":
        return f"Flat fee"
    if t == "percent_of_declared":
        return f"{rule.value}% of declared value"
    return ""
