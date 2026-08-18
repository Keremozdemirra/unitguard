"""Algebraic properties of Quantity.

Each test below asserts something that must hold for any correct
implementation -- a conversion identity, a group law, an invariance under
change of unit -- rather than that a call returned without raising.
"""

import unittest
from fractions import Fraction

from unitguard_dimensions import DimensionError, ENERGY, MASS
from unitguard_quantity import (
    CELSIUS,
    FAHRENHEIT,
    GIGAJOULE,
    GRAM,
    HOUR,
    JOULE,
    KELVIN,
    KILOGRAM,
    KILOWATT,
    KILOWATT_HOUR,
    MEGAJOULE,
    MEGAWATT_HOUR,
    ONE,
    PERCENT,
    Quantity,
    SECOND,
    TONNE,
    UnitError,
    derived,
    quantity,
    ratio,
    total,
)

Q = quantity


class TestExactMagnitudes(unittest.TestCase):
    def test_a_float_is_read_as_the_decimal_it_looks_like(self):
        self.assertEqual(Q(0.1, JOULE).value, Fraction(1, 10))

    def test_the_classic_float_failure_does_not_happen(self):
        self.assertEqual(Q(0.1, JOULE) + Q(0.2, JOULE), Q(0.3, JOULE))

    def test_booleans_are_not_magnitudes(self):
        with self.assertRaises(UnitError):
            Q(True, JOULE)

    def test_a_non_numeric_string_is_rejected(self):
        with self.assertRaises(UnitError):
            Q("a lot", JOULE)


class TestConversion(unittest.TestCase):
    def test_kilowatt_hour_to_megajoule_is_exact(self):
        self.assertEqual(Q(1, KILOWATT_HOUR).to(MEGAJOULE).value, Fraction(36, 10))

    def test_conversion_round_trips_exactly(self):
        # Exactness is the reason magnitudes are rationals; if this fails for
        # any pair the whole design has failed.
        original = Q(Fraction(7, 3), KILOWATT_HOUR)
        for target in (JOULE, MEGAJOULE, GIGAJOULE, MEGAWATT_HOUR):
            with self.subTest(target=target.symbol):
                self.assertEqual(original.to(target).to(KILOWATT_HOUR), original)
                self.assertEqual(
                    original.to(target).to(KILOWATT_HOUR).value, Fraction(7, 3)
                )

    def test_conversion_preserves_the_si_value(self):
        original = Q(Fraction(5, 7), TONNE)
        for target in (KILOGRAM, GRAM):
            self.assertEqual(original.to(target).si_value, original.si_value)

    def test_conversion_across_dimensions_is_refused(self):
        with self.assertRaises(DimensionError):
            Q(1, KILOWATT_HOUR).to(TONNE)

    def test_percent_is_a_hundredth(self):
        self.assertEqual(Q(50, PERCENT).to(ONE).value, Fraction(1, 2))


class TestAdditiveGroupLaws(unittest.TestCase):
    """Quantities of one dimension form an abelian group under addition."""

    def setUp(self):
        self.a = Q(Fraction(3, 7), KILOWATT_HOUR)
        self.b = Q(Fraction(11, 5), MEGAJOULE)
        self.c = Q(2, GIGAJOULE)
        self.zero = Q(0, JOULE)

    def test_commutative_in_value_even_across_units(self):
        self.assertEqual(self.a + self.b, self.b + self.a)

    def test_associative(self):
        self.assertEqual((self.a + self.b) + self.c, self.a + (self.b + self.c))

    def test_zero_is_an_identity(self):
        self.assertEqual(self.a + self.zero, self.a)

    def test_every_element_has_an_inverse(self):
        self.assertEqual(self.a + (-self.a), self.zero)

    def test_addition_is_reported_in_the_left_hand_unit(self):
        # Commutativity above is about the *quantity*; the unit chosen for the
        # answer follows the left operand, which is what the reader asked in.
        self.assertEqual((self.a + self.b).unit, KILOWATT_HOUR)
        self.assertEqual((self.b + self.a).unit, MEGAJOULE)

    def test_addition_is_invariant_under_the_unit_it_is_done_in(self):
        in_kwh = (self.a + self.b).si_value
        in_joule = (self.a.to(JOULE) + self.b.to(JOULE)).si_value
        self.assertEqual(in_kwh, in_joule)

    def test_adding_across_dimensions_raises(self):
        with self.assertRaises(DimensionError) as caught:
            Q(1, KILOWATT_HOUR) + Q(1, TONNE)
        self.assertIn("measure different things", str(caught.exception))

    def test_subtraction_is_addition_of_the_inverse(self):
        self.assertEqual(self.a - self.b, self.a + (-self.b))


