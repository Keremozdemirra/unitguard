"""Test suite for unitguard.dimensions. Standard library only."""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unitguard_dimensions.dimensions import (  # noqa: E402
    BASE_NAMES,
    BASE_SYMBOLS,
    DIMENSIONLESS,
    EMISSION_INTENSITY,
    ENERGY,
    ENERGY_INTENSITY,
    FORCE,
    LENGTH,
    MASS,
    NAMED,
    POWER,
    TIME,
    Dimension,
    DimensionError,
    name_of,
    product,
)


class GroupAxiomTests(unittest.TestCase):
    """Dimensions under multiplication form an abelian group. Assert the axioms."""

    SAMPLE = (MASS, LENGTH, TIME, ENERGY, POWER, EMISSION_INTENSITY, DIMENSIONLESS)

    def test_identity(self):
        for d in self.SAMPLE:
            self.assertEqual(d * DIMENSIONLESS, d)
            self.assertEqual(DIMENSIONLESS * d, d)

    def test_inverse(self):
        for d in self.SAMPLE:
            self.assertEqual(d * d.inverse(), DIMENSIONLESS)
            self.assertTrue((d / d).is_dimensionless)

    def test_associativity(self):
        for a in self.SAMPLE:
            for b in self.SAMPLE:
                for c in self.SAMPLE:
                    self.assertEqual((a * b) * c, a * (b * c))

    def test_commutativity(self):
        for a in self.SAMPLE:
            for b in self.SAMPLE:
                self.assertEqual(a * b, b * a)

    def test_division_undoes_multiplication(self):
        for a in self.SAMPLE:
            for b in self.SAMPLE:
                self.assertEqual((a * b) / b, a)


class PowerTests(unittest.TestCase):
    def test_zeroth_power_is_dimensionless(self):
        for d in (MASS, ENERGY, EMISSION_INTENSITY):
            self.assertTrue((d ** 0).is_dimensionless)

    def test_first_power_is_identity(self):
        self.assertEqual(ENERGY ** 1, ENERGY)

    def test_negative_power_is_the_inverse(self):
        self.assertEqual(ENERGY ** -1, ENERGY.inverse())

    def test_powers_add_under_multiplication(self):
        self.assertEqual((LENGTH ** 2) * (LENGTH ** 3), LENGTH ** 5)

    def test_root_is_exact_and_inverts_the_power(self):
        # A float representation would make this comparison unreliable, which
        # is the reason exponents are Fractions.
        self.assertEqual((ENERGY ** 2).root(2), ENERGY)
        self.assertEqual(ENERGY.root(2) ** 2, ENERGY)

    def test_half_power_is_representable(self):
        half = ENERGY ** Fraction(1, 2)
        self.assertEqual(half.as_dict()["M"], Fraction(1, 2))
        self.assertEqual(half * half, ENERGY)

    def test_cube_root_of_volume_is_length(self):
        self.assertEqual((LENGTH ** 3).root(3), LENGTH)

    def test_non_positive_root_rejected(self):
        with self.assertRaises(DimensionError):
            ENERGY.root(0)
        with self.assertRaises(DimensionError):
            ENERGY.root(-2)


class DerivedDimensionTests(unittest.TestCase):
    def test_energy_is_force_times_length(self):
        self.assertEqual(ENERGY, FORCE * LENGTH)

    def test_energy_has_the_textbook_exponents(self):
        self.assertEqual(ENERGY.as_dict(), {"M": 1, "L": 2, "T": -2})

    def test_power_is_energy_per_time(self):
        self.assertEqual(POWER, ENERGY / TIME)
        self.assertEqual(POWER * TIME, ENERGY)

    def test_emission_factor_times_energy_gives_mass(self):
        # The identity every Scope 2 calculation rests on.
        self.assertEqual(ENERGY * EMISSION_INTENSITY, MASS)

    def test_the_two_intensities_are_not_the_same_dimension(self):
        # tCO2e per MWh and MWh per tonne are routinely confused; they are not
        # even the same kind of quantity.
        self.assertNotEqual(EMISSION_INTENSITY, ENERGY_INTENSITY)

    def test_inverting_an_emission_factor_changes_the_result_dimension(self):
        self.assertNotEqual(ENERGY * EMISSION_INTENSITY.inverse(), MASS)


