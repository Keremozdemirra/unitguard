"""Properties of the unit table itself."""

import unittest
from fractions import Fraction

from unitguard_dimensions import ENERGY, MASS, POWER
from unitguard_quantity import (
    CELSIUS,
    FAHRENHEIT,
    HOUR,
    JOULE,
    KELVIN,
    KILOWATT,
    KILOWATT_HOUR,
    MEGAWATT_HOUR,
    SECOND,
    TONNE,
    UNITS,
    Unit,
    UnitError,
    derived,
    unit,
)


class TestDefinitionalIdentities(unittest.TestCase):
    """Each scale factor follows from a definition, so each is checkable."""

    def test_watt_hour_is_power_times_time(self):
        # 1 kWh is a kilowatt sustained for an hour: the scale factor of the
        # energy unit must equal the product of the two scale factors.
        self.assertEqual(
            KILOWATT_HOUR.scale, KILOWATT.scale * HOUR.scale / SECOND.scale
        )

    def test_kilowatt_hour_is_exactly_3_6_megajoules(self):
        self.assertEqual(KILOWATT_HOUR.scale, Fraction(3_600_000))
        self.assertEqual(MEGAWATT_HOUR.scale, 1000 * KILOWATT_HOUR.scale)

    def test_celsius_zero_is_273_15_kelvin(self):
        self.assertEqual(CELSIUS.offset, Fraction(27315, 100))
        self.assertEqual(CELSIUS.scale, KELVIN.scale)

    def test_fahrenheit_matches_celsius_at_its_two_anchor_points(self):
        # 32 degF is 0 degC and 212 degF is 100 degC. Both must fall out of the
        # scale-and-offset pair rather than being asserted separately.
        for fahrenheit_reading, kelvin_value in ((32, Fraction(27315, 100)),
                                                 (212, Fraction(37315, 100))):
            self.assertEqual(
                fahrenheit_reading * FAHRENHEIT.scale + FAHRENHEIT.offset,
                kelvin_value,
            )

    def test_every_scale_is_an_exact_rational(self):
        for symbol, defined in UNITS.items():
            with self.subTest(symbol=symbol):
                self.assertIsInstance(defined.scale, Fraction)
                self.assertIsInstance(defined.offset, Fraction)
                self.assertGreater(defined.scale, 0)

    def test_only_the_temperature_scales_are_affine(self):
        affine = {symbol for symbol, u in UNITS.items() if u.is_affine}
        self.assertEqual(affine, {"°C", "°F"})


class TestLookup(unittest.TestCase):
    def test_symbols_are_their_own_keys(self):
        for symbol, defined in UNITS.items():
            self.assertEqual(unit(symbol), defined)

    def test_unknown_symbol_raises_rather_than_guessing(self):
        with self.assertRaises(UnitError) as caught:
            unit("KWH")
        self.assertIn("unknown unit", str(caught.exception))


class TestDerived(unittest.TestCase):
    def test_ratio_unit_carries_the_ratio_of_dimensions_and_scales(self):
        intensity = derived("t/MWh", TONNE, MEGAWATT_HOUR)
        self.assertEqual(intensity.dimension, MASS / ENERGY)
        self.assertEqual(intensity.scale, TONNE.scale / MEGAWATT_HOUR.scale)

    def test_energy_over_time_is_power(self):
        self.assertEqual(derived("J/s", JOULE, SECOND).dimension, POWER)

    def test_affine_units_are_refused(self):
        with self.assertRaises(UnitError):
            derived("°C/s", CELSIUS, SECOND)


class TestUnitConstruction(unittest.TestCase):
    def test_negative_scale_is_refused(self):
        with self.assertRaises(UnitError):
            Unit("bad", ENERGY, Fraction(-1))

    def test_float_scale_is_refused(self):
        with self.assertRaises(UnitError):
            Unit("bad", ENERGY, 3.6)

    def test_difference_unit_of_an_absolute_unit_is_itself(self):
        self.assertIs(KELVIN.difference_unit(), KELVIN)

    def test_difference_unit_drops_the_offset_and_keeps_the_size(self):
        interval = CELSIUS.difference_unit()
        self.assertEqual(interval.offset, 0)
        self.assertEqual(interval.scale, CELSIUS.scale)


if __name__ == "__main__":
    unittest.main()