class TestMultiplicativeArithmetic(unittest.TestCase):
    def test_the_scope_two_identity(self):
        # energy x emission factor = mass, exactly.
        intensity = derived("t/MWh", TONNE, MEGAWATT_HOUR)
        emissions = Q(250, MEGAWATT_HOUR) * Q(Fraction(4, 10), intensity)
        self.assertEqual(emissions.dimension, MASS)
        self.assertEqual(emissions.to(TONNE).value, Fraction(100))

    def test_multiplication_is_commutative_and_associative_in_si_value(self):
        a, b, c = Q(3, MEGAWATT_HOUR), Q(5, HOUR), Q(Fraction(2, 3), TONNE)
        self.assertEqual((a * b).si_value, (b * a).si_value)
        self.assertEqual(((a * b) * c).si_value, (a * (b * c)).si_value)

    def test_power_times_time_is_energy(self):
        energy = Q(2, KILOWATT) * Q(3, HOUR)
        self.assertEqual(energy.dimension, ENERGY)
        self.assertEqual(energy.to(KILOWATT_HOUR).value, Fraction(6))

    def test_dividing_by_the_same_dimension_is_dimensionless(self):
        result = Q(1, KILOWATT_HOUR) / Q(1, MEGAJOULE)
        self.assertTrue(result.dimension.is_dimensionless)
        self.assertEqual(result.si_value, Fraction(36, 10))

    def test_scaling_distributes_over_addition(self):
        a, b = Q(Fraction(1, 3), KILOWATT_HOUR), Q(7, MEGAJOULE)
        self.assertEqual((a + b) * 3, a * 3 + b * 3)

    def test_integer_powers_multiply_dimensions(self):
        area_ish = Q(3, MEGAWATT_HOUR) ** 2
        self.assertEqual(area_ish.dimension, ENERGY**2)
        self.assertEqual(area_ish.si_value, Q(3, MEGAWATT_HOUR).si_value ** 2)

    def test_zeroth_power_is_dimensionless_one(self):
        self.assertEqual((Q(7, TONNE) ** 0).si_value, Fraction(1))
        self.assertTrue((Q(7, TONNE) ** 0).dimension.is_dimensionless)

    def test_roots_are_refused_rather_than_approximated(self):
        with self.assertRaises(UnitError) as caught:
            Q(4, JOULE) ** Fraction(1, 2)
        self.assertIn("Roots are out of scope", str(caught.exception))

    def test_division_by_a_zero_quantity_raises(self):
        with self.assertRaises(ZeroDivisionError):
            Q(1, JOULE) / Q(0, JOULE)


class TestAffineScales(unittest.TestCase):
    def test_celsius_to_kelvin_at_the_defining_point(self):
        self.assertEqual(Q(0, CELSIUS).to(KELVIN).value, Fraction(27315, 100))
        self.assertEqual(Q(Fraction(-27315, 100), CELSIUS).to(KELVIN).value, 0)

    def test_fahrenheit_to_celsius_round_numbers(self):
        for fahrenheit, celsius in ((32, 0), (212, 100), (-40, -40)):
            with self.subTest(fahrenheit=fahrenheit):
                self.assertEqual(Q(fahrenheit, FAHRENHEIT).to(CELSIUS).value, celsius)

    def test_affine_conversion_round_trips_exactly(self):
        original = Q(Fraction(37, 3), CELSIUS)
        self.assertEqual(original.to(FAHRENHEIT).to(CELSIUS), original)

    def test_two_readings_cannot_be_added(self):
        with self.assertRaises(UnitError) as caught:
            Q(20, CELSIUS) + Q(20, CELSIUS)
        self.assertIn("affine", str(caught.exception))

    def test_difference_of_two_readings_is_an_interval(self):
        difference = Q(30, CELSIUS) - Q(10, CELSIUS)
        self.assertFalse(difference.unit.is_affine)
        self.assertEqual(difference.to(KELVIN).value, Fraction(20))

    def test_a_fahrenheit_interval_is_five_ninths_of_a_kelvin(self):
        # 68 degF - 32 degF is 36 Fahrenheit degrees, which is 20 kelvin.
        difference = Q(68, FAHRENHEIT) - Q(32, FAHRENHEIT)
        self.assertEqual(difference.value, Fraction(36))
        self.assertEqual(difference.to(KELVIN).value, Fraction(20))

    def test_an_interval_may_be_added_to_a_reading(self):
        self.assertEqual(Q(20, CELSIUS) + Q(5, KELVIN), Q(25, CELSIUS))

    def test_an_interval_plus_a_reading_is_the_same_reading(self):
        self.assertEqual(Q(5, KELVIN) + Q(20, CELSIUS), Q(25, CELSIUS))

    def test_a_reading_cannot_be_subtracted_from_an_interval(self):
        with self.assertRaises(UnitError):
            Q(300, KELVIN) - Q(20, CELSIUS)

    def test_a_reading_cannot_be_scaled(self):
        with self.assertRaises(UnitError) as caught:
            Q(20, CELSIUS) * 2
        self.assertIn("affine", str(caught.exception))

    def test_a_reading_cannot_be_negated(self):
        with self.assertRaises(UnitError):
            -Q(20, CELSIUS)

    def test_the_same_temperature_in_three_scales_is_one_quantity(self):
        self.assertEqual(Q(0, CELSIUS), Q(Fraction(27315, 100), KELVIN))
        self.assertEqual(Q(0, CELSIUS), Q(32, FAHRENHEIT))


