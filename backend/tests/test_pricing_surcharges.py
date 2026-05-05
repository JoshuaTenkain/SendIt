"""Surcharge rule evaluation tests.

Duck-typed `SurchargeRule` fakes avoid a DB dependency.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.pricing.surcharges import SurchargeContext, apply_surcharges


@dataclass
class FakeRule:
    code: str
    name: str
    surcharge_type: str
    value: Decimal
    applies_when: dict | None = None
    is_active: bool = True
    effective_from: datetime = field(default_factory=lambda: datetime(2020, 1, 1, tzinfo=timezone.utc))
    effective_to: datetime | None = None


def ctx(**kw):
    base = dict(service_level="local_same_day", chargeable_weight_kg=Decimal("2.0"))
    base.update(kw)
    return SurchargeContext(**base)


def test_fuel_levy_percent():
    rules = [FakeRule("fuel_levy", "Fuel Levy", "percent", Decimal("10"))]
    lines = apply_surcharges(rules=rules, subtotal_cents=10000, ctx=ctx())
    assert len(lines) == 1
    assert lines[0].code == "fuel_levy"
    assert lines[0].amount_cents == 1000  # 10% of 10000


def test_flat_after_hours():
    rules = [
        FakeRule("after_hours", "After hours", "flat", Decimal("15000"),
                 applies_when={"after_hours": True}),
    ]
    # Not after hours → no line
    assert apply_surcharges(rules=rules, subtotal_cents=10000, ctx=ctx(after_hours=False)) == []
    # After hours → R150 flat
    lines = apply_surcharges(rules=rules, subtotal_cents=10000, ctx=ctx(after_hours=True))
    assert lines[0].amount_cents == 15000


def test_insurance_percent_of_declared():
    rules = [
        FakeRule("insurance", "Insurance", "percent_of_declared", Decimal("1.5")),
    ]
    # declared 100000 cents (R1000) -> 1.5% = 1500 cents
    lines = apply_surcharges(
        rules=rules, subtotal_cents=5000, ctx=ctx(declared_value_cents=100_000)
    )
    assert lines[0].amount_cents == 1500


def test_insurance_zero_when_no_declared_value():
    rules = [FakeRule("insurance", "Insurance", "percent_of_declared", Decimal("1.5"))]
    lines = apply_surcharges(rules=rules, subtotal_cents=5000, ctx=ctx(declared_value_cents=0))
    assert lines == []


def test_inactive_rule_skipped():
    rules = [FakeRule("fuel_levy", "Fuel Levy", "percent", Decimal("10"), is_active=False)]
    assert apply_surcharges(rules=rules, subtotal_cents=10000, ctx=ctx()) == []


def test_expired_rule_skipped():
    past = datetime.now(timezone.utc) - timedelta(days=30)
    rules = [FakeRule("fuel_levy", "Fuel Levy", "percent", Decimal("10"), effective_to=past)]
    assert apply_surcharges(rules=rules, subtotal_cents=10000, ctx=ctx()) == []


def test_future_rule_skipped():
    future = datetime.now(timezone.utc) + timedelta(days=30)
    rules = [FakeRule("promo", "Promo", "percent", Decimal("10"), effective_from=future)]
    assert apply_surcharges(rules=rules, subtotal_cents=10000, ctx=ctx()) == []


def test_service_level_predicate_list():
    rules = [
        FakeRule(
            "sat_levy", "Saturday", "flat", Decimal("9500"),
            applies_when={"saturday": True, "service_level": ["local_same_day", "local_overnight"]},
        )
    ]
    # Matching service level + saturday
    lines = apply_surcharges(
        rules=rules,
        subtotal_cents=10000,
        ctx=ctx(service_level="local_same_day", saturday=True),
    )
    assert len(lines) == 1
    # Wrong service level
    assert (
        apply_surcharges(
            rules=rules,
            subtotal_cents=10000,
            ctx=ctx(service_level="national_economy", saturday=True),
        )
        == []
    )


def test_multiple_rules_compose():
    rules = [
        FakeRule("fuel", "Fuel", "percent", Decimal("10")),
        FakeRule("outlying", "Outlying", "flat", Decimal("4500"), applies_when={"outlying": True}),
    ]
    lines = apply_surcharges(
        rules=rules, subtotal_cents=10000, ctx=ctx(outlying=True)
    )
    codes = {line.code for line in lines}
    assert codes == {"fuel", "outlying"}
    total = sum(line.amount_cents for line in lines)
    assert total == 1000 + 4500


def test_weight_range_predicate_gte():
    rules = [
        FakeRule(
            "heavy", "Heavy", "flat", Decimal("10000"),
            applies_when={"chargeable_weight_kg": {"gte": 20}},
        )
    ]
    # 2kg -> no
    assert apply_surcharges(rules=rules, subtotal_cents=10000, ctx=ctx()) == []
    # 25kg -> yes
    lines = apply_surcharges(
        rules=rules, subtotal_cents=10000, ctx=ctx(chargeable_weight_kg=Decimal("25"))
    )
    assert lines[0].amount_cents == 10000