class AdditionRuleTests(unittest.TestCase):
    def test_same_dimension_may_be_added(self):
        ENERGY.check_addable(FORCE * LENGTH)  # must not raise

    def test_different_dimensions_may_not(self):
        with self.assertRaises(DimensionError):
            ENERGY.check_addable(MASS)

    def test_the_error_names_both_dimensions_and_the_context(self):
        with self.assertRaises(DimensionError) as ctx:
            ENERGY.check_addable(MASS, context="scope 1 + scope 2")
        message = str(ctx.exception)
        self.assertIn(str(ENERGY), message)
        self.assertIn(str(MASS), message)
        self.assertIn("scope 1 + scope 2", message)

    def test_dimensionless_is_not_addable_to_a_dimensioned_quantity(self):
        with self.assertRaises(DimensionError):
            DIMENSIONLESS.check_addable(MASS)


class ConstructionTests(unittest.TestCase):
    def test_of_accepts_ints_and_exact_halves(self):
        self.assertEqual(Dimension.of(M=1, L=2, T=-2), ENERGY)
        self.assertEqual(Dimension.of(L=0.5).as_dict()["L"], Fraction(1, 2))

    def test_of_rejects_an_inexact_float(self):
        with self.assertRaises(DimensionError):
            Dimension.of(L=0.1234567)

    def test_of_rejects_an_unknown_base_dimension(self):
        with self.assertRaises(DimensionError) as ctx:
            Dimension.of(X=1)
        self.assertIn("X", str(ctx.exception))

    def test_of_rejects_a_non_numeric_exponent(self):
        with self.assertRaises(DimensionError):
            Dimension.of(M="two")

    def test_wrong_length_vector_rejected(self):
        with self.assertRaises(DimensionError):
            Dimension((Fraction(1), Fraction(0)))

    def test_raw_ints_in_the_vector_are_rejected(self):
        with self.assertRaises(DimensionError):
            Dimension((1, 0, 0, 0, 0, 0, 0))

    def test_from_mapping_round_trips(self):
        self.assertEqual(Dimension.from_mapping(ENERGY.as_dict()), ENERGY)

    def test_there_are_seven_base_dimensions_with_matching_names(self):
        self.assertEqual(len(BASE_SYMBOLS), 7)
        self.assertEqual(len(BASE_NAMES), len(BASE_SYMBOLS))


class HashingAndDisplayTests(unittest.TestCase):
    def test_dimensions_are_hashable_and_usable_as_keys(self):
        registry = {ENERGY: "joule", MASS: "kilogram"}
        self.assertEqual(registry[FORCE * LENGTH], "joule")

    def test_equal_dimensions_hash_equal(self):
        self.assertEqual(hash(ENERGY), hash(FORCE * LENGTH))

    def test_dimensionless_prints_as_one(self):
        self.assertEqual(str(DIMENSIONLESS), "1")

    def test_str_shows_exponents(self):
        self.assertEqual(str(ENERGY), "M·L^2·T^-2")

    def test_fractional_exponents_are_parenthesised(self):
        self.assertIn("^(1/2)", str(ENERGY ** Fraction(1, 2)))

    def test_name_of_finds_known_dimensions_and_falls_back(self):
        self.assertEqual(name_of(ENERGY), "energy")
        self.assertEqual(name_of(Dimension.of(J=3)), "J^3")

    def test_every_named_dimension_round_trips_through_name_of(self):
        for name, dimension in NAMED.items():
            self.assertEqual(NAMED[name_of(dimension)], dimension)


class ProductTests(unittest.TestCase):
    def test_empty_product_is_dimensionless(self):
        self.assertTrue(product([]).is_dimensionless)

    def test_product_matches_repeated_multiplication(self):
        self.assertEqual(product([MASS, LENGTH, TIME]), MASS * LENGTH * TIME)

    def test_product_of_a_dimension_and_its_inverse_cancels(self):
        self.assertTrue(product([ENERGY, ENERGY.inverse()]).is_dimensionless)


if __name__ == "__main__":
    unittest.main(verbosity=2)