class TestComparison(unittest.TestCase):
    def test_equality_is_physical_not_textual(self):
        self.assertEqual(Q(1, KILOWATT_HOUR), Q(Fraction(36, 10), MEGAJOULE))
        self.assertNotEqual(Q(1, KILOWATT_HOUR), Q(1, MEGAJOULE))

    def test_equal_quantities_hash_equal(self):
        self.assertEqual(
            hash(Q(1, KILOWATT_HOUR)), hash(Q(Fraction(36, 10), MEGAJOULE))
        )
        self.assertEqual(len({Q(1, KILOWATT_HOUR), Q(3_600_000, JOULE)}), 1)

    def test_different_dimensions_are_unequal_rather_than_an_error(self):
        self.assertNotEqual(Q(1, JOULE), Q(1, KILOGRAM))

    def test_ordering_is_consistent_across_units(self):
        self.assertLess(Q(1, MEGAJOULE), Q(1, KILOWATT_HOUR))
        self.assertGreater(Q(1, KILOWATT_HOUR), Q(1, MEGAJOULE))
        self.assertLessEqual(Q(1, KILOWATT_HOUR), Q(Fraction(36, 10), MEGAJOULE))

    def test_sorting_a_mixed_unit_list_orders_by_the_physical_quantity(self):
        values = [Q(1, GIGAJOULE), Q(1, JOULE), Q(1, KILOWATT_HOUR), Q(1, MEGAJOULE)]
        self.assertEqual(
            [q.unit.symbol for q in sorted(values)], ["J", "MJ", "kWh", "GJ"]
        )

    def test_ordering_across_dimensions_raises(self):
        with self.assertRaises(DimensionError):
            Q(1, JOULE) < Q(1, KILOGRAM)


class TestTotalAndRatio(unittest.TestCase):
    def test_total_converts_and_sums(self):
        summed = total([Q(1, KILOWATT_HOUR), Q(Fraction(36, 10), MEGAJOULE)])
        self.assertEqual(summed, Q(2, KILOWATT_HOUR))
        self.assertEqual(summed.unit, KILOWATT_HOUR)

    def test_total_honours_an_explicit_unit(self):
        summed = total([Q(1, KILOWATT_HOUR)], unit=MEGAJOULE)
        self.assertEqual(summed.unit, MEGAJOULE)
        self.assertEqual(summed.value, Fraction(36, 10))

    def test_total_of_nothing_needs_a_unit(self):
        with self.assertRaises(UnitError):
            total([])
        self.assertEqual(total([], unit=TONNE).value, 0)

    def test_total_refuses_an_affine_target(self):
        with self.assertRaises(UnitError):
            total([Q(10, CELSIUS)])

    def test_total_refuses_a_mixed_dimension_sequence(self):
        with self.assertRaises(DimensionError):
            total([Q(1, KILOWATT_HOUR), Q(1, TONNE)])

    def test_ratio_is_a_plain_exact_fraction(self):
        self.assertEqual(ratio(Q(1, KILOWATT_HOUR), Q(1, MEGAJOULE)), Fraction(36, 10))
        self.assertIsInstance(ratio(Q(1, TONNE), Q(4, TONNE)), Fraction)

    def test_ratio_of_a_thing_to_itself_is_one(self):
        self.assertEqual(ratio(Q(7, TONNE), Q(7000, KILOGRAM)), Fraction(1))

    def test_ratio_across_dimensions_raises(self):
        with self.assertRaises(DimensionError):
            ratio(Q(1, TONNE), Q(1, JOULE))


class TestDisplay(unittest.TestCase):
    def test_terminating_rationals_print_exactly(self):
        self.assertEqual(str(Q(Fraction(36, 10), MEGAJOULE)), "3.6 MJ")
        self.assertEqual(str(Q(2, TONNE)), "2 t")

    def test_repeating_rationals_are_marked_as_approximate(self):
        self.assertTrue(str(Q(Fraction(1, 3), TONNE)).startswith("~0.3333"))

    def test_dimensionless_quantities_print_without_a_unit(self):
        self.assertEqual(str(Q(Fraction(1, 2), ONE)), "0.5")

    def test_format_keeps_the_unit_attached(self):
        # A numeric format code would silently drop the unit, which is the one
        # thing this type exists to keep with the number.
        self.assertEqual(f"{Q(2, TONNE):>8}", "     2 t")

    def test_composed_symbols_are_bracketed(self):
        symbol = (Q(1, TONNE) / Q(1, MEGAWATT_HOUR) / Q(1, SECOND)).unit.symbol
        self.assertEqual(symbol, "(t/MWh)/s")


if __name__ == "__main__":
    unittest.main()
