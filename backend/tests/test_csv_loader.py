"""CSV parsing tests (pure functions, no DB)."""

from decimal import Decimal

import pytest

from app.pricing.csv_loader import CSVLoadError, parse_csv

PRD_TABLE = """Chargeable Weight (kg),Local Same-Day,Local Overnight,Regional Overnight,National Economy
0-1,9500,6500,8500,7000
1-2,11500,7500,10500,8500
2-5,14500,9500,13500,11500
5-10,19500,13500,18500,16000
10-15,24500,18500,23500,21000
15-20,29500,23500,28500,26000
20-25,34500,28500,33500,31000
"""


def _find(rows, service_level, weight_from):
    for r in rows:
        if r.service_level == service_level and r.weight_from_kg == weight_from:
            return r
    return None


def test_parse_prd_wide_table():
    rows = parse_csv(PRD_TABLE)
    # 7 bands x 4 service levels = 28 rows
    assert len(rows) == 28

    r = _find(rows, "local_same_day", Decimal("0"))
    assert r is not None
    assert r.weight_to_kg == Decimal("1")
    assert r.price_cents == 9500  # R95

    r = _find(rows, "national_economy", Decimal("20"))
    assert r.weight_to_kg == Decimal("25")
    assert r.price_cents == 31000  # R310


def test_rand_decimals_converted_to_cents():
    content = """Chargeable Weight (kg),Local Same-Day
0-1,95.00
1-2,115.50
"""
    rows = parse_csv(content)
    assert _find(rows, "local_same_day", Decimal("0")).price_cents == 9500
    assert _find(rows, "local_same_day", Decimal("1")).price_cents == 11550


def test_long_format_round_trip():
    content = """service_level,weight_from_kg,weight_to_kg,price_cents,estimated_delivery_days,service_level_display
local_overnight,0,1,6500,1,Local Overnight
local_overnight,1,2,7500,1,Local Overnight
"""
    rows = parse_csv(content)
    assert len(rows) == 2
    assert rows[0].service_level == "local_overnight"
    assert rows[0].price_cents == 6500
    assert rows[0].estimated_delivery_days == 1


def test_band_with_plus():
    content = """Chargeable Weight (kg),Local Same-Day
25+,34500
"""
    rows = parse_csv(content)
    assert len(rows) == 1
    assert rows[0].weight_from_kg == Decimal("25")
    assert rows[0].weight_to_kg >= Decimal("9999")


def test_empty_cells_skipped():
    content = """Chargeable Weight (kg),Local Same-Day,Local Overnight
0-1,9500,
1-2,,7500
"""
    rows = parse_csv(content)
    assert len(rows) == 2


def test_bad_band_raises():
    content = """Chargeable Weight (kg),Local Same-Day
notanumber,9500
"""
    with pytest.raises(CSVLoadError):
        parse_csv(content)


def test_header_only_raises():
    with pytest.raises(CSVLoadError):
        parse_csv("Chargeable Weight (kg),Local Same-Day\n")
