"""Pure unit tests for volumetric / chargeable weight."""

from decimal import Decimal

import pytest

from app.pricing.volumetric import chargeable_weight_kg, volumetric_weight_kg


class TestVolumetric:
    def test_prd_example_30x20x10_is_1_5kg(self):
        # 30 * 20 * 10 / 4000 = 1.5
        assert volumetric_weight_kg(30, 20, 10) == Decimal("1.50")

    def test_small_parcel(self):
        # 10 * 10 * 10 / 4000 = 0.25
        assert volumetric_weight_kg(10, 10, 10) == Decimal("0.25")

    def test_large_parcel(self):
        # 80 * 60 * 50 / 4000 = 60
        assert volumetric_weight_kg(80, 60, 50) == Decimal("60.00")

    def test_rejects_zero_dimension(self):
        with pytest.raises(ValueError):
            volumetric_weight_kg(0, 10, 10)

    def test_rejects_negative_dimension(self):
        with pytest.raises(ValueError):
            volumetric_weight_kg(-1, 10, 10)


class TestChargeable:
    def test_actual_exceeds_volumetric(self):
        # actual 5kg, volumetric 1.5kg => 5
        assert chargeable_weight_kg(
            actual_weight_kg=5, length_cm=30, width_cm=20, height_cm=10
        ) == Decimal("5.00")

    def test_volumetric_exceeds_actual(self):
        # actual 0.5kg, volumetric 15kg => 15
        assert chargeable_weight_kg(
            actual_weight_kg=0.5, length_cm=100, width_cm=60, height_cm=10
        ) == Decimal("15.00")

    def test_equal_pick_actual(self):
        assert chargeable_weight_kg(
            actual_weight_kg=Decimal("1.5"), length_cm=30, width_cm=20, height_cm=10
        ) == Decimal("1.50")

    def test_rejects_zero_actual(self):
        with pytest.raises(ValueError):
            chargeable_weight_kg(actual_weight_kg=0, length_cm=10, width_cm=10, height_cm=10)
